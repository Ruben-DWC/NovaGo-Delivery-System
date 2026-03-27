from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Admin para categorías de productos."""
    
    list_display = ('nombre', 'slug', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Admin para productos."""
    
    list_display = ('nombre', 'categoria', 'precio_display', 'stock', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    
    def precio_display(self, obj):
        """Muestra el precio formateado."""
        return format_html('<span style="font-weight: bold;">S/ {:.2f}</span>', obj.precio)
    precio_display.short_description = 'Precio'
