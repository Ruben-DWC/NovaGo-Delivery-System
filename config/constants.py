"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
Módulo de Calidad, Pruebas Automatizadas y Telemetría Health Check (APF3).
Autor: Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe)
"""
from decimal import Decimal

# Versión y metadatos del sistema (Avance 3 - Calidad, CI y Monitoreo)
APP_VERSION = "0.3.0-apf3-qa"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "testing-qa"
CANONICAL_PORTAL_PREFIX = "/portal/"

# Monitoreo de Disponibilidad y Métricas de Rendimiento
HEALTHCHECK_ROUTE = "/health/"
TELEMETRY_LATENCY_ALERT_MS = 250
METRICS_PROMETHEUS_ENABLED = True

# Parámetros operativos y capacidad de motorizados (Ajuste QA)
DELIVERY_FEE_BASE = Decimal("5.00")
DELIVERY_FREE_THRESHOLD = Decimal("50.00")
DEFAULT_ETA_MINUTES = 25
MAX_ACTIVE_ORDERS_PER_RIDER = 4  # Calibración operativa ampliada para motorizados
