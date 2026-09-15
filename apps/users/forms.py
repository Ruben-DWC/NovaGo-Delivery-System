import base64
import binascii
import uuid
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from apps.products.models import Producto, Categoria


User = get_user_model()


class ClientRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not username:
            return username

        existing = User.objects.filter(username=username).first()
        if existing and existing.is_active:
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email

        existing = User.objects.filter(email=email).first()
        if existing and existing.is_active:
            raise forms.ValidationError("Este correo ya está registrado.")

        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        validate_password(password2)
        return password2

    def save(self):
        self.was_reactivated = False
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]

        existing = User.objects.filter(username=username).first()

        if existing and not existing.is_active:
            self.was_reactivated = True
            existing.email = email
            existing.role = "cliente"
            existing.is_active = True
            existing.set_password(password)
            existing.save()
            return existing

        user = User(username=username)
        user.email = email
        user.role = "cliente"
        user.is_active = True
        user.set_password(password)
        user.save()
        return user


class UserProfileForm(forms.ModelForm):
    avatar_cropped_data = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'bio',
            'foto_perfil',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Cuéntanos un poco sobre ti...'}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        existing = User.objects.filter(email=email).exclude(pk=self.instance.pk).first()
        if existing:
            raise forms.ValidationError('Este correo ya está en uso por otro usuario.')

        return email

    def clean_avatar_cropped_data(self):
        raw_data = (self.cleaned_data.get('avatar_cropped_data') or '').strip()
        if not raw_data:
            return ''

        if ';base64,' not in raw_data or not raw_data.startswith('data:image/'):
            raise forms.ValidationError('Formato de imagen recortada inválido.')

        mime_type = raw_data.split(';base64,', 1)[0].replace('data:', '')
        supported_mimes = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}
        if mime_type not in supported_mimes:
            raise forms.ValidationError('Solo se permiten imágenes JPG, PNG o WEBP para el recorte.')

        encoded = raw_data.split(';base64,', 1)[1]
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise forms.ValidationError('No se pudo procesar la imagen recortada.') from exc

        if len(decoded) > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen recortada supera el límite de 5MB.')

        return raw_data

    def save(self, commit=True):
        user = super().save(commit=False)
        cropped_data = self.cleaned_data.get('avatar_cropped_data')
        if cropped_data:
            user.foto_perfil = self._decode_cropped_image(cropped_data)

        if commit:
            user.save()
            self.save_m2m()
        return user

    def _decode_cropped_image(self, image_data):
        header, encoded = image_data.split(';base64,', 1)
        mime = header.replace('data:', '')
        extension_by_mime = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
        }
        extension = extension_by_mime.get(mime)
        if not extension:
            raise forms.ValidationError('Formato de imagen no soportado para recorte.')

        decoded = base64.b64decode(encoded)
        file_name = f"perfil_{uuid.uuid4().hex}.{extension}"
        return ContentFile(decoded, name=file_name)


class AdminProductForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'descripcion',
            'categoria',
            'precio',
            'stock',
            'imagen',
            'destacado',
            'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminCategoryForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'icono', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-box'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminUserManageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'telefono', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }