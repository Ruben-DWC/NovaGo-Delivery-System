# Changelog

## [1.1.0-final] - 2026-11-27
- Rediseño integral Quick Commerce UI/UX (Home, Navbar con búsqueda global y cobertura, Catálogo con filtros y badges, Detalle de producto, Carrito con stepper táctil 44px y barra sticky móvil, Checkout, Confirmación y Tracking dinámico).
- Corrección de cálculo de cobertura por distrito (normalización decimal `es-pe` en `location_modal.html`) y validación de estado en pedidos cancelados / pago en efectivo.
- Endurecimiento de seguridad en producción (PythonAnywhere): `SECRET_KEY` migrada a `.env`, `CSRF_TRUSTED_ORIGINS` ampliado para `https://rubendwc.pythonanywhere.com`, permisos `chmod 600`, `APP_VERSION = "1.1.0-final"` en `/health/` y fallback de imagen en `Product.imagen_url`.
- Sincronización dual completa entre GitHub (`origin`) y GitLab (`gitlab`) en ramas `main`, `develop` y tag `v1.1.0-final`.

## [1.0.0-final] - 2026-11-24
- Integración de OAuth 2.0 (Google y GitHub) con `django-allauth`, correo de bienvenida y Asistente IA 3D Nova (`django-agentic`).
- Cierre de incidencias #7 y #9; suite automatizada ampliada a 68 pruebas aprobadas.

## [0.3.0-apf3] - 2026-11-05
- Contenerización multi-stage Docker + PostgreSQL 16 Alpine, endpoint `/health/` y pipelines CI/CD en GitHub Actions.
- Cierre de incidencias del Sprint 3: #5, #8 y #10.