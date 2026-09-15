from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('carrito/', views.CartView.as_view(), name='cart'),
    path('carrito/agregar/<int:producto_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('carrito/actualizar/<int:item_id>/', views.UpdateCartView.as_view(), name='update_cart'),
    path('carrito/eliminar/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    path('pedidos/', views.OrderListView.as_view(), name='order_list'),
    path('pedido/<int:pedido_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Admin Dashboard
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/reasignar/', views.AdminAsignarPedidoView.as_view(), name='admin_reasignar'),
    path('admin/asignacion-automatica/', views.AdminAsignacionAutomaticaView.as_view(), name='admin_asignacion_automatica'),
]
