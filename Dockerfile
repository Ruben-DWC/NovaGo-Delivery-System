# ==============================================================================
# Dockerfile para NovaGo Delivery System (Entorno de Producción y Cloud)
# Avance de Proyecto Final 03 (APF3) - Herramientas de Desarrollo
# Autor: Ruben Walter Vivas Jimenez (Ruben-DWC / u22224908@utp.edu.pe)
# ==============================================================================

FROM python:3.13-slim AS base

# Prevenir escritura de archivos .pyc y activar salida sin buffer para logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema requeridas para Pillow, PostgreSQL y networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar manifiesto de dependencias e instalar
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo de la aplicación
COPY . /app/

# Crear directorios para estáticos y multimedia con permisos adecuados
RUN mkdir -p /app/staticfiles /app/media

# Crear usuario sin privilegios root por estándares de ciberseguridad (CIS Benchmark)
RUN useradd -m -u 1000 novago_user && \
    chown -R novago_user:novago_user /app

USER novago_user

# Exponer el puerto de servicio web
EXPOSE 8000

# Healthcheck nativo para orquestadores Docker y plataformas Cloud (Northflank/K8s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando de inicio del servidor ASGI/WSGI de alto rendimiento
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
