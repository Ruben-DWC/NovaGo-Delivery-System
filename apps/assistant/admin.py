from django.contrib import admin

from .models import ConversacionLog


@admin.register(ConversacionLog)
class ConversacionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'session_key', 'proveedor', 'latencia_ms', 'tiene_error', 'fecha')
    list_filter = ('proveedor', 'fecha')
    search_fields = ('usuario__username', 'session_key', 'mensaje', 'respuesta', 'error')
    ordering = ('-fecha',)
    readonly_fields = (
        'usuario',
        'session_key',
        'mensaje',
        'respuesta',
        'herramientas_usadas',
        'proveedor',
        'latencia_ms',
        'error',
        'fecha',
    )

    @admin.display(boolean=True, description='Error')
    def tiene_error(self, obj):
        return bool(obj.error)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
