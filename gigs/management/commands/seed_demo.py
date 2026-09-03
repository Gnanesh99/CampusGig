
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from gigs.models import Category, Gig
from applications.models import Application, Assignment
from payments.models import Payment


class Command(BaseCommand):
    help = "Seeds realistic demo data for CampusGig demonstration."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding CampusGig Demo Data..."))

        # 1. Accounts
        employer_email = "employer@campusgig.demo"
        student1_email = "student1@campusgig.demo"
        student2_email = "student2@campusgig.demo"
        password = "DemoPass123!"

        employer, _ = User.objects.get_or_create(
            email=employer_email,
            defaults={
                "first_name": "Alice",
                "last_name": "Employer",
                "is_verified_college_email": True,
            },
        )
        employer.set_password(password)
        employer.save()

        student1, _ = User.objects.get_or_create(
            email=student1_email,
            defaults={
                "first_name": "Bob",
                "last_name": "Student",
                "is_verified_college_email": True,
            },
        )
        student1.set_password(password)
        student1.save()

        student2, _ = User.objects.get_or_create(
            email=student2_email,
            defaults={
                "first_name": "Charlie",
                "last_name": "Student",
                "is_verified_college_email": True,
            },
        )
        student2.set_password(password)
        student2.save()

        # 2. Categories
        cat_design, _ = Category.objects.get_or_create(
            slug="design-media", defaults={"name": "Design & Media"}
        )
        cat_tech, _ = Category.objects.get_or_create(
            slug="tech-web", defaults={"name": "Tech & Web"}
        )
        cat_tutor, _ = Category.objects.get_or_create(
            slug="tutoring-academics", defaults={"name": "Tutoring & Academics"}
        )

        # 3. Gigs
        gig1, _ = Gig.objects.get_or_create(
            poster=employer,
            title="Campus Event Poster Design",
            defaults={
                "category": cat_design,
                "description": "Need an eye-catching poster for the upcoming Annual Cultural Fest.",
                "budget": Decimal("500.00"),
                "location": "Student Union / Remote",
            },
        )

        gig2, _ = Gig.objects.get_or_create(
            poster=employer,
            title="Python Script for Lab Data Analysis",
            defaults={
                "category": cat_tech,
                "description": "Help clean and process CSV research data using Pandas and Matplotlib.",
                "budget": Decimal("1500.00"),
                "location": "Remote",
            },
        )

        gig3, _ = Gig.objects.get_or_create(
            poster=employer,
            title="Calculus I Peer Tutoring",
            defaults={
                "category": cat_tutor,
                "description": "Looking for a 2-hour tutoring session for Calculus I midterm preparation.",
                "budget": Decimal("800.00"),
                "location": "Campus Library",
            },
        )

        # 4. Applications & Assignments

        # Application 1 (Hired & Completed)
        app1, _ = Application.objects.get_or_create(
            gig=gig1,
            applicant=student1,
            defaults={
                "cover_letter": "I am a graphic design major with 2 years experience making event banners.",
                "status": "hired",
            },
        )
        app1.status = "hired"
        app1.save()

        assignment1, _ = Assignment.objects.get_or_create(
            application=app1,
            defaults={
                "employer": employer,
                "student": student1,
                "status": "Completed",
                "submission_text": "Finished poster design in high-res PNG & PDF formats.",
                "completed_at": timezone.now(),
            },
        )
        assignment1.status = "Completed"
        if not assignment1.completed_at:
            assignment1.completed_at = timezone.now()
        assignment1.submission_text = "Finished poster design in high-res PNG & PDF formats."
        assignment1.save()

        payment1 = Payment.objects.get(assignment=assignment1)
        payment1.status = "Paid"
        payment1.save()

        # Application 2 (Hired & Submitted)
        app2, _ = Application.objects.get_or_create(
            gig=gig2,
            applicant=student2,
            defaults={
                "cover_letter": "Computer Science sophomore proficient in Python data analysis.",
                "status": "hired",
            },
        )
        app2.status = "hired"
        app2.save()

        assignment2, _ = Assignment.objects.get_or_create(
            application=app2,
            defaults={
                "employer": employer,
                "student": student2,
                "status": "Submitted",
                "submission_text": "Completed Pandas data cleaning script with Jupyter notebook demonstration.",
            },
        )
        assignment2.status = "Submitted"
        assignment2.submission_text = "Completed Pandas data cleaning script with Jupyter notebook demonstration."
        assignment2.save()

        # Application 3 (Pending)
        app3, _ = Application.objects.get_or_create(
            gig=gig3,
            applicant=student1,
            defaults={
                "cover_letter": "Aced Calculus I last semester with an A grade.",
                "status": "pending",
            },
        )

        # Application 4 (Shortlisted)
        app4, _ = Application.objects.get_or_create(
            gig=gig3,
            applicant=student2,
            defaults={
                "cover_letter": "Math minor and peer tutor at the campus tutoring center.",
                "status": "shortlisted",
            },
        )

        self.stdout.write(self.style.SUCCESS("\nDemo Data Successfully Seeded!"))
        self.stdout.write("--------------------------------------------------")
        self.stdout.write(self.style.WARNING("DEMO ACCOUNTS (Password for all: DemoPass123!):"))
        self.stdout.write(f"  • Employer: {employer_email}")
        self.stdout.write(f"  • Student 1: {student1_email}")
        self.stdout.write(f"  • Student 2: {student2_email}")
        self.stdout.write("--------------------------------------------------")
        self.stdout.write("  • Gigs Created: 3")
        self.stdout.write("  • Applications Created: 4 (Statuses: Hired, Shortlisted, Pending)")
        self.stdout.write("  • Assignments Created: 2 (Statuses: Completed, Submitted)")
        self.stdout.write("  • Payments Created: 2 (Statuses: Paid, Pending)")
