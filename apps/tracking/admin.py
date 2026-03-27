from django.contrib import admin
from django.utils.html import format_html
from .models import UbicacionTracking, RutaEntrega


@admin.register(UbicacionTracking)
class UbicacionTrackingAdmin(admin.ModelAdmin):
    """Admin para ubicaciones de tracking."""
    
    list_display = ('pedido', 'motorizado', 'coordenadas', 'timestamp', 'ver_mapa')
    list_filter = ('timestamp',)
    search_fields = ('pedido__numero_pedido', 'motorizado__username')
    readonly_fields = ('timestamp',)
    
    def coordenadas(self, obj):
        return format_html(
            '<code style="background-color: #F3F4F6; padding: 4px 8px;">{:.6f}, {:.6f}</code>',
            obj.latitud, obj.longitud
        )
    coordenadas.short_description = 'GPS'
    
    def ver_mapa(self, obj):
        return format_html(
            '<a href="https://www.google.com/maps?q={},{}" target="_blank" '
            'style="background-color: #10B981; color: white; padding: 4px 12px; border-radius: 6px; text-decoration: none;">🗺️ Mapa</a>',
            obj.latitud, obj.longitud
        )
    ver_mapa.short_description = 'Mapa'


@admin.register(RutaEntrega)
class RutaEntregaAdmin(admin.ModelAdmin):
    """Admin para rutas de entrega."""
    
    list_display = ('pedido', 'motorizado', 'estado_display', 'distancia_km', 'tiempo_total', 'fecha_inicio')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('pedido__numero_pedido', 'motorizado__username')
    readonly_fields = ('tiempo_total',)
    
    def estado_display(self, obj):
        colors = {
            'planificada': '#F59E0B',
            'en_curso': '#3B82F6',
            'completada': '#10B981',
            'cancelada': '#EF4444'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.estado, '#6B7280'),
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
