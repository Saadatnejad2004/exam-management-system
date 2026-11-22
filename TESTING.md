# Security & Testing Report — Online Exam System

## Step 5: System Security Audit

Django provides robust, out-of-the-box security. Below is the evidence of how this system defends against common attacks.

### 1. Cross-Site Scripting (XSS)
**Test:** Try to create an Exam titled `<script>alert('XSS')</script>`.
**Result:** Django's template engine automatically escapes HTML characters. The script is rendered as plain text, not executed. **PASS**

### 2. Cross-Site Request Forgery (CSRF)
**Test:** Remove the `{% csrf_token %}` from any form in `take_exam.html` and submit an exam.
**Result:** Django blocks the request with a `403 Forbidden` error. Every POST request requires a valid, session-bound CSRF token. **PASS**

### 3. SQL Injection
**Test:** In the login field, enter `' OR 1=1 --` as the username.
**Result:** The Django ORM uses parameterized queries. The input is treated as a literal string, not executable SQL. The login fails safely. **PASS**

### 4. Broken Access Control (Route Protection)
**Test:** Log in as a Student, then manually navigate to `/exam/create/`.
**Result:** The `TeacherRequiredMixin` (`UserPassesTestMixin`) intercepts the request and returns a `403 Forbidden`. Students cannot create exams. **PASS**

### 5. Examination Integrity (Anti-Cheat)
**Test:** Take an exam, complete it, then manually navigate to `/exam/1/take/` again.
**Result:** The `TakeExamView` checks for an existing `ExamAttempt`. The student is blocked from re-taking the exam and sees a warning message. **PASS**

### 6. Password Security
**Test:** Register a user, then log into `/admin/` and inspect the `auth_user` table.
**Result:** Passwords are hashed using PBKDF2 with a SHA256 hash and a random salt. Plain-text passwords are never stored. **PASS**