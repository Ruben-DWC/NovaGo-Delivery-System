import json
import csv
from io import StringIO, BytesIO
from decimal import Decimal
from datetime import timedelta
from datetime import datetime
from pathlib import Path
from django.shortcuts import redirect, render, get_object_or_404 # type: ignore
from django.http import JsonResponse, HttpResponse # type: ignore
from django.urls import reverse_lazy, reverse # pyright: ignore[reportMissingModuleSource]
from django.views.generic import TemplateView, FormView, View, ListView, CreateView, UpdateView, DeleteView # type: ignore
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView # type: ignore
from django.contrib.auth import login, logout, get_user_model # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth.mixins import LoginRequiredMixin # type: ignore
from django.utils.decorators import method_decorator # type: ignore
from django.utils import timezone # pyright: ignore[reportMissingModuleSource]
from django.views.decorators.http import require_http_methods # type: ignore
from django.db import transaction # pyright: ignore[reportMissingModuleSource]
from django.db.models import Count, Sum, Q # pyright: ignore[reportMissingModuleSource]
from .forms import ClientRegisterForm, UserProfileForm, AdminProductForm, AdminCategoryForm, AdminUserManageForm
from .mixins import ClientRequiredMixin, AdminRequiredMixin, MotorizadoRequiredMixin
from .models import HistorialPerfilUsuario, AdminAuditLog
from apps.orders.models import Pedido
from apps.orders.models import ItemPedido
from apps.orders.views import CartView, OrderListView, OrderDetailView
from apps.tracking.views import TrackOrderView
from apps.products.models import Producto, Categoria
from apps.products.views import ProductListView, ProductDetailView
from apps.payments.models import Pago
from apps.orders.services import CartService, OrderService
from apps.orders.forms import CheckoutForm


