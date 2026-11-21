# Imagen del backend de Hilo Clínico para el despliegue (Railway, Render o cualquier host con Docker).
FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# El host inyecta PORT. Un solo proceso: las simulaciones viven en memoria (app/api/almacen.py).
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
