# Reservation System API

A full-stack Django reservation system for managing meeting rooms, room availability, and room bookings. The project includes a REST API, JWT authentication, a Django Templates frontend, staff management features, Docker-based PostgreSQL setup, and a production-like Gunicorn configuration.

## Features

### User features

- User registration with email verification
- Login and logout through the frontend
- JWT authentication for API access
- Password reset flow
- View available meeting rooms
- View room details and room availability by date
- Create room bookings
- View personal bookings
- Cancel own active bookings

### Staff features

- View all bookings in the system
- Update booking status: `PENDING`, `CONFIRMED`, `CANCELLED`, `COMPLETED`
- Create room types
- Create rooms
- Mark rooms as available or unavailable
- Upload room images when creating rooms
- Update or remove room images from the room detail page

### API features

- REST API built with Django REST Framework
- JWT authentication with SimpleJWT
- API documentation with Swagger and Redoc
- Filtering, search, ordering, and pagination support
- Booking conflict validation
- Room availability endpoint

## Tech stack

- Python 3.12
- Django 6
- Django REST Framework
- PostgreSQL
- SimpleJWT
- drf-spectacular
- django-filter
- Gunicorn
- WhiteNoise
- Docker and Docker Compose
- HTML, CSS, Django Templates
- GitHub Actions

## Project structure

```text
Reservation-System-API/
├── accounts/                  # Custom user, registration, verification, password reset
├── bookings/                  # Booking model, booking API, booking logic
├── frontend/                  # Django Templates frontend views, forms, and urls
├── reservation_system_api/    # Main Django project settings and urls
├── rooms/                     # Room types, rooms, room availability, room images
├── static/                    # CSS and static frontend assets
├── templates/                 # Base templates
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
├── requirements.txt
└── requests.http
```

## Main models

### RoomType

Represents a category of rooms, for example conference rooms, training rooms, or meeting rooms.

### Room

Represents a physical room that can be booked. A room has:

- name
- room type
- location
- capacity
- description
- image
- availability status

### Booking

Represents a reservation made by a user for a specific room and time period. Booking statuses:

- `PENDING`
- `CONFIRMED`
- `CANCELLED`
- `COMPLETED`

## Environment variables

Create a `.env` file for local development:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=reservation_api_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@reservation-api.local
FRONTEND_BASE_URL=http://127.0.0.1:8000

ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

For Docker, create `.env.docker`:

```env
SECRET_KEY=your-docker-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_NAME=reservation_api_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@reservation-api.local
FRONTEND_BASE_URL=http://127.0.0.1:8000

ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

Do not commit real `.env` files to GitHub.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/YVKiber/Reservation-System-API.git
cd Reservation-System-API
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Git Bash / Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database matching your `.env` values, for example:

```sql
CREATE DATABASE reservation_api_db;
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Docker setup

The project includes a Docker setup with a Django web container and a PostgreSQL database container.

### Build and start containers

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

Or run in detached mode:

```bash
docker compose up -d --build
```

The app will be available at:

```text
http://127.0.0.1:8000/
```

### Docker services

- `web` — Django application running with Gunicorn
- `db` — PostgreSQL database
- `postgres_data` — persistent PostgreSQL data volume
- `media_volume` — persistent uploaded media files volume

## Gunicorn and static files

Inside Docker, the application runs with Gunicorn:

```bash
gunicorn reservation_system_api.wsgi:application --bind 0.0.0.0:8000
```

Static files are collected automatically during container startup:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise is used for serving static files in the Docker-based setup.

On Windows, do not run Gunicorn directly from the local virtual environment. Use:

```bash
python manage.py runserver
```

for local development, and Docker for Gunicorn-based execution.

## API documentation

Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

Redoc:

```text
http://127.0.0.1:8000/api/redoc/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

## Main API endpoints

### Authentication

```text
POST /api/token/
POST /api/token/refresh/
```

### Accounts

```text
POST /api/accounts/register/
GET  /api/accounts/me/
PATCH /api/accounts/me/
POST /api/accounts/verify-email/
POST /api/accounts/resend-verification/
POST /api/accounts/change-password/
POST /api/accounts/password-reset/
POST /api/accounts/password-reset-confirm/
```

### Rooms

```text
GET    /api/room-types/
POST   /api/room-types/
GET    /api/rooms/
POST   /api/rooms/
GET    /api/rooms/{id}/
PATCH  /api/rooms/{id}/
DELETE /api/rooms/{id}/
GET    /api/rooms/{id}/availability/?date=YYYY-MM-DD
```

### Bookings

```text
GET  /api/bookings/
POST /api/bookings/
GET  /api/bookings/{id}/
POST /api/bookings/{id}/cancel/
POST /api/bookings/{id}/confirm/
POST /api/bookings/{id}/complete/
```

## Frontend pages

```text
/                         Home page
/login/                   Login
/logout/                  Logout
/register/                Registration
/verify-email/            Email verification result
/resend-verification/     Resend verification email
/password-reset/          Password reset request
/password-reset-confirm/  Password reset confirmation
/rooms/                   Rooms list
/rooms/<id>/              Room detail and availability
/rooms/create/            Staff room creation
/room-types/create/       Staff room type creation
/bookings/                User or staff bookings list
/bookings/create/         Create booking
```

## Room images

Staff users can upload room images. Recommended image characteristics:

- Format: JPG, JPEG, PNG, or WebP
- Recommended size: 1200×800 px or 1600×1000 px
- Recommended ratio: 3:2 or 16:9
- Orientation: horizontal
- Recommended file size: up to 1–2 MB

Uploaded images are stored in:

```text
media/rooms/
```

The `media/` directory should not be committed to GitHub.

## Booking rules

The system validates bookings to prevent invalid reservations:

- End time must be later than start time
- Booking start time cannot be in the past
- Users cannot book unavailable rooms
- Active bookings cannot overlap for the same room
- Cancelled and completed bookings are excluded from active conflict checks

## Roles and permissions

### Anonymous user

- Can view public pages
- Can view available rooms
- Can register and log in

### Authenticated user

- Can create bookings
- Can view own bookings
- Can cancel own active bookings
- Can view room availability

### Staff user

- Can view all bookings
- Can update booking statuses
- Can create room types
- Can create rooms
- Can make rooms available or unavailable
- Can upload, update, and remove room images

## Running tests

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

## Development notes

Useful commands:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Docker cleanup:

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

## Author

Developed as a Django REST Framework portfolio project focused on room booking, role-based access, API design, Docker deployment, and frontend integration with Django Templates.
