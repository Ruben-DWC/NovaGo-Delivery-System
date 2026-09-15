from django import forms
from apps.payments.models import Pago


class CheckoutForm(forms.Form):
    TIPO_FACTURACION_CHOICES = [
        ('boleta_simple', 'Boleta Simple'),
        ('boleta_dni', 'Boleta con DNI'),
        ('factura', 'Factura'),
    ]
    
    TIPO_POS_CHOICES = [
        ('pos_visa', 'POS Visa'),
        ('pos_mastercard', 'POS Mastercard'),
    ]
    
    # Campos básicos
    direccion_entrega = forms.CharField(
        label="Direccion de entrega",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
    telefono_contacto = forms.CharField(
        label="Telefono de contacto",
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    metodo_pago = forms.ChoiceField(
        label="Metodo de pago",
        choices=Pago.METODO_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "metodo_pago_select"}),
    )
    
    # Campos dinámicos según método de pago
    # Para Efectivo
    monto_efectivo = forms.DecimalField(
        label="¿Cuanto pagaría en efectivo?",
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "S/. 0.00", "step": "0.01"}),
    )
    
    # Para Tarjeta de Crédito/Débito
    numero_tarjeta = forms.CharField(
        label="Número de Tarjeta",
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "XXXX XXXX XXXX XXXX", "data-card-field": "true"}),
    )
    mes_vencimiento = forms.CharField(
        label="Mes/Año (MM/YY)",
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "MM/YY"}),
    )
    cvv = forms.CharField(
        label="CVV",
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "000", "maxlength": "4"}),
    )
    
    # Para Yape / Plin
    numero_celular = forms.CharField(
        label="Número de Celular Perú",
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "9XXXXXXXX"}),
    )
    
    # Para Pago Contra Entrega
    tipo_pos = forms.ChoiceField(
        label="Tipo de POS",
        choices=TIPO_POS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    
    # Facturación
    tipo_facturacion = forms.ChoiceField(
        label="Tipo de Facturación",
        choices=TIPO_FACTURACION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    
    # Checkboxes adicionales
    acepta_terminos = forms.BooleanField(
        label="Acepto los términos y condiciones",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    recibir_promociones = forms.BooleanField(
        label="Quisiera recibir promociones y descuentos",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    
    # Campos opcionales
    referencia = forms.CharField(
        label="Referencia de pago",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    notas = forms.CharField(
        label="Notas",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        required=False,
    )
