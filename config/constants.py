"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
"""
from decimal import Decimal

# Versión y metadatos del sistema
APP_VERSION = "0.2.0-apf2-client"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "development"

# Tarifas base y parámetros de delivery (Promoción Portal Cliente)
DELIVERY_FEE_BASE = Decimal("4.50")
DELIVERY_FREE_THRESHOLD = Decimal("50.00")
DEFAULT_ETA_MINUTES = 20
MAX_ACTIVE_ORDERS_PER_RIDER = 2