def _build_csv_response(filename, headers, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    return response


def _build_xlsx_response(filename, sheet_name, headers, rows):
    try:
        from openpyxl import Workbook  # type: ignore
    except Exception:
        return _build_csv_response(filename, headers, rows)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response


def _build_pdf_response(filename, title, headers, rows, signer_name='Administrador', signature_label='Firma de auditoria'):
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage  # type: ignore
    except Exception:
        return _build_csv_response(filename, headers, rows)

    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []

    project_root = Path(__file__).resolve().parents[2]
    logo_path = project_root / 'static' / 'images' / 'novago-logo-pdf.png'
    header_row = []
    if logo_path.exists():
        header_row.append(RLImage(str(logo_path), width=110, height=36))
    else:
        header_row.append(Paragraph('NovaGo', styles['Heading2']))

    issued_at = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    header_row.append(
        Paragraph(
            f"<b>{title}</b><br/>Fecha de emision: {issued_at}<br/>Responsable: {signer_name}",
            styles['Normal'],
        )
    )

    header_table = Table([header_row], colWidths=[120, 420])
    header_table.setStyle(
        TableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.extend([header_table, Spacer(1, 10)])

    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0EA5E9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )
    elements.append(table)
    elements.extend(
        [
            Spacer(1, 20),
            Paragraph('_______________________________', styles['Normal']),
            Paragraph(f'{signature_label}: {signer_name}', styles['Normal']),
        ]
    )
    doc.build(elements)

    stream.seek(0)
    response = HttpResponse(stream.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


def _log_admin_action(actor, action, target_model, target_id='', description='', metadata=None):
    if not actor or not getattr(actor, 'is_authenticated', False):
        return
    if not (getattr(actor, 'role', '') == 'admin' or actor.is_staff or actor.is_superuser):
        return

    AdminAuditLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model,
        target_id=str(target_id or ''),
        description=description[:255] if description else f'Accion {action} sobre {target_model}',
        metadata=metadata or {},
    )


def resolve_destination_by_role(user):
    if user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'admin':
        return reverse('users:portal_admin')
    if getattr(user, 'role', '') == 'motorizado':
        return reverse('users:portal_motorizado')
    return reverse('users:portal_cliente')


def build_order_progress_payload(order):
    status_step_map = {
        'pendiente': 1,
        'pendiente_asignacion': 1,
        'confirmado': 1,
        'en_preparacion': 2,
        'en_camino': 3,
        'entregado': 4,
        'cancelado': 0,
    }
    status_progress_map = {
        0: 0,
        1: 15,
        2: 45,
        3: 75,
        4: 100,
    }
    eta_default_by_state = {
        'pendiente': 30,
        'pendiente_asignacion': 28,
        'confirmado': 24,
        'en_preparacion': 18,
        'en_camino': 11,
    }

    current_step = status_step_map.get(order.estado, 1)
    route = getattr(order, 'ruta', None)
    eta_minutes = route.tiempo_estimado_min if route and getattr(route, 'tiempo_estimado_min', None) else eta_default_by_state.get(order.estado, 20)

    return {
        'estado': order.estado,
        'estado_display': order.get_estado_display(),
        'progress_step': current_step,
        'progress_percent': status_progress_map.get(current_step, 15),
        'eta_minutes': eta_minutes,
    }

class HomeView(TemplateView):
    template_name = 'home.html'

class LoginView(AuthLoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return resolve_destination_by_role(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['auth_success_destination'] = self.get_success_url()
        self.request.session['auth_success_role'] = getattr(self.request.user, 'role', 'cliente')
        response['Location'] = reverse('users:login_success')
        return response

class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = ClientRegisterForm
    success_url = reverse_lazy('users:dashboard')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        self.request.session['register_was_reactivated'] = getattr(form, 'was_reactivated', False)
        self.request.session['register_success_destination'] = resolve_destination_by_role(user)
        self.request.session['register_success_role'] = getattr(user, 'role', 'cliente')
        return redirect('users:register_success')

class LogoutView(LoginRequiredMixin, View):
    """Vista personalizada de logout con pantalla de despedida"""
    login_url = 'users:login'
    
    def get(self, request):
        # Obtener el rol antes de cerrar sesión
        role = getattr(request.user, 'role', 'cliente')
        
        # Cerrar sesión
        logout(request)
        
        # Renderizar pantalla de despedida
        return render(request, 'users/logout_goodbye.html', {
            'role': role,
            'home_url': reverse('home'),
        })

class ProfileView(LoginRequiredMixin, FormView):
    login_url = reverse_lazy('users:login')
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('users:profile')

    def dispatch(self, request, *args, **kwargs):
        current_route = getattr(getattr(request, 'resolver_match', None), 'view_name', '')
        if getattr(request.user, 'role', '') == 'cliente' and current_route == 'users:profile':
            return redirect('users:portal_cliente_perfil')
        if getattr(request.user, 'role', '') == 'motorizado' and current_route == 'users:profile':
            return redirect('users:portal_motorizado_perfil')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        def stringify_value(value):
            if value is None:
                return ''
            if hasattr(value, 'url'):
                return 'Imagen'
            return str(value)

        changed_fields = []
        for field_name in form.changed_data:
            field = form.fields.get(field_name)
            old_value = getattr(self.request.user, field_name, None)
            new_value = form.cleaned_data.get(field_name)
            changed_fields.append({
                'field': field_name,
                'label': field.label if field else field_name,
                'before': stringify_value(old_value),
                'after': stringify_value(new_value),
            })

        form.save()

        if changed_fields:
            HistorialPerfilUsuario.objects.create(
                usuario=self.request.user,
                campos_modificados=changed_fields,
            )

        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'No se pudo actualizar el perfil. Revisa los campos marcados.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile_user'] = user
        latest_change = user.historial_perfil.first()
        context['profile_last_updated_at'] = latest_change.actualizado_en if latest_change else None
        context['profile_recent_updates'] = user.historial_perfil.all()[:6]

        if getattr(user, 'role', '') == 'cliente':
            orders = Pedido.objects.filter(cliente=user)
            context['profile_orders_total'] = orders.count()
            context['profile_orders_delivered'] = orders.filter(estado='entregado').count()
            context['profile_orders_active'] = orders.filter(estado__in=['pendiente_asignacion', 'confirmado', 'en_preparacion', 'en_camino']).count()
            context['profile_total_spent'] = sum(order.total for order in orders) if orders.exists() else Decimal('0.00')
        return context

class ProfileEditView(ProfileView):
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile_edit')

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'users/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, 'role', '') == 'motorizado':
            return redirect('users:portal_motorizado')
        if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return redirect('users:portal_admin')
        return redirect('users:portal_cliente')


class ClientPortalView(ClientRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'client/portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = Pedido.objects.filter(cliente=self.request.user).order_by('-fecha_pedido')
        context['is_cliente'] = getattr(self.request.user, 'role', '') == 'cliente'
        context['is_motorizado'] = getattr(self.request.user, 'role', '') == 'motorizado'
        context['recent_orders'] = orders[:5]
        context['total_orders'] = orders.count()
        context['active_orders'] = orders.filter(estado__in=['pendiente_asignacion', 'confirmado', 'en_preparacion', 'en_camino']).count()

        active_order = orders.filter(estado__in=['pendiente_asignacion', 'confirmado', 'en_preparacion', 'en_camino']).select_related('ruta').first()
        eta_default_by_state = {
            'pendiente_asignacion': 28,
            'confirmado': 24,
            'en_preparacion': 18,
            'en_camino': 11,
        }
        eta_minutes = None
        if active_order:
            route = getattr(active_order, 'ruta', None)
            if route and route.tiempo_estimado_min:
                eta_minutes = route.tiempo_estimado_min
            else:
                eta_minutes = eta_default_by_state.get(active_order.estado, 20)
        context['active_order_widget'] = active_order
        context['active_order_eta_minutes'] = eta_minutes
        
        # Calcular total gastado
        total_spent = sum(order.total for order in orders) if orders.exists() else Decimal('0.00')
        context['total_spent'] = total_spent
        return context


class ClientCatalogoView(ClientRequiredMixin, ProductListView):
    login_url = reverse_lazy('users:login')
    template_name = 'products/product_list.html'


class ClientProductoDetailView(ClientRequiredMixin, ProductDetailView):
    login_url = reverse_lazy('users:login')
    template_name = 'products/product_detail.html'


class ClientCarritoView(ClientRequiredMixin, CartView):
    login_url = reverse_lazy('users:login')


class ClientPedidosView(ClientRequiredMixin, OrderListView):
    login_url = reverse_lazy('users:login')


class ClientPedidoDetailView(ClientRequiredMixin, OrderDetailView):
    login_url = reverse_lazy('users:login')
    template_name = 'client/order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get('forbidden'):
            return context

        order = context.get('order')
        if order:
            progress_payload = build_order_progress_payload(order)
            context.update(progress_payload)
            context['progress_status_url'] = reverse(
                'users:portal_cliente_confirmacion_estado',
                kwargs={'pedido_id': order.id},
            )
        return context


class ClientPerfilView(ClientRequiredMixin, ProfileView):
    login_url = reverse_lazy('users:login')
    success_url = reverse_lazy('users:portal_cliente_perfil')


class MotorizadoPerfilView(MotorizadoRequiredMixin, ProfileView):
    login_url = reverse_lazy('users:login')
    success_url = reverse_lazy('users:portal_motorizado_perfil')


class ClientPaymentGatewayView(ClientRequiredMixin, FormView):
    login_url = reverse_lazy('users:login')
    template_name = 'client/payment_gateway.html'
    form_class = CheckoutForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(CartService.get_totals(self.request))

        payable_orders = (
            Pedido.objects.filter(cliente=self.request.user)
            .select_related('pago')
            .order_by('-fecha_pedido')[:8]
        )

        def payment_status(order):
            payment = getattr(order, 'pago', None)
            if payment:
                return payment.get_estado_display(), payment.estado
            if order.estado in ['pendiente_asignacion', 'confirmado', 'en_preparacion']:
                return 'Pendiente', 'pendiente'
            if order.estado == 'entregado':
                return 'Completado', 'completado'
            return 'Sin pago', 'sin_pago'

        context['payment_cards'] = [
            {
                'id': order.id,
                'total': order.total,
                'fecha': order.fecha_pedido,
                'estado_label': payment_status(order)[0],
                'estado_key': payment_status(order)[1],
            }
            for order in payable_orders
        ]
        return context

    def form_valid(self, form):
        try:
            # Preparar datos de pago específicos según método
            metodo_pago = form.cleaned_data['metodo_pago']
            datos_pago_adicionales = {
                'metodo': metodo_pago,
                'monto_efectivo': form.cleaned_data.get('monto_efectivo'),
                'numero_tarjeta_ultimos': form.cleaned_data.get('numero_tarjeta', '')[-4:] if form.cleaned_data.get('numero_tarjeta') else '',
                'mes_vencimiento': form.cleaned_data.get('mes_vencimiento'),
                'numero_celular': form.cleaned_data.get('numero_celular'),
                'tipo_pos': form.cleaned_data.get('tipo_pos'),
                'tipo_facturacion': form.cleaned_data.get('tipo_facturacion'),
                'acepta_terminos': form.cleaned_data.get('acepta_terminos'),
                'recibir_promociones': form.cleaned_data.get('recibir_promociones'),
            }
            
            order = OrderService.create_order_from_cart(
                user=self.request.user,
                request=self.request,
                direccion_entrega=form.cleaned_data['direccion_entrega'],
                telefono_contacto=form.cleaned_data['telefono_contacto'],
                metodo_pago=metodo_pago,
                referencia=form.cleaned_data.get('referencia', ''),
                notas=form.cleaned_data.get('notas', ''),
                datos_pago_adicionales=datos_pago_adicionales,
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)

        messages.success(self.request, 'Pedido generado correctamente desde la pasarela de cliente.')
        return redirect('users:portal_cliente_confirmacion', pedido_id=order.id)


class ClientOrderConfirmationView(ClientRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'client/order_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_object_or_404(
            Pedido.objects.select_related('cliente', 'motorizado').prefetch_related('items__producto', 'pago', 'ruta'),
            id=self.kwargs['pedido_id'],
            cliente=self.request.user,
        )
        progress_payload = build_order_progress_payload(order)
        context['order'] = order
        context.update(progress_payload)
        return context


class ClientOrderProgressApiView(ClientRequiredMixin, View):
    login_url = reverse_lazy('users:login')

    def get(self, request, pedido_id, *args, **kwargs):
        order = get_object_or_404(
            Pedido.objects.select_related('ruta', 'pago'),
            id=pedido_id,
            cliente=request.user,
        )
        payload = build_order_progress_payload(order)
        payload['payment_status_display'] = order.pago.get_estado_display() if getattr(order, 'pago', None) else 'Sin pago'
        payload['tracking_url'] = reverse('users:portal_cliente_rastreo_pedido', kwargs={'pedido_id': order.id})
        payload['orders_url'] = reverse('users:portal_cliente_pedidos')
        payload['detail_url'] = reverse('users:portal_cliente_pedido_detalle', kwargs={'pedido_id': order.id})
        payload['portal_url'] = reverse('users:portal_cliente')
        return JsonResponse(payload)


class ClientTrackingHubView(ClientRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'client/tracking_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_states = ['pendiente_asignacion', 'confirmado', 'en_preparacion', 'en_camino']
        orders = Pedido.objects.filter(cliente=self.request.user).order_by('-fecha_pedido')
        context['trackable_orders'] = orders.filter(estado__in=active_states)[:10]
        context['recent_orders'] = orders[:10]
        return context


class ClientTrackingOrderView(ClientRequiredMixin, TrackOrderView):
    login_url = reverse_lazy('users:login')


def build_admin_dashboard_context():
    User = get_user_model()

    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    month_start = today.replace(day=1)

    recent_orders = Pedido.objects.select_related('cliente', 'motorizado').order_by('-fecha_pedido')[:12]
    total_orders = Pedido.objects.count()
    total_users = User.objects.count()
    total_products = Producto.objects.count()
    low_stock_count = Producto.objects.filter(activo=True, stock__lte=5).count()

    revenue_qs = Pedido.objects.filter(estado='entregado')
    total_revenue_value = revenue_qs.aggregate(total=Sum('total')).get('total') or Decimal('0.00')
    revenue_today_value = revenue_qs.filter(fecha_entrega__date=today).aggregate(total=Sum('total')).get('total') or Decimal('0.00')

    delivered_count = Pedido.objects.filter(estado='entregado').count()
    completion_rate = round((delivered_count / total_orders) * 100, 1) if total_orders else 0

    avg_ticket = (total_revenue_value / delivered_count) if delivered_count else Decimal('0.00')

    status_rows = list(
        Pedido.objects.values('estado')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    status_labels = []
    status_values = []
    for row in status_rows:
        estado_key = row['estado']
        estado_label = dict(Pedido.ESTADO_CHOICES).get(estado_key, estado_key)
        status_labels.append(estado_label)
        status_values.append(row['total'])

    daily_labels = []
    daily_orders = []
    daily_revenue = []
    for idx in range(7):
        current_day = week_start + timedelta(days=idx)
        day_orders_qs = Pedido.objects.filter(fecha_pedido__date=current_day)
        day_revenue_qs = Pedido.objects.filter(estado='entregado', fecha_entrega__date=current_day)
        daily_labels.append(current_day.strftime('%d/%m'))
        daily_orders.append(day_orders_qs.count())
        daily_revenue.append(float(day_revenue_qs.aggregate(total=Sum('total')).get('total') or 0))

    payment_rows = list(
        Pago.objects.values('metodo')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )
    payment_labels = [dict(Pago.METODO_CHOICES).get(row['metodo'], row['metodo']) for row in payment_rows]
    payment_values = [row['total'] for row in payment_rows]

    top_products = list(
        ItemPedido.objects.values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:6]
    )

    users_by_role = list(User.objects.values('role').annotate(total=Count('id')).order_by('role'))
    user_role_labels = [dict(User.ROLE_CHOICES).get(row['role'], row['role']) for row in users_by_role]
    user_role_values = [row['total'] for row in users_by_role]

    cohort_labels = []
    cohort_values = []
    for idx in range(7, -1, -1):
        cohort_start = today - timedelta(days=(idx * 7))
        cohort_end = cohort_start + timedelta(days=6)
        cohort_users = User.objects.filter(
            role='cliente',
            fecha_registro__date__gte=cohort_start,
            fecha_registro__date__lte=cohort_end,
        )
        cohort_total = cohort_users.count()
        cohort_converted = Pedido.objects.filter(
            cliente__in=cohort_users,
            estado='entregado',
        ).values('cliente_id').distinct().count()
        conversion = round((cohort_converted / cohort_total) * 100, 1) if cohort_total else 0
        cohort_labels.append(f"{cohort_start.strftime('%d/%m')} - {cohort_end.strftime('%d/%m')}")
        cohort_values.append(conversion)

    funnel_created = total_orders
    funnel_assigned = Pedido.objects.exclude(motorizado__isnull=True).count()
    funnel_in_route = Pedido.objects.filter(estado__in=['en_camino', 'entregado']).count()
    funnel_delivered = delivered_count

    return {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_products': total_products,
        'orders_today': Pedido.objects.filter(fecha_pedido__date=today).count(),
        'orders_month': Pedido.objects.filter(fecha_pedido__date__gte=month_start).count(),
        'total_revenue': f"S/. {total_revenue_value:.2f}",
        'revenue_today': f"S/. {revenue_today_value:.2f}",
        'avg_ticket': f"S/. {avg_ticket:.2f}",
        'completion_rate': completion_rate,
        'low_stock_count': low_stock_count,
        'users_by_role': users_by_role,
        'chart_user_role_labels': json.dumps(user_role_labels),
        'chart_user_role_values': json.dumps(user_role_values),
        'top_products': top_products,
        'chart_status_labels': json.dumps(status_labels),
        'chart_status_values': json.dumps(status_values),
        'chart_daily_labels': json.dumps(daily_labels),
        'chart_daily_orders': json.dumps(daily_orders),
        'chart_daily_revenue': json.dumps(daily_revenue),
        'chart_payment_labels': json.dumps(payment_labels),
        'chart_payment_values': json.dumps(payment_values),
        'chart_cohort_labels': json.dumps(cohort_labels),
        'chart_cohort_values': json.dumps(cohort_values),
        'chart_funnel_labels': json.dumps(['Creados', 'Asignados', 'En ruta', 'Entregados']),
        'chart_funnel_values': json.dumps([funnel_created, funnel_assigned, funnel_in_route, funnel_delivered]),
    }


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_admin_dashboard_context())
        return context


class AdminAnalyticsBaseView(AdminRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    page_title = ''
    page_description = ''
    page_variant = ''
    template_name = 'admin/analytics_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_admin_dashboard_context())
        context['page_title'] = self.page_title
        context['page_description'] = self.page_description
        context['page_variant'] = self.page_variant
        return context


class AdminReportsView(AdminAnalyticsBaseView):
    template_name = 'admin/analytics_page.html'
    page_title = 'Reportes ejecutivos'
    page_description = 'Distribución de estados, usuarios por rol y pedidos recientes en una vista independiente.'
    page_variant = 'reports'


class AdminIncomeView(AdminAnalyticsBaseView):
    template_name = 'admin/analytics_page.html'
    page_title = 'Ingresos y ventas'
    page_description = 'Tendencia de ingresos, ticket promedio y métodos de pago más usados.'
    page_variant = 'income'


class AdminPerformanceView(AdminAnalyticsBaseView):
    template_name = 'admin/analytics_page.html'
    page_title = 'Performance operativa'
    page_description = 'Embudo de conversión, cohortes y productos más vendidos para seguimiento operativo.'
    page_variant = 'performance'


class AdminOrdersManageView(AdminRequiredMixin, ListView):
    template_name = 'admin/orders_manage.html'
    model = Pedido
    context_object_name = 'orders'
    paginate_by = 20

    @staticmethod
    def build_filtered_queryset(request):
        queryset = Pedido.objects.select_related('cliente', 'motorizado', 'pago').order_by('-fecha_pedido')
        q = (request.GET.get('q') or '').strip()
        estado = (request.GET.get('estado') or '').strip()
        metodo_pago = (request.GET.get('metodo_pago') or '').strip()
        assigned = (request.GET.get('assigned') or '').strip()

        if q:
            queryset = queryset.filter(
                Q(id__icontains=q)
                | Q(cliente__username__icontains=q)
                | Q(cliente__first_name__icontains=q)
                | Q(cliente__last_name__icontains=q)
                | Q(telefono_contacto__icontains=q)
            )
        if estado in dict(Pedido.ESTADO_CHOICES):
            queryset = queryset.filter(estado=estado)
        if metodo_pago in dict(Pago.METODO_CHOICES):
            queryset = queryset.filter(pago__metodo=metodo_pago)
        if assigned == '1':
            queryset = queryset.exclude(motorizado__isnull=True)
        elif assigned == '0':
            queryset = queryset.filter(motorizado__isnull=True)

        return queryset

    def get_queryset(self):
        return self.build_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['motorizados'] = User.objects.filter(role='motorizado', is_active=True).order_by('username')
        context['estado_options'] = Pedido.ESTADO_CHOICES
        context['metodo_pago_options'] = Pago.METODO_CHOICES
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_estado'] = (self.request.GET.get('estado') or '').strip()
        context['filter_metodo_pago'] = (self.request.GET.get('metodo_pago') or '').strip()
        context['filter_assigned'] = (self.request.GET.get('assigned') or '').strip()
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        if 'scope' in query_params:
            query_params.pop('scope')
        context['pagination_query'] = query_params.urlencode()
        return context


class AdminOrdersBulkActionView(AdminRequiredMixin, View):
    def post(self, request):
        action = (request.POST.get('action') or '').strip()
        order_ids = request.POST.getlist('selected_orders')

        if not order_ids:
            messages.warning(request, 'Selecciona al menos un pedido para aplicar acciones masivas.')
            return redirect('users:admin_orders')

        orders = Pedido.objects.filter(id__in=order_ids)
        if not orders.exists():
            messages.error(request, 'No se encontraron pedidos válidos para procesar.')
            return redirect('users:admin_orders')

        with transaction.atomic():
            if action == 'assign':
                motorizado_id = request.POST.get('motorizado_id')
                if not motorizado_id:
                    messages.error(request, 'Selecciona un motorizado para asignar.')
                    return redirect('users:admin_orders')
                motorizado = get_object_or_404(get_user_model(), id=motorizado_id, role='motorizado')
                updated = orders.update(motorizado=motorizado, fecha_asignacion=timezone.now())
                _log_admin_action(
                    request.user,
                    'bulk_update',
                    'Pedido',
                    description='Asignacion masiva de pedidos',
                    metadata={'count': updated, 'motorizado_id': motorizado.id, 'order_ids': order_ids},
                )
                messages.success(request, f'{updated} pedidos asignados a {motorizado.get_full_name() or motorizado.username}.')
            elif action == 'status':
                new_status = (request.POST.get('new_status') or '').strip()
                if new_status not in dict(Pedido.ESTADO_CHOICES):
                    messages.error(request, 'Estado inválido para actualización masiva.')
                    return redirect('users:admin_orders')
                updated = orders.update(estado=new_status)
                _log_admin_action(
                    request.user,
                    'bulk_update',
                    'Pedido',
                    description='Cambio masivo de estado de pedidos',
                    metadata={'count': updated, 'new_status': new_status, 'order_ids': order_ids},
                )
                messages.success(request, f'{updated} pedidos actualizados al estado {dict(Pedido.ESTADO_CHOICES).get(new_status)}.')
            elif action == 'cancel':
                updated = orders.update(estado='cancelado')
                _log_admin_action(
                    request.user,
                    'bulk_update',
                    'Pedido',
                    description='Cancelacion masiva de pedidos',
                    metadata={'count': updated, 'order_ids': order_ids},
                )
                messages.success(request, f'{updated} pedidos cancelados correctamente.')
            else:
                messages.error(request, 'Acción masiva no reconocida.')

        return redirect('users:admin_orders')


class AdminDashboardExportView(AdminRequiredMixin, View):
    def get(self, request):
        export_format = (request.GET.get('format') or 'csv').lower()
        today = timezone.localdate()
        User = get_user_model()
        delivered_qs = Pedido.objects.filter(estado='entregado')
        total_revenue = delivered_qs.aggregate(total=Sum('total')).get('total') or Decimal('0.00')
        revenue_today = delivered_qs.filter(fecha_entrega__date=today).aggregate(total=Sum('total')).get('total') or Decimal('0.00')

        headers = ['Fecha', 'Pedidos Totales', 'Pedidos Hoy', 'Usuarios', 'Productos', 'Ingresos Totales', 'Ingresos Hoy']
        rows = [[
            today.isoformat(),
            Pedido.objects.count(),
            Pedido.objects.filter(fecha_pedido__date=today).count(),
            User.objects.count(),
            Producto.objects.count(),
            float(total_revenue),
            float(revenue_today),
        ]]

        if export_format == 'xlsx':
            _log_admin_action(request.user, 'export', 'Dashboard', description='Exportacion dashboard admin', metadata={'format': 'xlsx'})
            return _build_xlsx_response('dashboard_admin', 'Dashboard', headers, rows)
        _log_admin_action(request.user, 'export', 'Dashboard', description='Exportacion dashboard admin', metadata={'format': 'csv'})
        return _build_csv_response('dashboard_admin', headers, rows)


class AdminOrdersExportView(AdminRequiredMixin, View):
    def get(self, request):
        export_format = (request.GET.get('format') or 'csv').lower()
        orders = AdminOrdersManageView.build_filtered_queryset(request)

        headers = ['ID', 'Cliente', 'Motorizado', 'Estado', 'Metodo Pago', 'Total', 'Fecha Pedido']
        rows = [
            [
                order.id,
                order.cliente.get_full_name() or order.cliente.username,
                (order.motorizado.get_full_name() or order.motorizado.username) if order.motorizado else 'Sin asignar',
                order.get_estado_display(),
                order.pago.get_metodo_display() if getattr(order, 'pago', None) else 'Sin pago',
                float(order.total),
                timezone.localtime(order.fecha_pedido).strftime('%d/%m/%Y %H:%M'),
            ]
            for order in orders
        ]

        if export_format == 'xlsx':
            _log_admin_action(request.user, 'export', 'Pedido', description='Exportacion de pedidos', metadata={'format': 'xlsx', 'rows': len(rows)})
            return _build_xlsx_response('pedidos_admin', 'Pedidos', headers, rows)
        _log_admin_action(request.user, 'export', 'Pedido', description='Exportacion de pedidos', metadata={'format': 'csv', 'rows': len(rows)})
        return _build_csv_response('pedidos_admin', headers, rows)


class AdminUsersExportView(AdminRequiredMixin, View):
    def get(self, request):
        export_format = (request.GET.get('format') or 'csv').lower()
        users = get_user_model().objects.all()

        scope = (request.GET.get('scope') or 'all').strip()
        q = (request.GET.get('q') or '').strip()
        role = (request.GET.get('role') or '').strip()
        active = (request.GET.get('active') or '').strip()
        if scope == 'clientes':
            users = users.filter(role='cliente')
        elif scope == 'empleados':
            users = users.filter(role__in=['motorizado', 'admin'])
        if q:
            users = users.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
        if role in {'cliente', 'motorizado', 'admin'}:
            users = users.filter(role=role)
        if active == '1':
            users = users.filter(is_active=True)
        elif active == '0':
            users = users.filter(is_active=False)

        headers = ['ID', 'Usuario', 'Nombre', 'Email', 'Rol', 'Activo', 'Fecha Registro']
        rows = [
            [
                user.id,
                user.username,
                user.get_full_name(),
                user.email,
                user.get_role_display(),
                'Si' if user.is_active else 'No',
                timezone.localtime(user.fecha_registro).strftime('%d/%m/%Y %H:%M') if user.fecha_registro else '',
            ]
            for user in users.order_by('-fecha_registro')
        ]

        if export_format == 'xlsx':
            _log_admin_action(request.user, 'export', 'User', description='Exportacion de usuarios', metadata={'format': 'xlsx', 'rows': len(rows), 'scope': scope})
            return _build_xlsx_response('usuarios_admin', 'Usuarios', headers, rows)
        _log_admin_action(request.user, 'export', 'User', description='Exportacion de usuarios', metadata={'format': 'csv', 'rows': len(rows), 'scope': scope})
        return _build_csv_response('usuarios_admin', headers, rows)


class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = 'admin/products_list.html'
    model = Producto
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Producto.objects.select_related('categoria').order_by('-fecha_creacion')
        q = (self.request.GET.get('q') or '').strip()
        category = (self.request.GET.get('category') or '').strip()
        active = (self.request.GET.get('active') or '').strip()

        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        if category.isdigit():
            queryset = queryset.filter(categoria_id=int(category))
        if active == '1':
            queryset = queryset.filter(activo=True)
        elif active == '0':
            queryset = queryset.filter(activo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['categories'] = Categoria.objects.order_by('nombre')
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_category'] = (self.request.GET.get('category') or '').strip()
        context['filter_active'] = (self.request.GET.get('active') or '').strip()
        context['pagination_query'] = query_params.urlencode()
        return context


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name = 'admin/product_form.html'
    model = Producto
    form_class = AdminProductForm
    success_url = reverse_lazy('users:admin_products')

    def form_valid(self, form):
        messages.success(self.request, 'Producto creado correctamente.')
        return super().form_valid(form)


class AdminProductUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'admin/product_form.html'
    model = Producto
    form_class = AdminProductForm
    success_url = reverse_lazy('users:admin_products')

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado correctamente.')
        return super().form_valid(form)


class AdminProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Producto
    success_url = reverse_lazy('users:admin_products')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Producto eliminado correctamente.')
        return super().post(request, *args, **kwargs)


class AdminCategoryListView(AdminRequiredMixin, ListView):
    template_name = 'admin/categories_list.html'
    model = Categoria
    context_object_name = 'categories'
    paginate_by = 12

    def get_queryset(self):
        queryset = Categoria.objects.order_by('nombre')
        q = (self.request.GET.get('q') or '').strip()
        active = (self.request.GET.get('active') or '').strip()
        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        if active == '1':
            queryset = queryset.filter(activa=True)
        elif active == '0':
            queryset = queryset.filter(activa=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_active'] = (self.request.GET.get('active') or '').strip()
        context['pagination_query'] = query_params.urlencode()
        return context


class AdminCategoryCreateView(AdminRequiredMixin, CreateView):
    template_name = 'admin/category_form.html'
    model = Categoria
    form_class = AdminCategoryForm
    success_url = reverse_lazy('users:admin_categories')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada correctamente.')
        return super().form_valid(form)


class AdminCategoryUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'admin/category_form.html'
    model = Categoria
    form_class = AdminCategoryForm
    success_url = reverse_lazy('users:admin_categories')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada correctamente.')
        return super().form_valid(form)


class AdminCategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Categoria
    success_url = reverse_lazy('users:admin_categories')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Categoría eliminada correctamente.')
        return super().post(request, *args, **kwargs)


class AdminUserListView(AdminRequiredMixin, ListView):
    template_name = 'admin/users_list.html'
    model = get_user_model()
    context_object_name = 'admin_users'
    paginate_by = 14

    scope = 'all'

    def get_scope(self):
        if self.scope and self.scope != 'all':
            return self.scope
        return (self.kwargs.get('scope') or 'all').strip()

    def get_queryset(self):
        queryset = get_user_model().objects.order_by('-fecha_registro')
        scope = self.get_scope()
        q = (self.request.GET.get('q') or '').strip()
        role = (self.request.GET.get('role') or '').strip()
        active = (self.request.GET.get('active') or '').strip()

        if scope == 'clientes':
            queryset = queryset.filter(role='cliente')
        elif scope == 'empleados':
            queryset = queryset.filter(role__in=['motorizado', 'admin'])

        if q:
            queryset = queryset.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
        if role in {'cliente', 'motorizado', 'admin'}:
            queryset = queryset.filter(role=role)
        if active == '1':
            queryset = queryset.filter(is_active=True)
        elif active == '0':
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = get_user_model().objects.all()
        scope = self.get_scope()

        if scope == 'clientes':
            base_queryset = base_queryset.filter(role='cliente')
            page_title = 'Gestión de Clientes'
            page_description = 'Control de cuentas de clientes, estado de actividad y contacto.'
        elif scope == 'empleados':
            base_queryset = base_queryset.filter(role__in=['motorizado', 'admin'])
            page_title = 'Gestión de Empleados'
            page_description = 'Supervisión de equipo interno y motorizados con acceso operativo.'
        else:
            page_title = 'Gestión de Usuarios'
            page_description = 'Administración global de clientes, motorizados y administradores.'

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')

        context['scope'] = scope
        context['page_title'] = page_title
        context['page_description'] = page_description
        context['stats_total'] = base_queryset.count()
        context['stats_active'] = base_queryset.filter(is_active=True).count()
        context['stats_inactive'] = base_queryset.filter(is_active=False).count()
        context['stats_clientes'] = base_queryset.filter(role='cliente').count()
        context['stats_motorizados'] = base_queryset.filter(role='motorizado').count()
        context['stats_admins'] = base_queryset.filter(role='admin').count()
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_role'] = (self.request.GET.get('role') or '').strip()
        context['filter_active'] = (self.request.GET.get('active') or '').strip()
        context['pagination_query'] = query_params.urlencode()
        context['export_query'] = query_params.urlencode()
        return context


class AdminUsersBulkActionView(AdminRequiredMixin, View):
    def post(self, request):
        action = (request.POST.get('action') or '').strip()
        selected_ids = request.POST.getlist('selected_users')
        redirect_query = (request.POST.get('next_query') or '').strip()
        redirect_url = reverse('users:admin_users')
        if redirect_query:
            redirect_url = f"{redirect_url}?{redirect_query}"

        if not selected_ids:
            messages.warning(request, 'Selecciona al menos un usuario para aplicar acciones masivas.')
            return redirect(redirect_url)

        queryset = get_user_model().objects.filter(id__in=selected_ids)
        if not queryset.exists():
            messages.error(request, 'No se encontraron usuarios validos para procesar.')
            return redirect(redirect_url)

        if action == 'activate':
            updated = queryset.update(is_active=True)
            _log_admin_action(
                request.user,
                'bulk_update',
                'User',
                description='Activacion masiva de usuarios',
                metadata={'count': updated, 'user_ids': selected_ids},
            )
            messages.success(request, f'{updated} usuarios activados correctamente.')
        elif action == 'deactivate':
            updated = queryset.exclude(id=request.user.id).update(is_active=False)
            _log_admin_action(
                request.user,
                'bulk_update',
                'User',
                description='Desactivacion masiva de usuarios',
                metadata={'count': updated, 'user_ids': selected_ids},
            )
            messages.success(request, f'{updated} usuarios desactivados correctamente.')
        elif action == 'change_role':
            new_role = (request.POST.get('bulk_role') or '').strip()
            if new_role not in {'cliente', 'motorizado', 'admin'}:
                messages.error(request, 'Selecciona un rol valido para el cambio masivo.')
                return redirect(redirect_url)

            updated = queryset.update(role=new_role)
            _log_admin_action(
                request.user,
                'bulk_update',
                'User',
                description='Cambio masivo de rol de usuarios',
                metadata={'count': updated, 'new_role': new_role, 'user_ids': selected_ids},
            )
            messages.success(request, f'{updated} usuarios actualizados al rol {dict(get_user_model().ROLE_CHOICES).get(new_role, new_role)}.')
        else:
            messages.error(request, 'Accion masiva de usuarios no reconocida.')

        return redirect(redirect_url)


class AdminUserUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'admin/user_form.html'
    model = get_user_model()
    form_class = AdminUserManageForm
    success_url = reverse_lazy('users:admin_users')

    def form_valid(self, form):
        changed_fields = list(form.changed_data)
        messages.success(self.request, 'Usuario actualizado correctamente.')
        _log_admin_action(
            self.request.user,
            'update',
            'User',
            target_id=self.object.id,
            description='Actualizacion de usuario desde panel admin',
            metadata={'changed_fields': changed_fields},
        )
        return super().form_valid(form)


class AdminPaymentsManageView(AdminRequiredMixin, ListView):
    template_name = 'admin/payments_manage.html'
    model = Pago
    context_object_name = 'payments'
    paginate_by = 20

    @staticmethod
    def build_filtered_queryset(request):
        queryset = Pago.objects.select_related('pedido', 'pedido__cliente', 'conciliado_por').order_by('-fecha_pago')
        q = (request.GET.get('q') or '').strip()
        estado = (request.GET.get('estado') or '').strip()
        metodo = (request.GET.get('metodo') or '').strip()
        conciliado = (request.GET.get('conciliado') or '').strip()

        if q:
            queryset = queryset.filter(
                Q(id__icontains=q)
                | Q(pedido__id__icontains=q)
                | Q(pedido__cliente__username__icontains=q)
                | Q(referencia__icontains=q)
            )
        if estado in dict(Pago.ESTADO_CHOICES):
            queryset = queryset.filter(estado=estado)
        if metodo in dict(Pago.METODO_CHOICES):
            queryset = queryset.filter(metodo=metodo)
        if conciliado == '1':
            queryset = queryset.filter(conciliado=True)
        elif conciliado == '0':
            queryset = queryset.filter(conciliado=False)
        return queryset

    def get_queryset(self):
        return self.build_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['estado_options'] = Pago.ESTADO_CHOICES
        context['metodo_options'] = Pago.METODO_CHOICES
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_estado'] = (self.request.GET.get('estado') or '').strip()
        context['filter_metodo'] = (self.request.GET.get('metodo') or '').strip()
        context['filter_conciliado'] = (self.request.GET.get('conciliado') or '').strip()
        context['pagination_query'] = query_params.urlencode()
        context['stats_total'] = Pago.objects.count()
        context['stats_pendientes'] = Pago.objects.filter(estado='pendiente').count()
        context['stats_completados'] = Pago.objects.filter(estado='completado').count()
        context['stats_conciliados'] = Pago.objects.filter(conciliado=True).count()
        return context


class AdminPaymentsBulkActionView(AdminRequiredMixin, View):
    def post(self, request):
        action = (request.POST.get('action') or '').strip()
        selected_ids = request.POST.getlist('selected_payments')

        if not selected_ids:
            messages.warning(request, 'Selecciona al menos un pago para procesar acciones masivas.')
            return redirect('users:admin_payments')

        payments = Pago.objects.filter(id__in=selected_ids)
        if not payments.exists():
            messages.error(request, 'No se encontraron pagos validos para procesar.')
            return redirect('users:admin_payments')

        if action == 'set_status':
            new_status = (request.POST.get('new_status') or '').strip()
            if new_status not in dict(Pago.ESTADO_CHOICES):
                messages.error(request, 'Estado de pago invalido para la accion masiva.')
                return redirect('users:admin_payments')

            updates = {'estado': new_status}
            if new_status == 'completado':
                updates['fecha_confirmacion'] = timezone.now()
            updated = payments.update(**updates)
            _log_admin_action(
                request.user,
                'bulk_update',
                'Pago',
                description='Cambio masivo de estado de pagos',
                metadata={'count': updated, 'new_status': new_status, 'payment_ids': selected_ids},
            )
            messages.success(request, f'{updated} pagos actualizados al estado {dict(Pago.ESTADO_CHOICES).get(new_status)}.')
        elif action == 'reconcile':
            updated = payments.update(conciliado=True, fecha_conciliacion=timezone.now(), conciliado_por=request.user)
            _log_admin_action(
                request.user,
                'bulk_update',
                'Pago',
                description='Conciliacion masiva de pagos',
                metadata={'count': updated, 'payment_ids': selected_ids},
            )
            messages.success(request, f'{updated} pagos conciliados correctamente.')
        elif action == 'unreconcile':
            updated = payments.update(conciliado=False, fecha_conciliacion=None, conciliado_por=None)
            _log_admin_action(
                request.user,
                'bulk_update',
                'Pago',
                description='Desconciliacion masiva de pagos',
                metadata={'count': updated, 'payment_ids': selected_ids},
            )
            messages.success(request, f'{updated} pagos marcados como no conciliados.')
        else:
            messages.error(request, 'Accion masiva de pagos no reconocida.')

        return redirect('users:admin_payments')


class AdminPaymentsExportView(AdminRequiredMixin, View):
    def get(self, request):
        export_format = (request.GET.get('format') or 'csv').lower()
        payments = AdminPaymentsManageView.build_filtered_queryset(request)
        headers = ['ID', 'Pedido', 'Cliente', 'Metodo', 'Estado', 'Monto', 'Conciliado', 'Conciliado Por', 'Fecha Pago', 'Fecha Conciliacion', 'Referencia']
        rows = [
            [
                payment.id,
                payment.pedido_id,
                payment.pedido.cliente.get_full_name() or payment.pedido.cliente.username,
                payment.get_metodo_display(),
                payment.get_estado_display(),
                float(payment.monto),
                'Si' if payment.conciliado else 'No',
                payment.conciliado_por.get_full_name() if payment.conciliado_por else '',
                timezone.localtime(payment.fecha_pago).strftime('%d/%m/%Y %H:%M') if payment.fecha_pago else '',
                timezone.localtime(payment.fecha_conciliacion).strftime('%d/%m/%Y %H:%M') if payment.fecha_conciliacion else '',
                payment.referencia,
            ]
            for payment in payments
        ]

        if export_format == 'xlsx':
            _log_admin_action(request.user, 'export', 'Pago', description='Exportacion de pagos', metadata={'format': 'xlsx', 'rows': len(rows)})
            return _build_xlsx_response('pagos_admin', 'Pagos', headers, rows)
        if export_format == 'pdf':
            _log_admin_action(request.user, 'export', 'Pago', description='Exportacion de pagos', metadata={'format': 'pdf', 'rows': len(rows)})
            signer_name = request.user.get_full_name() or request.user.username
            return _build_pdf_response('pagos_admin', 'Reporte de pagos administrativos', headers, rows, signer_name=signer_name)
        _log_admin_action(request.user, 'export', 'Pago', description='Exportacion de pagos', metadata={'format': 'csv', 'rows': len(rows)})
        return _build_csv_response('pagos_admin', headers, rows)


class AdminAuditLogListView(AdminRequiredMixin, ListView):
    template_name = 'admin/audit_logs.html'
    model = AdminAuditLog
    context_object_name = 'audit_logs'
    paginate_by = 25

    @staticmethod
    def build_filtered_queryset(request):
        queryset = AdminAuditLog.objects.select_related('actor').order_by('-created_at')
        q = (request.GET.get('q') or '').strip()
        action = (request.GET.get('action') or '').strip()
        model_name = (request.GET.get('model') or '').strip()
        from_date = (request.GET.get('from_date') or '').strip()
        to_date = (request.GET.get('to_date') or '').strip()
        from_datetime = (request.GET.get('from_datetime') or '').strip()
        to_datetime = (request.GET.get('to_datetime') or '').strip()

        if q:
            queryset = queryset.filter(
                Q(description__icontains=q)
                | Q(target_model__icontains=q)
                | Q(target_id__icontains=q)
                | Q(actor__username__icontains=q)
            )
        if action in dict(AdminAuditLog.ACTION_CHOICES):
            queryset = queryset.filter(action=action)
        if model_name:
            queryset = queryset.filter(target_model__icontains=model_name)
        if from_datetime:
            try:
                from_dt = datetime.fromisoformat(from_datetime)
                if timezone.is_naive(from_dt):
                    from_dt = timezone.make_aware(from_dt, timezone.get_current_timezone())
                queryset = queryset.filter(created_at__gte=from_dt)
            except ValueError:
                pass
        if to_datetime:
            try:
                to_dt = datetime.fromisoformat(to_datetime)
                if timezone.is_naive(to_dt):
                    to_dt = timezone.make_aware(to_dt, timezone.get_current_timezone())
                queryset = queryset.filter(created_at__lte=to_dt)
            except ValueError:
                pass
        if from_date:
            try:
                from_date_dt = datetime.strptime(from_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=from_date_dt)
            except ValueError:
                pass
        if to_date:
            try:
                to_date_dt = datetime.strptime(to_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=to_date_dt)
            except ValueError:
                pass
        return queryset

    def get_queryset(self):
        return self.build_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['action_options'] = AdminAuditLog.ACTION_CHOICES
        context['filter_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_action'] = (self.request.GET.get('action') or '').strip()
        context['filter_model'] = (self.request.GET.get('model') or '').strip()
        context['filter_from_date'] = (self.request.GET.get('from_date') or '').strip()
        context['filter_to_date'] = (self.request.GET.get('to_date') or '').strip()
        context['filter_from_datetime'] = (self.request.GET.get('from_datetime') or '').strip()
        context['filter_to_datetime'] = (self.request.GET.get('to_datetime') or '').strip()
        context['pagination_query'] = query_params.urlencode()
        context['export_query'] = query_params.urlencode()
        return context


class AdminAuditLogExportView(AdminRequiredMixin, View):
    def get(self, request):
        export_format = (request.GET.get('format') or 'csv').lower()
        logs = AdminAuditLogListView.build_filtered_queryset(request)
        headers = ['Fecha', 'Administrador', 'Accion', 'Modelo', 'ID Objetivo', 'Descripcion']
        rows = [
            [
                timezone.localtime(item.created_at).strftime('%d/%m/%Y %H:%M'),
                item.actor.get_full_name() or item.actor.username if item.actor else 'Sistema',
                item.get_action_display(),
                item.target_model,
                item.target_id,
                item.description,
            ]
            for item in logs
        ]
        if export_format == 'xlsx':
            _log_admin_action(request.user, 'export', 'AdminAuditLog', description='Exportacion de bitacora administrativa', metadata={'format': 'xlsx', 'rows': len(rows)})
            return _build_xlsx_response('bitacora_admin', 'Bitacora', headers, rows)
        if export_format == 'pdf':
            _log_admin_action(request.user, 'export', 'AdminAuditLog', description='Exportacion de bitacora administrativa', metadata={'format': 'pdf', 'rows': len(rows)})
            signer_name = request.user.get_full_name() or request.user.username
            return _build_pdf_response('bitacora_admin', 'Bitacora administrativa', headers, rows, signer_name=signer_name)
        _log_admin_action(request.user, 'export', 'AdminAuditLog', description='Exportacion de bitacora administrativa', metadata={'format': 'csv', 'rows': len(rows)})
        return _build_csv_response('bitacora_admin', headers, rows)


class AdminClientListView(AdminUserListView):
    scope = 'clientes'


class AdminEmployeeListView(AdminUserListView):
    scope = 'empleados'


class AdminRolesManageView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/roles_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        by_role = User.objects.values('role').annotate(total=Count('id')).order_by('role')
        totals = {row['role']: row['total'] for row in by_role}
        context['roles_summary'] = [
            {
                'key': 'cliente',
                'label': 'Cliente',
                'total': totals.get('cliente', 0),
                'description': 'Compra productos, gestiona pagos y rastrea pedidos.',
            },
            {
                'key': 'motorizado',
                'label': 'Motorizado',
                'total': totals.get('motorizado', 0),
                'description': 'Gestiona entregas, ubicación en ruta y estado operativo.',
            },
            {
                'key': 'admin',
                'label': 'Administrador',
                'total': totals.get('admin', 0),
                'description': 'Supervisa KPIs, catálogos, pedidos y usuarios del sistema.',
            },
        ]
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['inactive_users'] = User.objects.filter(is_active=False).count()
        return context


class LoginSuccessView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'users/login_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination = self.request.session.pop('auth_success_destination', resolve_destination_by_role(self.request.user))
        role = self.request.session.pop('auth_success_role', getattr(self.request.user, 'role', 'cliente'))
        context['destination'] = destination
        context['role'] = role
        context['seconds'] = 2
        return context


class RegisterSuccessView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('users:login')
    template_name = 'users/register_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination = self.request.session.pop('register_success_destination', resolve_destination_by_role(self.request.user))
        role = self.request.session.pop('register_success_role', getattr(self.request.user, 'role', 'cliente'))
        was_reactivated = self.request.session.pop('register_was_reactivated', False)
        context['destination'] = destination
        context['role'] = role
        context['was_reactivated'] = was_reactivated
        context['seconds'] = 3
        return context
