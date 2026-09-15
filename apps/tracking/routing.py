from django.urls import path

from apps.tracking.consumers import MotorizadoTrackingConsumer, OrderStatusConsumer, OrderTrackingConsumer


websocket_urlpatterns = [
    path('ws/tracking/motorizado/', MotorizadoTrackingConsumer.as_asgi()),
    path('ws/orders/<int:pedido_id>/status/', OrderStatusConsumer.as_asgi()),
    path('ws/tracking/order/<int:pedido_id>/', OrderTrackingConsumer.as_asgi()),
]
