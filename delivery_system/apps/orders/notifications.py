"""
Servicio de notificaciones operativas para el módulo de pedidos NovaGo.
Soporte de alertas SMS / WhatsApp y webhooks para cambios de estado de entrega.
"""
import logging

logger = logging.getLogger(__name__)


class OrderNotificationService:
    @staticmethod
    def notify_order_status_change(order_id: int, old_status: str, new_status: str, customer_phone: str) -> bool:
        """
        Envía notificación al cliente sobre la actualización de su encomienda.
        """
        message = f"NovaGo Delivery: Su pedido #{order_id} cambió de {old_status} a {new_status}."
        logger.info("Notificando pedido #%s a %s: %s", order_id, customer_phone, message)
        # Mock de integración con pasarela de mensajería
        return True

    @staticmethod
    def notify_delivery_assigned(order_id: int, rider_name: str, rider_phone: str) -> bool:
        """
        Notifica asignación de motorizado al despacho.
        """
        message = f"NovaGo Delivery: Motorizado {rider_name} asignado al pedido #{order_id}. Contacto: {rider_phone}"
        logger.info("Asignación de despacho #%s: %s", order_id, message)
        return True
