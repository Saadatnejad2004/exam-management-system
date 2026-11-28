# Online Examination System (Django)

A server-rendered online examination platform with teacher-managed exams, multiple-choice questions, automatic grading, and student results.

## Features
- Student registration and login; teacher accounts are provisioned by an administrator.
- Teachers create and manage only their own exams, questions, choices, and reports.
- One attempt per student and exam.
- Server-enforced exam deadlines that persist across page refreshes.
- Automatic grading and protected student results.

## Requirements
- Python 3.12+
- Django 6.1.x (see `requirements.txt`)

## Local setup
1. `python -m venv .venv`
2. Activate the environment (`source .venv/bin/activate` on macOS/Linux).
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and replace the example secret, or set the environment variables directly. The settings load `.env` automatically.
5. `python manage.py migrate`
6. Create a teacher account with `python manage.py createsuperuser`, or promote an existing user through Django admin by setting `is_staff=True`.
7. `python manage.py runserver`

Public registration intentionally creates student accounts only. Do not expose teacher privileges through a public registration form.

## Configuration
- `DJANGO_SECRET_KEY`: required for production; use a long random secret.
- `DJANGO_DEBUG`: defaults to `False`.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames.
- `DJANGO_EMAIL_*`: optional email backend and SMTP configuration.

## Tests
Run `python manage.py test` after installing dependencies.
