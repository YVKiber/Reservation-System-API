#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "PostgreSQL is ready."

python manage.py migrate

python manage.py runserver 0.0.0.0:8000