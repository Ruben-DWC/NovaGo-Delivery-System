from django.contrib import admin
from django.utils.html import format_html
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Admin para pagos."""
    
    list_display = ('codigo_pago', 'pedido', 'metodo_display', 'monto_display', 'estado_display', 'fecha_pago')
    list_filter = ('estado', 'metodo_pago', 'fecha_pago')
    search_fields = ('codigo_pago', 'pedido__numero_pedido', 'referencia_transaccion')
    readonly_fields = ('codigo_pago', 'fecha_pago')
    
    def metodo_display(self, obj):
        iconos = {
            'efectivo': '💵',
            'transferencia': '🏦',
            'tarjeta': '💳',
            'yape': '📱',
            'plin': '📲'
        }
        return format_html('{} {}', iconos.get(obj.metodo_pago, '💰'), obj.get_metodo_pago_display())
    metodo_display.short_description = 'Método'
    
    def monto_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #DC2626;">S/ {:.2f}</span>', obj.monto)
    monto_display.short_description = 'Monto'
    
    def estado_display(self, obj):
        colors = {
            'pendiente': '#F59E0B',
            'procesando': '#3B82F6',
            'confirmado': '#10B981',
            'rechazado': '#EF4444',
            'reembolsado': '#6B7280'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.estado, '#6B7280'),
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
