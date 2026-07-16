#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py collectstatic --noinput

exec gunicorn reservation_system_api.wsgi:application --bind 0.0.0.0:8000