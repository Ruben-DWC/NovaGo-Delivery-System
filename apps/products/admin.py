from django.contrib import admin
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    pass

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    pass
