from django.db import migrations, models
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("exams", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="exam",
            name="duration_minutes",
            field=models.PositiveIntegerField(default=60, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddConstraint(
            model_name="exam",
            constraint=models.CheckConstraint(condition=models.Q(("duration_minutes__gte", 1)), name="exam_duration_at_least_one_minute"),
        ),
        migrations.AlterUniqueTogether(name="examattempt", unique_together=set()),
        migrations.AddField(
            model_name="examattempt",
            name="started_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="examattempt",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="examattempt",
            constraint=models.UniqueConstraint(fields=("user", "exam"), name="unique_user_exam_attempt"),
        ),
        migrations.AddConstraint(
            model_name="studentanswer",
            constraint=models.UniqueConstraint(fields=("attempt", "question"), name="unique_answer_per_attempt_question"),
        ),
    ]
