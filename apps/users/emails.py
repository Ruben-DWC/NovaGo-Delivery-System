import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def enviar_correo_bienvenida(user, proveedor: Optional[str] = None) -> bool:
    """
    Envía un correo de bienvenida/registro exitoso al usuario.
    Si falla el servidor SMTP o el usuario no tiene email, registra el aviso
    y retorna False sin interrumpir el flujo de autenticación.
    """
    email_destino = (getattr(user, 'email', '') or '').strip()
    if not email_destino:
        logger.info('Usuario %s sin correo electrónico; se omite correo de bienvenida.', getattr(user, 'username', ''))
        return False

    nombre = user.get_full_name().strip() or getattr(user, 'username', '') or 'Cliente'
    metodo = (proveedor or 'NovaGo').capitalize()
    asunto = f'¡Bienvenido a NovaGo Delivery System, {nombre}!'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NovaGo Delivery <no-reply@novago.pe>')

    contexto = {
        'nombre': nombre,
        'email': email_destino,
        'metodo_registro': metodo,
        'rol': getattr(user, 'role', 'cliente'),
        'app_url': getattr(settings, 'NOVAGO_PUBLIC_URL', 'http://127.0.0.1:8000/'),
    }

    try:
        html_body = render_to_string('emails/welcome_email.html', contexto)
        text_body = strip_tags(html_body)
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_body,
            from_email=from_email,
            to=[email_destino],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Correo de bienvenida enviado a %s vía %s.', email_destino, metodo)
        return True
    except Exception as exc:
        logger.warning('No se pudo enviar correo de bienvenida a %s: %s', email_destino, exc)
        return False
