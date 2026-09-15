from django.urls import path # type: ignore
from . import views

app_name = 'tracking'

urlpatterns = [
    path('motorizado/', views.MotorizadoDashboardView.as_view(), name='motorizado_dashboard'),
    path('portal/motorizado/', views.MotorizadoDashboardView.as_view(), name='portal_motorizado'),
    path('portal/motorizado/historial/', views.MotorizadoHistoryView.as_view(), name='motorizado_historial'),
    path('portal/motorizado/pedido/<int:pedido_id>/', views.MotorizadoOrderDetailView.as_view(), name='motorizado_pedido_detalle'),
    path('portal/motorizado/rastreo/<int:pedido_id>/', views.TrackOrderView.as_view(), name='motorizado_rastreo_pedido'),
    path('motorizado/dashboard/', views.MotorizadoDashboardView.as_view(), name='motorizado_dashboard_portal'),
    path('rastrear/<int:pedido_id>/', views.TrackOrderView.as_view(), name='track_order'),
    
    path('api/actualizar-ubicacion/', views.UpdateLocationView.as_view(), name='update_location'),
    path('api/mapa-motorizado/', views.MotorizadoMapDataView.as_view(), name='motorizado_map_data'),
    path('api/pedido/<int:pedido_id>/snapshot/', views.OrderTrackingSnapshotView.as_view(), name='order_tracking_snapshot'),
    
    # Gestión de jornada
    path('api/iniciar-jornada/', views.IniciarJornadaView.as_view(), name='iniciar_jornada'),
    path('api/finalizar-jornada/', views.FinalizarJornadaView.as_view(), name='finalizar_jornada'),
    path('api/marcar-en-preparacion/', views.MarcarEnPreparacionView.as_view(), name='marcar_en_preparacion'),
    path('api/marcar-en-camino/', views.MarcarEnCaminoView.as_view(), name='marcar_en_camino'),
    path('api/marcar-entregado/', views.MarcarEntregadoView.as_view(), name='marcar_entregado'),
]
