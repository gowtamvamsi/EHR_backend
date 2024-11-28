#!/bin/bash

# Wait for database to be ready
python manage.py wait_for_db

# Run migrations
python manage.py migrate

# Create superuser if needed (using environment variables)
if [[ -n "${DJANGO_SUPERUSER_USERNAME}" ]] && [[ -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
fi

# Load initial data if needed
python manage.py loaddata initial_data