from io import BytesIO

import pytest
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import resolve, reverse
from PIL import Image

User = get_user_model()


def _create_test_image_file(name="avatar.png"):
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color=(255, 106, 61)).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.django_db
class TestAllauthConfiguration:
    def test_settings_allauth_configured(self):
        assert settings.SITE_ID == 1
        assert "django.contrib.sites" in settings.INSTALLED_APPS
        assert "allauth" in settings.INSTALLED_APPS
        assert "allauth.account" in settings.INSTALLED_APPS
        assert "allauth.socialaccount" in settings.INSTALLED_APPS
        assert "allauth.socialaccount.providers.google" in settings.INSTALLED_APPS
        assert "allauth.socialaccount.providers.github" in settings.INSTALLED_APPS
        assert "allauth.account.middleware.AccountMiddleware" in settings.MIDDLEWARE
        assert (
            "allauth.account.auth_backends.AuthenticationBackend"
            in settings.AUTHENTICATION_BACKENDS
        )
        assert settings.SOCIALACCOUNT_LOGIN_ON_GET is True
        assert settings.ACCOUNT_EMAIL_VERIFICATION == "none"
        assert settings.LOGIN_REDIRECT_URL == "/"
        assert settings.LOGOUT_REDIRECT_URL == "/"

    def test_socialaccount_providers_present_without_crash(self):
        providers = settings.SOCIALACCOUNT_PROVIDERS
        assert "google" in providers
        assert "github" in providers
        assert "APP" in providers["google"]
        assert "APP" in providers["github"]
        assert "client_id" in providers["google"]["APP"]
        assert "secret" in providers["google"]["APP"]
        assert "client_id" in providers["github"]["APP"]
        assert "secret" in providers["github"]["APP"]

    def test_allauth_urls_resolve(self):
        assert resolve("/accounts/login/")
        assert resolve("/accounts/google/login/")
        assert resolve("/accounts/github/login/")
        assert resolve("/accounts/google/login/callback/")
        assert resolve("/accounts/github/login/callback/")


@pytest.mark.django_db
class TestOAuthTemplatesAndButtons:
    def test_login_page_renders_oauth_buttons(self, client):
        response = client.get(reverse("users:login"))
        assert response.status_code == 200
        html = response.content.decode("utf-8")
        assert "Continuar con Google" in html
        assert "Continuar con GitHub" in html
        assert "/accounts/google/login/" in html
        assert "/accounts/github/login/" in html

    def test_register_page_renders_oauth_buttons(self, client):
        response = client.get(reverse("users:register"))
        assert response.status_code == 200
        html = response.content.decode("utf-8")
        assert "Continuar con Google" in html
        assert "Continuar con GitHub" in html
        assert "/accounts/google/login/" in html
        assert "/accounts/github/login/" in html


@pytest.mark.django_db
class TestOAuthUserRoleAndAvatar:
    def test_new_oauth_user_defaults_to_cliente_role(self):
        user = User.objects.create_user(
            username="oauth_google_user",
            email="oauth@novago.pe",
        )
        assert user.role == "cliente"
        assert user.es_cliente() is True

    def test_avatar_url_priority_3_static_fallback(self):
        user = User.objects.create_user(username="avatar_default_user")
        assert user.avatar_url.endswith("images/default-avatar.svg")

    def test_avatar_url_priority_2_google_picture(self):
        user = User.objects.create_user(username="avatar_google_user")
        google_pic = "https://lh3.googleusercontent.com/a/test-avatar"
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="google-uid-123",
            extra_data={"picture": google_pic},
        )
        assert user.avatar_url == google_pic

    def test_avatar_url_priority_2_github_avatar_url(self):
        user = User.objects.create_user(username="avatar_github_user")
        github_pic = "https://avatars.githubusercontent.com/u/99999?v=4"
        SocialAccount.objects.create(
            user=user,
            provider="github",
            uid="github-uid-456",
            extra_data={"avatar_url": github_pic},
        )
        assert user.avatar_url == github_pic

    def test_avatar_url_priority_1_local_foto_perfil_overrides_social(self, tmp_path, settings):
        settings.MEDIA_ROOT = tmp_path
        user = User.objects.create_user(
            username="avatar_local_user",
            foto_perfil=_create_test_image_file("custom.png"),
        )
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="google-uid-789",
            extra_data={"picture": "https://lh3.googleusercontent.com/a/ignored"},
        )
        assert user.avatar_url == user.foto_perfil.url
        assert "custom" in user.avatar_url


@pytest.mark.django_db
class TestWelcomeEmailNotification:
    def test_user_signed_up_signal_sends_welcome_email(self, mailoutbox, rf):
        from allauth.account.signals import user_signed_up

        user = User.objects.create_user(
            username="subiendovideos903",
            email="subiendovideos903@gmail.com",
            first_name="Subiendo",
            last_name="Videos",
        )
        request = rf.get("/")
        user_signed_up.send(sender=User, request=request, user=user)

        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert "subiendovideos903@gmail.com" in msg.to
        assert "Bienvenido a NovaGo" in msg.subject
        assert any("text/html" in alt[1] for alt in msg.alternatives)

    def test_smtp_error_does_not_crash_welcome_email(self, monkeypatch):
        from apps.users.emails import enviar_correo_bienvenida

        def _broken_send(*args, **kwargs):
            raise ConnectionRefusedError("SMTP disabled")

        monkeypatch.setattr("django.core.mail.EmailMultiAlternatives.send", _broken_send)
        user = User.objects.create_user(
            username="smtp_fail_user",
            email="smtpfail@example.com",
        )
        assert enviar_correo_bienvenida(user, proveedor="google") is False
