"""
Constantes de configuración y políticas operativas de NovaGo Delivery System.
Versión unificada y conciliada colaborativamente para el Avance 2 (APF2).
"""
from decimal import Decimal

# Versión y metadatos del sistema (Consolidación APF2)
APP_VERSION = "0.2.0-apf2"
APP_NAME = "NovaGo Delivery System"
APP_ENV = "development"
CANONICAL_PORTAL_PREFIX = "/portal/"

# Tarifas base y parámetros de delivery (Consenso Comercial y Operativo)
DELIVERY_FEE_BASE = Decimal("5.00")
DELIVERY_FREE_THRESHOLD = Decimal("50.00")  # Beneficio comercial acordado para clientes
DEFAULT_ETA_MINUTES = 25
MAX_ACTIVE_ORDERS_PER_RIDER = 3  # Capacidad operativa ampliada para motorizados
