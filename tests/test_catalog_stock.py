"""
Pruebas de Catálogo, Filtros Dinámicos e Integridad de Inventario.
Verifica la disponibilidad de productos y la consulta de catálogo.
Autor: Conislla Lavado Cesar Jesus (umaten / u23264049@utp.edu.pe)
"""
from decimal import Decimal
from django.test import TestCase, Client
from apps.products.models import Producto, Categoria

class CatalogStockTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_catalog_view_accessible(self):
        """Verifica que la vista del catálogo de productos responda correctamente."""
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)

    def test_create_and_query_product(self):
        """Verifica la persistencia en base de datos y cálculo de stock."""
        categoria = Categoria.objects.create(nombre="Bebidas", descripcion="Bebidas frias")
        producto = Producto.objects.create(
            nombre="Agua Mineral 1L Test",
            descripcion="Agua sin gas 1 litro",
            categoria=categoria,
            precio=Decimal("3.50"),
            stock=25
        )
        self.assertIsNotNone(producto.id)
        self.assertEqual(producto.stock, 25)
        self.assertTrue(producto.activo)
        self.assertGreater(producto.stock, 0)
