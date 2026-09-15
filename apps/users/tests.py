from django.contrib.auth import get_user_model # type: ignore
from django.test import TestCase # type: ignore
from django.urls import reverse # type: ignore
from apps.orders.models import Pedido
from apps.payments.models import Pago


class RolePortalAccessTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.password = 'TestPass123!'

		self.cliente = User.objects.create_user(
			username='cliente_test',
			password=self.password,
			role='cliente',
			email='cliente@test.com',
		)
		self.motorizado = User.objects.create_user(
			username='moto_test',
			password=self.password,
			role='motorizado',
			email='moto@test.com',
		)
		self.admin_user = User.objects.create_user(
			username='admin_test',
			password=self.password,
			role='admin',
			email='admin@test.com',
			is_staff=True,
			is_superuser=False,
		)

	def test_cliente_can_access_portal_cliente(self):
		self.client.force_login(self.cliente)
		response = self.client.get(reverse('users:portal_cliente'))
		self.assertEqual(response.status_code, 200)

	def test_motorizado_cannot_access_portal_cliente(self):
		self.client.force_login(self.motorizado)
		response = self.client.get(reverse('users:portal_cliente'))
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('home'))

	def test_motorizado_can_access_portal_motorizado(self):
		self.client.force_login(self.motorizado)
		response = self.client.get(reverse('users:portal_motorizado'), follow=True)
		self.assertEqual(response.status_code, 200)

	def test_cliente_cannot_access_portal_motorizado(self):
		self.client.force_login(self.cliente)
		response = self.client.get(reverse('users:portal_motorizado'), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.redirect_chain[-1][0], reverse('home'))

	def test_admin_can_access_portal_admin(self):
		self.client.force_login(self.admin_user)
		response = self.client.get(reverse('users:portal_admin'))
		self.assertEqual(response.status_code, 200)

	def test_cliente_cannot_access_portal_admin(self):
		self.client.force_login(self.cliente)
		response = self.client.get(reverse('users:portal_admin'))
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('home'))

	def test_admin_can_apply_bulk_user_activation(self):
		self.cliente.is_active = False
		self.cliente.save(update_fields=['is_active'])
		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('users:admin_users_bulk_action'),
			data={
				'action': 'activate',
				'selected_users': [self.cliente.id],
			}
		)
		self.assertEqual(response.status_code, 302)
		self.cliente.refresh_from_db()
		self.assertTrue(self.cliente.is_active)

	def test_admin_can_access_payments_and_audit_pages(self):
		pedido = Pedido.objects.create(
			cliente=self.cliente,
			estado='pendiente_asignacion',
			direccion_entrega='Av. Test 123',
			telefono_contacto='999111222',
			subtotal=10,
			costo_envio=5,
			total=15,
		)
		Pago.objects.create(
			pedido=pedido,
			metodo='yape',
			monto=15,
			estado='pendiente',
			referencia='TX-001',
		)

		self.client.force_login(self.admin_user)
		payments_response = self.client.get(reverse('users:admin_payments'))
		audit_response = self.client.get(reverse('users:admin_audit_logs'))

		self.assertEqual(payments_response.status_code, 200)
		self.assertEqual(audit_response.status_code, 200)
