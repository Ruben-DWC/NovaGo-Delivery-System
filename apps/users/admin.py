from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, PerfilMotorizado


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo User."""
    
    list_display = ('username', 'email', 'rol_display', 'telefono', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'telefono', 'nombre_completo')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'telefono', 'nombre_completo', 'direccion', 'avatar')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'telefono', 'nombre_completo', 'email')
        }),
    )
    
    def rol_display(self, obj):
        """Muestra el rol con color."""
        colors = {
            'cliente': '#10B981',
            'motorizado': '#F59E0B',
            'admin': '#DC2626'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.role, '#6B7280'),
            obj.get_role_display()
        )
    rol_display.short_description = 'Rol'


@admin.register(PerfilMotorizado)
class PerfilMotorizadoAdmin(admin.ModelAdmin):
    """Admin para perfiles de motorizados."""
    
    list_display = ('usuario', 'tipo_vehiculo', 'placa_vehiculo', 'calificacion', 'entregas_completadas', 'disponible')
    list_filter = ('disponible', 'tipo_vehiculo')
    search_fields = ('usuario__username', 'usuario__nombre_completo', 'placa_vehiculo', 'licencia')
    readonly_fields = ('entregas_completadas',)
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información del Vehículo', {
            'fields': ('tipo_vehiculo', 'placa_vehiculo', 'licencia')
        }),
        ('Estado y Estadísticas', {
            'fields': ('disponible', 'calificacion', 'entregas_completadas')
        }),
    )
