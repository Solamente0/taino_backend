#! /bin/sh

cd /home/app/api || exit

 python manage.py migrate &&
  gunicorn --log-level=debug -w 5 --bind :8088 --timeout 1900 config.wsgi --reload
