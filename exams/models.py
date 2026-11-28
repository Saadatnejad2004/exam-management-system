from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils import timezone


class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1)])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_exams")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(duration_minutes__gte=1), name="exam_duration_at_least_one_minute"),
        ]

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.exam.title} - Q{self.pk}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} (Correct: {self.is_correct})"


class ExamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "exam"), name="unique_user_exam_attempt"),
        ]
        ordering = ("-started_at",)

    @property
    def is_completed(self):
        return self.completed_at is not None

    @property
    def deadline(self):
        from datetime import timedelta
        return self.started_at + timedelta(minutes=self.exam.duration_minutes)

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.score}/{self.total_points}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("attempt", "question"), name="unique_answer_per_attempt_question"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.choice_id and self.question_id and self.choice.question_id != self.question_id:
            raise ValidationError({"choice": "The selected choice must belong to this question."})
        if self.attempt_id and self.question_id and self.attempt.exam_id != self.question.exam_id:
            raise ValidationError({"question": "The question must belong to the attempted exam."})

    def __str__(self):
        return f"Attempt {self.attempt_id} - Q{self.question_id}"
