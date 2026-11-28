from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from .forms import ChoiceForm, CustomLoginForm, ExamForm, QuestionForm, UserRegisterForm
from .models import Choice, Exam, ExamAttempt, Question, StudentAnswer


class CustomLoginView(LoginView):
    template_name = "exams/login.html"
    authentication_form = CustomLoginForm


class CustomLogoutView(LogoutView):
    next_page = "login"


def register(request):
    """Public registration always creates a student; staff promotion is admin-only."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = UserRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "exams/register.html", {"form": form})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "exams/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            context["exams"] = Exam.objects.filter(created_by=self.request.user).order_by("-created_at")
        else:
            context["exams"] = Exam.objects.all().order_by("-created_at")
        return context


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restricts access to staff users; ownership is checked per object as well."""
    def test_func(self):
        return self.request.user.is_staff


class ExamCreateView(TeacherRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("exam_detail", kwargs={"pk": self.object.pk})


class QuestionCreateView(TeacherRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "exams/question_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.exam = get_object_or_404(Exam, pk=kwargs["pk"], created_by=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.exam = self.exam
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("exam_detail", kwargs={"pk": self.exam.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = self.exam
        return context


class ExamDetailView(LoginRequiredMixin, TemplateView):
    template_name = "exams/exam_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.exam = get_object_or_404(Exam, pk=kwargs["pk"])
        if not request.user.is_staff or self.exam.created_by_id != request.user.pk:
            return HttpResponseForbidden("You do not have permission to manage this exam.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = self.exam
        context["questions"] = self.exam.questions.prefetch_related("choices").all()
        context["form"] = QuestionForm()
        return context


class ChoiceCreateView(TeacherRequiredMixin, CreateView):
    model = Choice
    form_class = ChoiceForm
    template_name = "exams/choice_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.question = get_object_or_404(
            Question.objects.select_related("exam"),
            pk=kwargs["question_pk"],
            exam__created_by=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.question = self.question
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("exam_detail", kwargs={"pk": self.question.exam_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        return context


class TakeExamView(LoginRequiredMixin, TemplateView):
    template_name = "exams/take_exam.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_staff:
            return HttpResponseForbidden("Teacher accounts cannot take student exams.")
        self.exam = get_object_or_404(Exam, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def _get_or_start_attempt(self):
        try:
            attempt, _ = ExamAttempt.objects.get_or_create(user=self.request.user, exam=self.exam)
        except IntegrityError:
            attempt = ExamAttempt.objects.get(user=self.request.user, exam=self.exam)
        return attempt

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self._get_or_start_attempt()
        if attempt.is_completed:
            context["already_taken"] = True
            context["attempt"] = attempt
            return context
        remaining = max(0, int((attempt.deadline - timezone.now()).total_seconds()))
        if remaining == 0:
            attempt.completed_at = timezone.now()
            attempt.total_points = sum(self.exam.questions.values_list("points", flat=True))
            attempt.save(update_fields=["completed_at", "total_points"])
            context["already_taken"] = True
            context["attempt"] = attempt
            context["expired"] = True
            return context
        context["exam"] = self.exam
        context["attempt"] = attempt
        context["remaining_seconds"] = remaining
        context["questions"] = self.exam.questions.prefetch_related("choices").all()
        return context

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            attempt = get_object_or_404(
                ExamAttempt.objects.select_for_update(), user=request.user, exam=self.exam
            )
            if attempt.is_completed:
                return redirect("exam_result", pk=attempt.pk)
            if timezone.now() >= attempt.deadline:
                attempt.total_points = sum(self.exam.questions.values_list("points", flat=True))
                attempt.completed_at = timezone.now()
                attempt.save(update_fields=["total_points", "completed_at"])
                messages.error(request, "The exam time has expired. Late answers were not accepted.")
                return redirect("exam_result", pk=attempt.pk)

            questions = list(self.exam.questions.all())
            score = 0
            total_points = sum(question.points for question in questions)
            for question in questions:
                choice_id = request.POST.get(f"question_{question.pk}")
                if not choice_id:
                    continue
                choice = Choice.objects.filter(pk=choice_id, question=question).first()
                if choice is None:
                    continue
                answer, _ = StudentAnswer.objects.get_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={"choice": choice},
                )
                if answer.choice.is_correct:
                    score += question.points

            attempt.score = score
            attempt.total_points = total_points
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=["score", "total_points", "completed_at"])
        return redirect("exam_result", pk=attempt.pk)


class ExamResultView(LoginRequiredMixin, TemplateView):
    template_name = "exams/exam_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = get_object_or_404(ExamAttempt, pk=self.kwargs["pk"], user=self.request.user)
        context["attempt"] = attempt
        context["percentage"] = round((attempt.score / attempt.total_points) * 100, 1) if attempt.total_points else 0
        return context


class ExamReportView(TeacherRequiredMixin, TemplateView):
    template_name = "exams/exam_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs["pk"], created_by=self.request.user)
        attempts = ExamAttempt.objects.filter(exam=exam, completed_at__isnull=False).select_related("user").order_by("-completed_at")
        percentages = [attempt.score / attempt.total_points * 100 for attempt in attempts if attempt.total_points]
        context.update({"exam": exam, "attempts": attempts, "avg_score": round(sum(percentages) / len(percentages), 1) if percentages else 0})
        return context
