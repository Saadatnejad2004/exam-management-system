from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from .forms import UserRegisterForm, ExamForm, QuestionForm, ChoiceForm
from .models import Exam, Question, Choice, ExamAttempt, StudentAnswer
from django.db.models import Avg

# ============ AUTHENTICATION ============

class CustomLoginView(LoginView):
    template_name = 'exams/login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('is_teacher'):
                user.is_staff = True
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'exams/register.html', {'form': form})

# ============ DASHBOARD & TEACHER MODULES ============

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'exams/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            # Teacher sees exams they created
            context['exams'] = Exam.objects.filter(created_by=self.request.user).order_by('-created_at')
        else:
            # Student sees all available exams (we'll add taking exams in Phase C)
            context['exams'] = Exam.objects.all().order_by('-created_at')
        return context

class TeacherRequiredMixin(UserPassesTestMixin):
    """Restricts access to Teachers only."""
    def test_func(self):
        return self.request.user.is_staff

class ExamCreateView(TeacherRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'

    def form_valid(self, form):
        # Assign the currently logged-in teacher as the creator
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # After creating an exam, go add questions to it
        return reverse_lazy('exam_detail', kwargs={'pk': self.object.pk})

class QuestionCreateView(TeacherRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'exams/question_form.html'

    def form_valid(self, form):
        # Link the question to the exam from the URL
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        form.instance.exam = exam
        return super().form_valid(form)

    def get_success_url(self):
        # Stay on the same page to add another question
        return reverse_lazy('exam_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = get_object_or_404(Exam, pk=self.kwargs['pk'])
        return context

class ExamDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'exams/exam_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        context['exam'] = exam
        context['questions'] = exam.questions.all()
        context['form'] = QuestionForm()
        return context

# ============ TEACHER: ADD CHOICES ============

class ChoiceCreateView(TeacherRequiredMixin, CreateView):
    model = Choice
    form_class = ChoiceForm
    template_name = 'exams/choice_form.html'

    def form_valid(self, form):
        question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
        form.instance.question = question
        return super().form_valid(form)

    def get_success_url(self):
        # After adding a choice, go back to the exam detail page
        question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
        return reverse_lazy('exam_detail', kwargs={'pk': question.exam.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = get_object_or_404(Question, pk=self.kwargs['question_pk'])
        return context

# ============ STUDENT: TAKE EXAM ============

class TakeExamView(LoginRequiredMixin, TemplateView):
    template_name = 'exams/take_exam.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        
        # Security: Check if the student already took this exam
        if ExamAttempt.objects.filter(user=self.request.user, exam=exam).exists():
            context['already_taken'] = True
            return context
            
        context['exam'] = exam
        # Optimize query: prefetch choices so we don't hit the DB for every question
        context['questions'] = exam.questions.prefetch_related('choices').all()
        return context

    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        
        if ExamAttempt.objects.filter(user=request.user, exam=exam).exists():
            return redirect('dashboard')

        score = 0
        total_points = 0
        attempt = ExamAttempt.objects.create(user=request.user, exam=exam)
        
        questions = exam.questions.all()
        for q in questions:
            total_points += q.points
            choice_id = request.POST.get(f'question_{q.id}')
            
            if choice_id:
                try:
                    choice = Choice.objects.get(id=choice_id, question=q)
                    # Record the student's answer
                    StudentAnswer.objects.create(attempt=attempt, question=q, choice=choice)
                    
                    # Calculate score
                    if choice.is_correct:
                        score += q.points
                except Choice.DoesNotExist:
                    pass # Invalid choice submitted

        # Save final score
        attempt.score = score
        attempt.total_points = total_points
        attempt.save()

        return redirect('exam_result', pk=attempt.pk)

# ============ STUDENT: VIEW RESULT ============

class ExamResultView(LoginRequiredMixin, TemplateView):
    template_name = 'exams/exam_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = get_object_or_404(ExamAttempt, pk=self.kwargs['pk'], user=self.request.user)
        context['attempt'] = attempt
        # Calculate percentage
        if attempt.total_points > 0:
            context['percentage'] = round((attempt.score / attempt.total_points) * 100, 1)
        else:
            context['percentage'] = 0
        return context


class ExamReportView(TeacherRequiredMixin, TemplateView):
    template_name = 'exams/exam_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'], created_by=self.request.user)
        
        # Fetch all attempts for this exam
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('user').order_by('-completed_at')
        
        # Calculate average score percentage using Python (since total_points can vary per attempt, but usually it's the same)
        total_percentage = 0
        for attempt in attempts:
            if attempt.total_points > 0:
                total_percentage += (attempt.score / attempt.total_points) * 100
        
        avg_score = round(total_percentage / attempts.count(), 1) if attempts.exists() else 0

        context['exam'] = exam
        context['attempts'] = attempts
        context['avg_score'] = avg_score
        return context