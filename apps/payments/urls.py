from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pago/<str:numero_pedido>/', views.PaymentProcessView.as_view(), name='payment_process'),
    path('pago/confirmar/<str:codigo_pago>/', views.PaymentConfirmView.as_view(), name='payment_confirm'),
    path('pago/exitoso/<str:codigo_pago>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('pago/fallido/<str:codigo_pago>/', views.PaymentFailureView.as_view(), name='payment_failure'),
]
