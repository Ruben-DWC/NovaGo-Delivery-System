from django.contrib import admin
from django.utils.html import format_html
from .models import Pedido, ItemPedido


class ItemPedidoInline(admin.TabularInline):
    """Inline para items del pedido."""
    model = ItemPedido
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Admin para pedidos."""
    
    list_display = ('numero_pedido', 'cliente', 'motorizado', 'estado_display', 'total_display', 'fecha_pedido')
    list_filter = ('estado', 'fecha_pedido')
    search_fields = ('numero_pedido', 'cliente__username', 'direccion_entrega')
    readonly_fields = ('numero_pedido', 'subtotal', 'costo_envio', 'total')
    inlines = [ItemPedidoInline]
    
    def estado_display(self, obj):
        colors = {
            'pendiente': '#F59E0B',
            'confirmado': '#3B82F6',
            'en_preparacion': '#8B5CF6',
            'en_camino': '#06B6D4',
            'entregado': '#10B981',
            'cancelado': '#EF4444'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.estado, '#6B7280'),
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def total_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #DC2626;">S/ {:.2f}</span>', obj.total)
    total_display.short_description = 'Total'


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    """Admin para items de pedidos."""
    
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('pedido__numero_pedido', 'producto__nombre')
    readonly_fields = ('subtotal',)
