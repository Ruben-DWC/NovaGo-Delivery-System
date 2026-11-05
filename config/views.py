"""
Vistas de monitoreo y diagnóstico de NovaGo Delivery System.
Módulo de Telemetría y Health Check para Orquestación Cloud y Docker (APF3).
Autor: Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe)
"""
import time
from django.http import JsonResponse
from django.db import connection
from config.constants import APP_VERSION, APP_NAME

def healthcheck_view(request):
    """
    Endpoint de sondeo de estado operativo para sondas Liveness/Readiness
    en plataformas Cloud (Northflank, Kubernetes, Docker Healthchecks).
    """
    start_time = time.time()
    db_status = "connected"
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as ex:
        db_status = f"disconnected: {str(ex)}"
        
    latency_ms = round((time.time() - start_time) * 1000, 2)
    is_healthy = (db_status == "connected")
    status_code = 200 if is_healthy else 503
    
    return JsonResponse({
        "status": "healthy" if is_healthy else "unhealthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "database": db_status,
        "latency_ms": latency_ms,
        "checks": {
            "database": "pass" if is_healthy else "fail",
            "routing": "pass"
        }
    }, status=status_code)
