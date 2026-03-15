#!/bin/sh

echo "=============================="
echo "Aplicando migraciones..."
echo "=============================="
python manage.py migrate --noinput

echo "=============================="
echo "Recolectando archivos estáticos..."
echo "=============================="
python manage.py collectstatic --noinput

echo "=============================="
echo "Creando superusuario..."
echo "=============================="
python manage.py createsuperuser --noinput || true

echo "=============================="
echo "Iniciando Gunicorn..."
echo "=============================="
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120