# CampusGig

CampusGig is a Django web application that connects students with short-term gigs (freelance-style jobs) posted by employers within a campus community. It handles the full lifecycle of a gig: posting, applying, hiring, assignment submission, review, and payment through Razorpay.

## Features

- **Custom accounts app** — email-based authentication (no usernames), with student profiles that track college, department, skills, portfolio links, rating, and completed-gig count.
- **Gig postings** — employers create, edit, and delete gigs with a title, description, category, budget, and location.
- **Applications** — students apply to gigs with a cover letter; employers review and update application status (pending, shortlisted, rejected, hired).
- **Assignments** — once a student is hired, an assignment is created automatically to track progress (assigned → in progress → submitted → completed), including file/text submission and employer feedback.
- **Payments** — a `Payment` record is created automatically alongside each assignment and is processed through the [Razorpay](https://razorpay.com/) checkout and webhook flow.
- **Employer and student dashboards** — separate views for each side of the marketplace to track gigs, applications, assignments, and payment status.
- **Demo data seeding** — a management command populates the database with realistic sample employers, students, gigs, applications, and payments.

## Tech Stack

- **Backend:** Django 4.2 (Python 3.12)
- **Database:** PostgreSQL (via `psycopg`)
- **Payments:** Razorpay
- **Static files / deployment:** WhiteNoise, Gunicorn
- **Config:** `python-dotenv` for environment variables, with split settings for local and production

## Project Structure

```
CampusGig/
├── accounts/        # Custom User model, student profiles, auth forms
├── gigs/            # Gig postings, categories, demo data seeding
├── applications/    # Applications and assignments (hire → work → review)
├── payments/        # Razorpay integration and payment records
├── templates/        # Base templates and shared pages
├── campusgig/        # Project settings (base/local/production), URLs, WSGI/ASGI
└── manage.py
```

## Getting Started

### Prerequisites

- Python 3.12
- PostgreSQL running locally (or accessible via connection settings)
- A Razorpay account (test keys are fine for development)

### 1. Clone the repository

```bash
git clone https://github.com/Gnanesh99/CampusGig.git
cd CampusGig
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=campusgig
POSTGRES_USER=campusgig
POSTGRES_PASSWORD=campusgigpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
```

The app defaults to `campusgig.settings.local` for development. Set `DJANGO_SETTINGS_MODULE=campusgig.settings.production` for a production-style run (this also enables WhiteNoise, SSL-required DB connections, and `CSRF_TRUSTED_ORIGINS`).

### 4. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. (Optional) Seed demo data

```bash
python manage.py seed_demo
```

This creates a sample employer, students, gigs, applications, an assignment, and a payment so you can explore the app immediately.

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Key URLs

| Path | Description |
|---|---|
| `/` | Home page |
| `/gigs/` | Browse, create, and manage gig postings |
| `/applications/dashboard/` | Student dashboard (applications & assignments) |
| `/applications/employer/dashboard/` | Employer dashboard (applications & assignments) |
| `/payments/<id>/checkout/` | Razorpay checkout for a payment |
| `/accounts/login/` | Login (Django's built-in auth views) |
| `/admin/` | Django admin |

## Deployment

The `production` settings are configured for a PythonAnywhere-style deployment using Gunicorn and WhiteNoise for static files, with PostgreSQL over SSL. Collect static files before deploying:

```bash
python manage.py collectstatic --noinput
```
But check that PythonAnywhere does not support PostgreSQL freely and it also does not support external database connections, so this project was deployed in  Render.

https://campusgig-e5w8.onrender.com/

## Contributing

Issues and pull requests are welcome. Please keep changes focused and avoid unrelated refactors.

## License

No license has been specified for this project yet.
