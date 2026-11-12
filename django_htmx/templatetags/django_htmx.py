from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def django_htmx_script() -> str:
    return mark_safe('<script defer src="https://unpkg.com/htmx.org@2.0.4"></script>')

