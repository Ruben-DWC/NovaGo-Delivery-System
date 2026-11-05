"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
Módulo de Arquitectura, Contenedores Docker y Despliegue Cloud (APF3).
Autor: Ruben Walter Vivas Jimenez (Ruben-DWC / u22224908@utp.edu.pe)
"""
from decimal import Decimal

# Versión y metadatos del sistema (Avance 3 - Infraestructura Cloud & Docker)
APP_VERSION = "0.3.0-apf3-infra"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "production-ready"
CANONICAL_PORTAL_PREFIX = "/portal/"

# Infraestructura de Contenedores y Plataforma Cloud
DEPLOYMENT_PLATFORM = "Northflank Cloud PaaS / Docker Engine 29.x"
CLOUD_DATABASE_ENGINE = "PostgreSQL 16 Relational Engine"
CI_CD_ORCHESTRATOR = "GitHub Actions Automation (CI/CD)"

# Tarifas base y parámetros de delivery
DELIVERY_FEE_BASE = Decimal("5.00")
DELIVERY_FREE_THRESHOLD = Decimal("50.00")
DEFAULT_ETA_MINUTES = 25
MAX_ACTIVE_ORDERS_PER_RIDER = 3
