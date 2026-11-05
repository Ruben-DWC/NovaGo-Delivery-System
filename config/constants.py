"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
Versión unificada y conciliada colaborativamente para el Avance 3 (APF3).
Integrantes del Equipo (Modalidad Dúo Oficial UTP):
- Ruben Walter Vivas Jimenez (Ruben-DWC / u22224908@utp.edu.pe) - Arquitectura Backend & Docker
- Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe) - Calidad, CI/CD & Telemetría
"""
from decimal import Decimal

# Versión y metadatos del sistema (Consolidación Oficial APF3)
APP_VERSION = "0.3.0-apf3"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "production-container"
CANONICAL_PORTAL_PREFIX = "/portal/"

# Infraestructura Cloud & Orquestación de Contenedores
DEPLOYMENT_PLATFORM = "Northflank Cloud PaaS / Docker Engine 29.x"
CLOUD_DATABASE_ENGINE = "PostgreSQL 16 Relational Engine"
CI_CD_ORCHESTRATOR = "GitHub Actions Automation (CI/CD)"

# Monitoreo de Disponibilidad, Health Check y Métricas
HEALTHCHECK_ROUTE = "/health/"
TELEMETRY_LATENCY_ALERT_MS = 250
METRICS_PROMETHEUS_ENABLED = True

# Parámetros operativos y capacidad de motorizados (Consenso Operativo y Comercial)
DELIVERY_FEE_BASE = Decimal("5.00")
DELIVERY_FREE_THRESHOLD = Decimal("50.00")  # Beneficio comercial acordado para clientes
DEFAULT_ETA_MINUTES = 25
MAX_ACTIVE_ORDERS_PER_RIDER = 4  # Capacidad máxima ajustada para alta demanda
