from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .emails import enviar_correo_bienvenida


@receiver(user_signed_up)
def on_allauth_user_signed_up(sender, request, user, **kwargs):
    """Envía un correo de bienvenida cuando un usuario se registra vía OAuth 2.0 o allauth."""
    sociallogin = kwargs.get('sociallogin')
    proveedor = sociallogin.account.provider if sociallogin else 'NovaGo'
    enviar_correo_bienvenida(user, proveedor=proveedor)
