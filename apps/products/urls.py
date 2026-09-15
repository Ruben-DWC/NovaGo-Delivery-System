from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('categoria/<int:categoria_id>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    path('buscar/', views.ProductSearchView.as_view(), name='product_search'),
]
