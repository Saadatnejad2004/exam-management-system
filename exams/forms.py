from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Exam, Question, Choice

# ============ AUTH FORMS ============

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_teacher = forms.BooleanField(required=False, label="Register as a Teacher")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_teacher']

# ============ EXAM FORMS ============

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration_minutes']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter the question...'}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']