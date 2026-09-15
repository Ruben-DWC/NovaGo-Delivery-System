from django.contrib import admin
from .models import UbicacionTracking, RutaEntrega

@admin.register(UbicacionTracking)
class UbicacionTrackingAdmin(admin.ModelAdmin):
    pass

@admin.register(RutaEntrega)
class RutaEntregaAdmin(admin.ModelAdmin):
    pass
