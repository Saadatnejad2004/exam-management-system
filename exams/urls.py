from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Dashboard & Modules
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('exam/create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('exam/<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('exam/<int:pk>/add-question/', views.QuestionCreateView.as_view(), name='question_create'),

    # Teacher: Add Choices
    path('question/<int:question_pk>/add-choice/', views.ChoiceCreateView.as_view(), name='choice_create'),
    
    # Student: Take & Submit Exam
    path('exam/<int:pk>/take/', views.TakeExamView.as_view(), name='take_exam'),
    path('result/<int:pk>/', views.ExamResultView.as_view(), name='exam_result'),
]