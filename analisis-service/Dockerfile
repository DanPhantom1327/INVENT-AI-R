
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del servicio
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries=10 -r requirements.txt

# Copiar el código de análisis
COPY . .

# Puerto interno de Django
EXPOSE 8000

# Arrancar el servicio
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
