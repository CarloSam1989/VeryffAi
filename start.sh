#!/bin/sh

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Creando superusuario si no existe..."

python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME")
email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superusuario creado.")
    else:
        print("Superusuario ya existe.")
else:
    print("Variables de superusuario no configuradas.")
END

echo "Iniciando servidor..."

gunicorn core.wsgi:application --bind 0.0.0.0:$PORT