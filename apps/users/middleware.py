"""
Middleware de Control de Acceso Basado en Roles (RBAC) para NovaGo Delivery.
Garantiza aislamiento estricto entre portales:
- /portal/admin/ -> Solo administradores y personal de staff
- /portal/motorizado/ -> Solo motorizados y administradores
- /portal/cliente/ -> Solo clientes y administradores
- /portal/ -> Redirección inteligente al portal correspondiente
"""
from django.shortcuts import redirect, render

FORBIDDEN_TEMPLATE = '403.html'

PORTAL_RULES = (
    (
        ('/portal/admin/', '/users/portal/admin/'),
        ('admin',),
        'Administrador',
        'Acceso restringido exclusivamente a supervisores y administradores de NovaGo Delivery.',
    ),
    (
        ('/portal/motorizado/', '/tracking/portal/motorizado/'),
        ('motorizado', 'admin'),
        'Motorizado / Repartidor',
        'Acceso exclusivo para el personal de despacho vehicular de NovaGo Delivery.',
    ),
    (
        ('/portal/cliente/', '/users/portal/cliente/'),
        ('cliente', 'admin'),
        'Cliente',
        'Acceso exclusivo al portal de compras y gestión para clientes de NovaGo Delivery.',
    ),
)


class RoleBasedAccessMiddleware:
    """
    Interviene en cada petición HTTP hacia rutas de portales (/portal/*)
    verificando la autenticación y los privilegios RBAC según el modelo Usuario.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Dispatcher central inteligente: /portal/
        if path in ('/portal/', '/portal'):
            return self._handle_portal_root(request)

        for prefixes, allowed_roles, role_name, denial_reason in PORTAL_RULES:
            if path.startswith(prefixes):
                if not request.user.is_authenticated:
                    return redirect(f"/users/login/?next={path}")

                user_role = getattr(request.user, 'role', '')
                is_authorized = (
                    user_role in allowed_roles
                    or request.user.is_staff
                    or request.user.is_superuser
                )
                if not is_authorized:
                    return render(
                        request,
                        FORBIDDEN_TEMPLATE,
                        {
                            'required_role': role_name,
                            'current_role': user_role or 'Sin rol asignado',
                            'reason': denial_reason,
                        },
                        status=403,
                    )

        return self.get_response(request)

    def _handle_portal_root(self, request):
        if not request.user.is_authenticated:
            return redirect(f"/users/login/?next={request.path}")
        role = getattr(request.user, 'role', '')
        if role == 'admin' or request.user.is_staff or request.user.is_superuser:
            return redirect('/portal/admin/')
        elif role == 'motorizado':
            return redirect('/portal/motorizado/')
        return redirect('/portal/cliente/')
