"""
Pruebas de Seguridad y Control de Acceso Basado en Roles (RBAC).
Verifica que las rutas canónicas /portal/* protejan los recursos de usuarios no autorizados.
Autor: Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe)
"""
from django.test import TestCase, Client

class SecurityRBACTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthenticated_portal_redirects(self):
        """Un usuario anónimo que intente entrar a /portal/ debe ser redirigido a login."""
        response = self.client.get('/portal/', follow=False)
        self.assertIn(response.status_code, (301, 302))
        self.assertIn('/users/login/', response.url)

    def test_home_page_renders_successfully(self):
        """Verifica que la página principal cargue con status 200."""
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"NovaGo" in response.content or b"novago" in response.content.lower())
