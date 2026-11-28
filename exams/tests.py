from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ExamForm
from .models import Choice, Exam, ExamAttempt, Question, StudentAnswer


class ExamSecurityAndTimingTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="StrongPass123!", is_staff=True)
        self.other_teacher = User.objects.create_user(username="other", password="StrongPass123!", is_staff=True)
        self.student = User.objects.create_user(username="student", password="StrongPass123!")
        self.exam = Exam.objects.create(title="Physics", duration_minutes=30, created_by=self.teacher)
        self.question = Question.objects.create(exam=self.exam, text="2 + 2?", points=2)
        self.correct = Choice.objects.create(question=self.question, text="4", is_correct=True)
        self.wrong = Choice.objects.create(question=self.question, text="5", is_correct=False)

    def test_public_registration_cannot_create_teacher(self):
        response = self.client.post(reverse("register"), {
            "username": "newstudent", "email": "student@example.com",
            "password1": "SafePass123!", "password2": "SafePass123!", "is_teacher": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.get(username="newstudent").is_staff)

    def test_teacher_cannot_manage_another_teachers_exam(self):
        self.client.login(username="other", password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("exam_detail", args=[self.exam.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("question_create", args=[self.exam.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("choice_create", args=[self.question.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("exam_report", args=[self.exam.pk])).status_code, 404)

    def test_student_cannot_open_teacher_management_page(self):
        self.client.login(username="student", password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("exam_detail", args=[self.exam.pk])).status_code, 403)

    def test_teacher_cannot_take_exam_as_a_student(self):
        self.client.login(username="teacher", password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("take_exam", args=[self.exam.pk])).status_code, 403)

    def test_exam_duration_must_be_at_least_one_minute(self):
        form = ExamForm(data={"title": "Invalid duration", "description": "", "duration_minutes": 0})
        self.assertFalse(form.is_valid())
        self.assertIn("duration_minutes", form.errors)

    def test_attempt_is_created_once_and_timer_survives_refresh(self):
        self.client.login(username="student", password="StrongPass123!")
        url = reverse("take_exam", args=[self.exam.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        attempt = ExamAttempt.objects.get(user=self.student, exam=self.exam)
        original_start = attempt.started_at
        self.client.get(url)
        attempt.refresh_from_db()
        self.assertEqual(attempt.started_at, original_start)

    def test_submission_is_graded_and_locked_after_completion(self):
        self.client.login(username="student", password="StrongPass123!")
        url = reverse("take_exam", args=[self.exam.pk])
        self.client.get(url)
        attempt = ExamAttempt.objects.get(user=self.student, exam=self.exam)
        response = self.client.post(url, {f"question_{self.question.pk}": str(self.correct.pk)})
        self.assertRedirects(response, reverse("exam_result", args=[attempt.pk]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 2)
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(attempt.answers.count(), 1)
        self.assertRedirects(self.client.post(url, {}), reverse("exam_result", args=[attempt.pk]))

    def test_expired_attempt_rejects_late_answers(self):
        self.client.login(username="student", password="StrongPass123!")
        url = reverse("take_exam", args=[self.exam.pk])
        self.client.get(url)
        attempt = ExamAttempt.objects.get(user=self.student, exam=self.exam)
        attempt.started_at = timezone.now() - timedelta(minutes=31)
        attempt.save(update_fields=["started_at"])
        response = self.client.post(url, {f"question_{self.question.pk}": str(self.correct.pk)})
        self.assertRedirects(response, reverse("exam_result", args=[attempt.pk]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.answers.count(), 0)
        self.assertIsNotNone(attempt.completed_at)

    def test_invalid_choice_from_another_question_is_ignored(self):
        another_question = Question.objects.create(exam=self.exam, text="Other?", points=1)
        another_choice = Choice.objects.create(question=another_question, text="Other answer", is_correct=True)
        self.client.login(username="student", password="StrongPass123!")
        url = reverse("take_exam", args=[self.exam.pk])
        self.client.get(url)
        attempt = ExamAttempt.objects.get(user=self.student, exam=self.exam)
        self.client.post(url, {f"question_{self.question.pk}": str(another_choice.pk)})
        self.assertFalse(StudentAnswer.objects.filter(attempt=attempt).exists())

    def test_answer_uniqueness_constraint(self):
        attempt = ExamAttempt.objects.create(user=self.student, exam=self.exam)
        StudentAnswer.objects.create(attempt=attempt, question=self.question, choice=self.correct)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudentAnswer.objects.create(attempt=attempt, question=self.question, choice=self.correct)
