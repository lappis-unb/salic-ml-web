#!/usr/bin/env bash

python3 manage.py makemigrations
python3 manage.py migrate
python manage.py collectstatic --noinput
echo "** Caching information **"
sh redis_cache.sh
echo "** Attempting to start service **"
# python3 manage.py runserver 0.0.0.0:8080
gunicorn --env DJANGO_SETTINGS_MODULE=salic_ml_web.settings -b :8080 salic_ml_web.wsgi --reload --timeout 120