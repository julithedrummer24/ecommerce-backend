# Imagen base de Python
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Copiar archivos y requerimientos
COPY requirements.txt /app/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install psycopg2-binary

# Copiar el código del proyecto
COPY . /app/

COPY wait_for_db.sh /wait_for_db.sh
RUN chmod +x /wait_for_db.sh

# Comando por defecto
CMD ["wait_for_db.sh","python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
