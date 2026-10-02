"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from apps.users import views as user_views
from apps.tracking import views as tracking_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/home/')),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Rutas Canónicas de Portales (Consolidación de Arquitectura de Rutas Avance 2)
    path('portal/', user_views.PortalDispatcherRedirectView.as_view(), name='portal_root'),
    path('portal/admin/', user_views.AdminDashboardView.as_view(), name='canonical_portal_admin'),
    path('portal/cliente/', user_views.ClientPortalView.as_view(), name='canonical_portal_cliente'),
    path('portal/motorizado/', tracking_views.MotorizadoDashboardView.as_view(), name='canonical_portal_motorizado'),
    
    path('users/', include('apps.users.urls')),
    path('products/', include('apps.products.urls')),
    path('orders/', include('apps.orders.urls')),
    path('tracking/', include('apps.tracking.urls')),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

