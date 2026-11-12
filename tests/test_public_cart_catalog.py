"""
Pruebas de Catálogo Público, Carrito de Compras Global y Accesibilidad UI.
Verifica que usuarios anónimos y registrados puedan consultar el catálogo,
agregar productos al carrito, recibir feedback visual y acceder a /orders/carrito/.
Autores: Conislla Lavado Cesar Jesus (umaten) & Ruben Walter Vivas Jimenez (Ruben-DWC)
"""
from decimal import Decimal
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from apps.products.models import Producto, Categoria
from apps.orders.services import CartService
from apps.orders.context_processors import cart_context


class PublicCartCatalogTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nombre="Hamburguesas", descripcion="Hamburguesas artesanales")
        self.producto = Producto.objects.create(
            nombre="Burger Clásica NovaGo",
            descripcion="Carne artesanal de 180g con queso cheddar y vegetales",
            categoria=self.categoria,
            precio=Decimal("18.50"),
            stock=15,
            activo=True
        )

    def test_public_catalog_accessible(self):
        """El catálogo público debe ser accesible a cualquier visitante anónimo con código 200."""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Burger Clásica NovaGo")
        self.assertContains(response, "floating-cart-pill")
        self.assertContains(response, "Carrito")

    def test_public_cart_page_accessible(self):
        """La página del carrito /orders/carrito/ debe ser accesible sin autenticación previa."""
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tu Carrito")

    def test_cart_context_processor_empty(self):
        """El context processor global debe reportar 0 ítems cuando el carrito está vacío."""
        request = self.factory.get('/')
        request.session = self.client.session
        ctx = cart_context(request)
        self.assertEqual(ctx['cart_count'], 0)
        self.assertEqual(ctx['cart_total'], 0)

    def test_add_to_cart_standard_post(self):
        """Agregar producto mediante POST tradicional redirige y actualiza la sesión."""
        url = reverse('orders:add_to_cart', kwargs={'producto_id': self.producto.id})
        response = self.client.post(url, {'quantity': 2}, HTTP_REFERER=reverse('products:product_list'))
        self.assertEqual(response.status_code, 302)

        # Verificar sesión
        session = self.client.session
        cart = session.get(CartService.SESSION_KEY, {})
        self.assertEqual(cart.get(str(self.producto.id)), 2)

        # Verificar renderizado en la página del carrito
        cart_resp = self.client.get(reverse('orders:cart'))
        self.assertEqual(cart_resp.status_code, 200)
        self.assertContains(cart_resp, "Burger Clásica NovaGo")
        self.assertTrue("37,00" in cart_resp.content.decode() or "37.00" in cart_resp.content.decode())

    def test_add_to_cart_ajax(self):
        """Agregar producto mediante AJAX debe responder JSON con el nuevo total y contador."""
        url = reverse('orders:add_to_cart', kwargs={'producto_id': self.producto.id})
        response = self.client.post(
            url,
            {'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['cart_count'], 1)
        self.assertEqual(data['cart_subtotal'], 18.5)
        self.assertEqual(data['cart_total'], 23.5)  # 18.50 + 5.00 shipping

    def test_cart_context_processor_populated(self):
        """El context processor debe reflejar los totales una vez agregados productos."""
        url = reverse('orders:add_to_cart', kwargs={'producto_id': self.producto.id})
        self.client.post(url, {'quantity': 3})

        # Al consultar cualquier página pública, el navbar y el contexto tienen los datos
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cart_count'], 3)
        self.assertContains(response, "js-nav-cart-count")

    def test_cart_data_api_endpoint(self):
        """El endpoint público /orders/carrito/api/ debe responder JSON con la lista de items."""
        # Agregar producto primero
        self.client.post(reverse('orders:add_to_cart', kwargs={'producto_id': self.producto.id}), {'quantity': 2})

        response = self.client.get(reverse('orders:cart_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['nombre'], "Burger Clásica NovaGo")

    def test_cart_ajax_update_and_remove(self):
        """Actualizar y eliminar productos vía AJAX debe responder JSON actualizado."""
        # Agregar
        self.client.post(reverse('orders:add_to_cart', kwargs={'producto_id': self.producto.id}), {'quantity': 1})

        # Actualizar cantidad a 4
        update_url = reverse('orders:update_cart', kwargs={'item_id': self.producto.id})
        resp_update = self.client.post(
            update_url,
            {'quantity': 4},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(resp_update.status_code, 200)
        data_up = resp_update.json()
        self.assertEqual(data_up['cart_count'], 4)
        self.assertEqual(data_up['cart_subtotal'], 74.0)

        # Eliminar
        remove_url = reverse('orders:remove_from_cart', kwargs={'item_id': self.producto.id})
        resp_remove = self.client.post(
            remove_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(resp_remove.status_code, 200)
        data_rem = resp_remove.json()
        self.assertEqual(data_rem['cart_count'], 0)
        self.assertEqual(data_rem['items'], [])

    def test_public_tracking_lookup(self):
        """La página pública de rastreo /tracking/consulta/ debe responder 200 y permitir búsqueda."""
        response = self.client.get(reverse('tracking:public_lookup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Consulta el Estado de tu Entrega")

        # Búsqueda de pedido inexistente
        resp_not_found = self.client.get(reverse('tracking:public_lookup') + '?order_id=99999')
        self.assertEqual(resp_not_found.status_code, 200)
        self.assertContains(resp_not_found, "Pedido no encontrado")

    def test_public_pages_about_terms_contact(self):
        """Las páginas públicas institucionales deben responder 200."""
        for route in ['users:about', 'users:terms', 'users:contact']:
            resp = self.client.get(reverse(route))
            self.assertEqual(resp.status_code, 200)

    def test_official_teacher_name_consistency(self):
        """Verificar que el nombre de la docente oficial sea Jeymi Melanie Valdivia Eguiluz."""
        from pathlib import Path
        readme_path = Path(__file__).resolve().parent.parent / 'README.md'
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Jeymi Melanie Valdivia Eguiluz", content)
        self.assertNotIn("Rene Alonso Nieto", content)
        self.assertNotIn("Nieto Valencia", content)
