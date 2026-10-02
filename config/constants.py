"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
"""
from decimal import Decimal

# Versión y metadatos del sistema
APP_VERSION = "0.2.0-apf2-core"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "development"
CANONICAL_PORTAL_PREFIX = "/portal/"

# Tarifas base y parámetros de delivery (Gestión Operativa)
DELIVERY_FEE_BASE = Decimal("5.00")
DELIVERY_FREE_THRESHOLD = Decimal("55.00")
DEFAULT_ETA_MINUTES = 25
MAX_ACTIVE_ORDERS_PER_RIDER = 3
