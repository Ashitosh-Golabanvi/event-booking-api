# Event Booking API

[![Django CI](https://github.com/Ashitosh-Golabanvi/event-booking-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashitosh-Golabanvi/event-booking-api/actions/workflows/ci.yml)

A RESTful event booking system built with Django REST Framework and PostgreSQL. It supports organizer-managed events, attendee bookings, booking cancellation, JWT authentication, and organizer sales dashboards.

## Features

- User registration and JWT authentication.
- Organizer and attendee roles.
- Event creation, editing, publishing, cancellation, and draft deletion.
- Public listing of upcoming published events.
- Event filtering by city, date range, price, and free-only status.
- Search by event title and description.
- Sorting and pagination.
- Remaining-seat information.
- Booking of 1–5 seats per request.
- Prevention of duplicate confirmed bookings for the same attendee and event.
- Booking cancellation subject to the 24-hour restriction.
- Automatic cancellation of bookings when an event is cancelled.
- Organizer dashboard with booking counts, available seats, and gross revenue.
- Attendee booking details and non-guessable booking references.
- Django Admin for managing users, events, and bookings.
- Swagger UI, ReDoc, and OpenAPI schema.
- Automated tests and repeatable demo-data seeding.
- GitHub Actions CI for automated configuration, migration, and test checks.

## Tech Stack

- Python 3.12+
- Django 5.2
- Django REST Framework
- PostgreSQL
- Simple JWT
- drf-spectacular
- Docker and Docker Compose
- GitHub Actions

## Prerequisites

- Git
- Python 3.12 or newer, for local development
- Docker Desktop, for containerized setup

## Setup Option 1: Docker Compose (Recommended)

### 1. Clone the repository

```bash
git clone https://github.com/Ashitosh-Golabanvi/event-booking-api.git
cd event-booking-api
```

### 2. Configure environment variables

Create your local environment file.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Review `.env` and configure the required Django settings, including the secret key, debug setting, and allowed hosts.

Do not commit `.env` or expose secret keys, passwords, or production credentials.

### 3. Build and start the application

```bash
docker compose up --build -d
```

Docker Compose starts PostgreSQL and the Django application. The application container applies database migrations during startup.

Check the container status:

```bash
docker compose ps
```

View application logs if needed:

```bash
docker compose logs web
```

### 4. Open the application

- **Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **ReDoc:** [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **OpenAPI schema:** [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 5. Create an admin account

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to create the account.

### 6. Load demo data

```bash
docker compose exec web python manage.py seed_demo
```

The seed command creates or reuses demo users, events, and bookings. It can be run repeatedly without duplicating the existing demo records.

The command may reuse existing users when their email addresses match. Consequently, the usernames and passwords of reused accounts may differ from the newly created demo-account defaults. Check the command output before logging in.

The password `DemoPass123!` is used for users created by the seed command; it does not reset passwords on reused users. Demo credentials are intended for local testing only.

### 7. Run tests in Docker

```bash
docker compose exec web python manage.py test
```

### 8. Stop the application

```bash
docker compose down
```

This stops the containers without deleting the PostgreSQL data volume.

## Setup Option 2: Local Development

### 1. Clone the repository

```bash
git clone https://github.com/Ashitosh-Golabanvi/event-booking-api.git
cd event-booking-api
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Configure the Django settings and PostgreSQL credentials in `.env`.

### 5. Start PostgreSQL

You can start the database service with:

```bash
docker compose up -d db
```

For local Django execution, configure the database host and port to connect to the published PostgreSQL port in `docker-compose.yml` (port `6000` by default).

### 6. Apply migrations

```bash
python manage.py migrate
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API is available at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### 8. Run tests and configuration checks

Open a separate terminal from the project directory, activate the virtual environment, and run the test suite:

```bash
python manage.py test
```

Check Django configuration:

```bash
python manage.py check
```

Check whether model changes require new migrations:

```bash
python manage.py makemigrations --check --dry-run
```

## API Documentation

Swagger UI and ReDoc provide interactive API documentation, including endpoint paths, HTTP methods, request schemas, and response formats.

- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI schema:** `/api/schema/`

## Main API Endpoint Groups

| Endpoint group | Purpose |
|---|---|
| `/api/auth/` | Registration and authentication |
| `/api/events/` | Event listing, details, and event management |
| `/api/events/bookings/` | Booking operations |
| `/api/events/organizer/dashboard/` | Organizer dashboard and sales summaries |

Consult the generated API documentation for the complete list of endpoints and supported methods.

## Event Lifecycle and Permissions

Events follow the lifecycle:

`Draft → Published → Cancelled`

- Organizers manage their own events.
- Draft events can be edited or deleted.
- Published events can be cancelled rather than deleted.
- Publishing requires a future start time.
- Event cancellation also cancels associated bookings.
- Public event browsing is available without authentication; protected operations require authentication.
- Attendees can manage their own bookings, subject to booking rules.

## Booking and Concurrency

The booking flow uses PostgreSQL database transactions and row-level locking when checking and updating event seat availability. This helps serialize concurrent booking attempts for the same event and prevents requests from independently relying on the same stale seat count.

A database constraint also prevents multiple confirmed bookings for the same attendee and event. Booking references are generated separately from database IDs.

These guarantees rely on booking operations using the same PostgreSQL database and the implemented transaction, locking, and constraint strategy. The application must correctly acquire the relevant locks and perform seat validation and booking updates within the transaction. The included automated tests cover the implemented booking and event rules.

## Organizer Dashboard

The organizer dashboard summarizes the organizer's own events, confirmed bookings, seats booked, remaining seats, and gross revenue. Revenue and booking summaries use database aggregation rather than iterating over every booking in Python.

Organizers can also inspect event bookings with attendee details, seat counts, booking status, and booking timestamps.

## Running Tests

Run the complete test suite locally:

```bash
python manage.py test
```

Or inside Docker:

```bash
docker compose exec web python manage.py test
```

The current test suite contains 19 tests, all of which passed in the verified Docker environment.

Additional useful checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

The GitHub Actions workflow runs automatically on pushes to `main` and pull requests targeting `main`. It checks Django configuration, verifies migration consistency, and runs the automated test suite.

You can view the workflow and its results here:

[GitHub Actions — Django CI](https://github.com/Ashitosh-Golabanvi/event-booking-api/actions)

## Demo Data

To load demo users, events, and bookings:

```bash
python manage.py seed_demo
```

For Docker:

```bash
docker compose exec web python manage.py seed_demo
```

Read the command output to identify the actual demo usernames and whether any existing accounts were reused.

## Project Structure

```text
event-booking-api/
├── accounts/
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo.py
│   └── admin.py
├── events/
├── config/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

## Assumptions and Limitations

- The application uses PostgreSQL for its database and booking transaction behavior.
- The included Docker configuration runs Django's development server; production deployment should use a production-grade WSGI or ASGI server and appropriate security settings.
- Demo accounts are for local testing only. Change or replace demo credentials before any shared or production deployment.
- Booking cancellation follows the implemented 24-hour cutoff.
- Concurrency protection depends on the implemented PostgreSQL transaction, locking, and constraint strategy.
- API behavior and validation rules are documented in the generated API schema and covered by the automated test suite.

## License

This project was developed as an event booking API assessment.
