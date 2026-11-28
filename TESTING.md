# Automated and Manual Testing

## Automated tests

Run the test suite with:

```bash
python manage.py test
```

The automated suite covers:
- Public registration cannot grant teacher privileges.
- Teachers can only manage their own exams, questions, choices, and reports.
- Students cannot open teacher management screens or take exams using a teacher account.
- Exam duration validation.
- An attempt is created once and its start time survives refreshes.
- Correct answer grading and one-attempt enforcement.
- Server-side expiration rejects late answers.
- Choices belonging to another question are ignored.
- Database uniqueness prevents duplicate answers for one question in an attempt.

## Manual smoke test

1. Create a teacher using `createsuperuser` or promote a user through Django admin (`is_staff=True`).
2. Create an exam with a duration of at least one minute.
3. Add questions and choices, marking the correct choice for each question.
4. Register a normal student account and start the exam.
5. Refresh the exam page and confirm the countdown continues from the original start time.
6. Submit before the deadline and verify the result and teacher report.
7. Start another attempt and wait for the deadline; verify late answers are rejected.
8. Log in as a different teacher and confirm the first teacher's exam cannot be managed or reported.

Automated tests have not been executed in this delivery environment because Django dependencies could not be installed (network access to the package index was unavailable). Python syntax compilation was completed successfully.
