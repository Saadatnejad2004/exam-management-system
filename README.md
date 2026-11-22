# Online Examination System (Django)

A secure, full-stack productivity application built with Python/Django to facilitate online testing, automated grading, and performance reporting.

## Features
- **Authentication:** Role-based access (Teachers vs. Students) using Django's built-in `User` model.
- **Examination Modules:** Teachers can create exams, add multiple-choice questions, and define point values.
- **Automated Grading:** Instant result calculation upon submission.
- **Performance Reports:** Teachers can view class averages and individual student scores.
- **Security:** Protects against XSS, CSRF, SQL Injection, and unauthorized access.

## Tech Stack
- Python 3.12+
- Django 5.x
- SQLite (Development)
- HTML/CSS (Server-side rendered templates)

## Getting Started
1. `python -m venv venv`
2. `source venv/bin/activate`
3. `pip install django`
4. `python manage.py migrate`
5. `python manage.py runserver`
6. Register a Teacher account (check the box) to create an exam.
7. Register a Student account (leave unchecked) to take an exam.