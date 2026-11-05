"""
Pruebas Automatizadas para el Endpoint de Diagnóstico y Health Check.
Verifica que el servicio esté operativo y la base de datos responda.
Autor: Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe)
"""
from django.test import TestCase, Client

class HealthCheckTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_healthcheck_endpoint_status(self):
        """Verifica que /health/ retorne HTTP 200 y status healthy."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "NovaGo Delivery System")
        self.assertIn("version", data)
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["checks"]["database"], "pass")
        self.assertEqual(data["checks"]["routing"], "pass")

    def test_healthcheck_latency_metric(self):
        """Verifica que la telemetría reporte latencia menor a 1000ms."""
        response = self.client.get('/health/')
        data = response.json()
        self.assertIn("latency_ms", data)
        self.assertLess(float(data["latency_ms"]), 1000.0)
