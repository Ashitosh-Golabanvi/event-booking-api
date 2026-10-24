\# Event Booking API



A RESTful event booking system built using Django REST Framework and PostgreSQL. The API supports authentication, event management, attendee bookings, booking cancellation, and organizer dashboards.



\## Features



\- User registration and JWT authentication

\- Organizer and attendee roles

\- Event creation, updating, publishing, and cancellation

\- Public listing of upcoming published events

\- Event filtering, searching, sorting, and pagination

\- Booking creation with seat availability validation

\- Prevention of duplicate confirmed bookings

\- Booking cancellation with a 24-hour restriction

\- Organizer dashboard and event booking details

\- Interactive API documentation using Swagger UI and ReDoc

\- Automated API tests



\## Tech Stack



\- Python

\- Django

\- Django REST Framework

\- PostgreSQL

\- Simple JWT

\- drf-spectacular

\- Docker Compose



\## Prerequisites



\- Python installed

\- Docker Desktop

\- Git



\## Setup



\### 1. Clone the repository



```bash

git clone https://github.com/Ashitosh-Golabanvi/event-booking-api.git

cd event-booking-api

```



\### 2. Create and activate a virtual environment



Windows PowerShell:



```powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



\### 3. Install dependencies



```bash

pip install -r requirements.txt

```



\### 4. Configure environment variables



Copy `.env.example` to `.env` and update the values for your local environment.



Windows PowerShell:



```powershell

Copy-Item .env.example .env

```



Keep your `.env` file private. Never commit passwords, secret keys, or production credentials.



\### 5. Start PostgreSQL



```bash

docker compose up -d db

```



Ensure your `.env` database settings match the credentials and port configured in `docker-compose.yml`.



\### 6. Apply migrations



```bash

python manage.py migrate

```



\### 7. Run the development server



```bash

python manage.py runserver

```



\## API Documentation



With the server running, open:



\- Swagger UI: http://127.0.0.1:8000/api/docs/

\- ReDoc: http://127.0.0.1:8000/api/redoc/

\- OpenAPI schema: http://127.0.0.1:8000/api/schema/



\## API Endpoint Groups



| Endpoint | Purpose |

|---|---|

| `/api/auth/` | Authentication endpoints |

| `/api/events/` | Event listing and management |

| `/api/events/bookings/` | Booking operations |

| `/api/events/organizer/dashboard/` | Organizer dashboard |



Refer to Swagger UI for the complete endpoint list, HTTP methods, request bodies, and responses.



\## Running Tests



```bash

python manage.py test

```



\## Project Structure



```text

event-booking-api/

├── accounts/

├── events/

├── config/

├── manage.py

├── requirements.txt

├── docker-compose.yml

├── .env.example

└── README.md

```



\## License



This project was developed as an event booking API assessment.



