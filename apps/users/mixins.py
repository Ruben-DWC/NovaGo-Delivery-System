from django.contrib import messages # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from django.shortcuts import redirect # type: ignore


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = tuple()
    allow_staff = False
    redirect_url = 'home'
    denied_message = 'No tienes permisos para acceder a esta sección.'

    def dispatch(self, request, *args, **kwargs):
        user_role = getattr(request.user, 'role', '')
        role_allowed = user_role in self.allowed_roles
        staff_allowed = self.allow_staff and (request.user.is_staff or request.user.is_superuser)

        if not (role_allowed or staff_allowed):
            messages.error(request, self.denied_message)
            return redirect(self.redirect_url)

        return super().dispatch(request, *args, **kwargs)


class ClientRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('cliente',)
    allow_staff = False
    denied_message = 'Acceso restringido al portal de cliente.'


class MotorizadoRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('motorizado', 'admin')
    allow_staff = True
    denied_message = 'Acceso restringido al portal de motorizado.'


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('admin',)
    allow_staff = True
    denied_message = 'Acceso restringido al portal administrativo.'
