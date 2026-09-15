from django.urls import path # type: ignore
from django.views.generic.base import RedirectView # type: ignore
from . import views

app_name = 'users'

urlpatterns = [
    # Landing page principal
    path('home/', views.HomeView.as_view(), name='home'),
    
    # Autenticación
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/exitoso/', views.LoginSuccessView.as_view(), name='login_success'),
    path('registro/', views.RegisterView.as_view(), name='register'),
    path('registro/exitoso/', views.RegisterSuccessView.as_view(), name='register_success'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Perfiles
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('perfil/editar/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # Dashboard según rol
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('portal/cliente/', views.ClientPortalView.as_view(), name='portal_cliente'),
    path('portal/cliente/catalogo/', views.ClientCatalogoView.as_view(), name='portal_cliente_catalogo'),
    path('portal/cliente/catalogo/categoria/<int:categoria_id>/', views.ClientCatalogoView.as_view(), name='portal_cliente_catalogo_categoria'),
    path('portal/cliente/catalogo/<int:pk>/', views.ClientProductoDetailView.as_view(), name='portal_cliente_producto'),
    path('portal/cliente/carrito/', views.ClientCarritoView.as_view(), name='portal_cliente_carrito'),
    path('portal/cliente/pedidos/', views.ClientPedidosView.as_view(), name='portal_cliente_pedidos'),
    path('portal/cliente/pedidos/<int:pedido_id>/', views.ClientPedidoDetailView.as_view(), name='portal_cliente_pedido_detalle'),
    path('portal/cliente/pago/', views.ClientPaymentGatewayView.as_view(), name='portal_cliente_pago'),
    path('portal/cliente/confirmacion/<int:pedido_id>/', views.ClientOrderConfirmationView.as_view(), name='portal_cliente_confirmacion'),
    path('portal/cliente/confirmacion/<int:pedido_id>/estado/', views.ClientOrderProgressApiView.as_view(), name='portal_cliente_confirmacion_estado'),
    path('portal/cliente/perfil/', views.ClientPerfilView.as_view(), name='portal_cliente_perfil'),
    path('portal/motorizado/perfil/', views.MotorizadoPerfilView.as_view(), name='portal_motorizado_perfil'),
    path('portal/cliente/rastreo/', views.ClientTrackingHubView.as_view(), name='portal_cliente_rastreo'),
    path('portal/cliente/rastreo/<int:pedido_id>/', views.ClientTrackingOrderView.as_view(), name='portal_cliente_rastreo_pedido'),
    path('portal/motorizado/', RedirectView.as_view(pattern_name='tracking:portal_motorizado', permanent=False), name='portal_motorizado'),
    path('portal/admin/', views.AdminDashboardView.as_view(), name='portal_admin'),
    path('portal/admin/reportes/', views.AdminReportsView.as_view(), name='admin_reports'),
    path('portal/admin/ingresos/', views.AdminIncomeView.as_view(), name='admin_income'),
    path('portal/admin/performance/', views.AdminPerformanceView.as_view(), name='admin_performance'),
    path('portal/admin/pedidos/', views.AdminOrdersManageView.as_view(), name='admin_orders'),
    path('portal/admin/pedidos/acciones-masivas/', views.AdminOrdersBulkActionView.as_view(), name='admin_orders_bulk_action'),
    path('portal/admin/export/dashboard/', views.AdminDashboardExportView.as_view(), name='admin_export_dashboard'),
    path('portal/admin/export/pedidos/', views.AdminOrdersExportView.as_view(), name='admin_export_orders'),
    path('portal/admin/export/usuarios/', views.AdminUsersExportView.as_view(), name='admin_export_users'),
    path('portal/admin/export/pagos/', views.AdminPaymentsExportView.as_view(), name='admin_export_payments'),
    path('portal/admin/export/bitacora/', views.AdminAuditLogExportView.as_view(), name='admin_export_audit_logs'),
    path('portal/admin/productos/', views.AdminProductListView.as_view(), name='admin_products'),
    path('portal/admin/productos/nuevo/', views.AdminProductCreateView.as_view(), name='admin_product_create'),
    path('portal/admin/productos/<int:pk>/editar/', views.AdminProductUpdateView.as_view(), name='admin_product_update'),
    path('portal/admin/productos/<int:pk>/eliminar/', views.AdminProductDeleteView.as_view(), name='admin_product_delete'),
    path('portal/admin/categorias/', views.AdminCategoryListView.as_view(), name='admin_categories'),
    path('portal/admin/categorias/nueva/', views.AdminCategoryCreateView.as_view(), name='admin_category_create'),
    path('portal/admin/categorias/<int:pk>/editar/', views.AdminCategoryUpdateView.as_view(), name='admin_category_update'),
    path('portal/admin/categorias/<int:pk>/eliminar/', views.AdminCategoryDeleteView.as_view(), name='admin_category_delete'),
    path('portal/admin/usuarios/', views.AdminUserListView.as_view(), name='admin_users'),
    path('portal/admin/usuarios/acciones-masivas/', views.AdminUsersBulkActionView.as_view(), name='admin_users_bulk_action'),
    path('portal/admin/clientes/', views.AdminClientListView.as_view(), name='admin_clients'),
    path('portal/admin/empleados/', views.AdminEmployeeListView.as_view(), name='admin_employees'),
    path('portal/admin/roles/', views.AdminRolesManageView.as_view(), name='admin_roles'),
    path('portal/admin/usuarios/<int:pk>/editar/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('portal/admin/pagos/', views.AdminPaymentsManageView.as_view(), name='admin_payments'),
    path('portal/admin/pagos/acciones-masivas/', views.AdminPaymentsBulkActionView.as_view(), name='admin_payments_bulk_action'),
    path('portal/admin/bitacora/', views.AdminAuditLogListView.as_view(), name='admin_audit_logs'),

    # Alias compatibles (legacy)
    path('client/portal/', views.ClientPortalView.as_view(), name='client_portal'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]
