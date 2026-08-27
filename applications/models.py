from django.conf import settings
from django.db import models

from gigs.models import Gig


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['gig', 'applicant'], name='unique_application_per_gig_and_applicant')
        ]

    def __str__(self):
        return f"{self.applicant} - {self.gig}"


class Assignment(models.Model):
    STATUS_CHOICES = [
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Submitted', 'Submitted'),
        ('Completed', 'Completed'),
    ]

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='assignment')
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Assigned')
    hired_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    submission_text = models.TextField(null=True, blank=True)
    submission_file = models.FileField(upload_to='assignment_submissions/', null=True, blank=True)
    employer_feedback = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        created = self._state.adding
        super().save(*args, **kwargs)

        if created:
            from payments.models import Payment

            Payment.objects.get_or_create(
                assignment=self,
                defaults={
                    'payer': self.employer,
                    'payee': self.student,
                    'amount': self.application.gig.budget,
                    'status': 'Pending',
                },
            )

    def __str__(self):
        return f"Assignment for {self.application}"
