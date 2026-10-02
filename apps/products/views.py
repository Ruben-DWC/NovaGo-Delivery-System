from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from .models import Producto, Categoria


class ProductListView(ListView):
	model = Producto
	template_name = 'products/product_list.html'
	context_object_name = 'products'
	paginate_by = 12

	def get_queryset(self):
		queryset = (
			Producto.objects.select_related('categoria')
			.filter(activo=True)
		)

		categoria_id = self.kwargs.get('categoria_id')
		query = self.request.GET.get('q', '').strip()
		sort = self.request.GET.get('sort', '').strip()
		min_price = self.request.GET.get('min_price', '').strip()
		max_price = self.request.GET.get('max_price', '').strip()

		if categoria_id:
			queryset = queryset.filter(categoria_id=categoria_id, categoria__activa=True)

		if query:
			queryset = queryset.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))

		if min_price:
			try:
				queryset = queryset.filter(precio__gte=float(min_price))
			except (ValueError, TypeError):
				pass

		if max_price:
			try:
				queryset = queryset.filter(precio__lte=float(max_price))
			except (ValueError, TypeError):
				pass

		# Ordenamiento dinámico
		if sort == 'precio_asc':
			queryset = queryset.order_by('precio')
		elif sort == 'precio_desc':
			queryset = queryset.order_by('-precio')
		elif sort == 'nombre_asc':
			queryset = queryset.order_by('nombre')
		elif sort == 'recientes':
			queryset = queryset.order_by('-fecha_creacion')
		else:
			queryset = queryset.order_by('-destacado', '-fecha_creacion')

		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		is_client_role = self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'cliente'
		if is_client_role:
			context['catalog_url_name'] = 'users:portal_cliente_catalogo'
			context['catalog_category_url_name'] = 'users:portal_cliente_catalogo_categoria'
			context['product_detail_url_name'] = 'users:portal_cliente_producto'
			context['search_url_name'] = 'users:portal_cliente_catalogo'
		else:
			context['catalog_url_name'] = 'products:product_list'
			context['catalog_category_url_name'] = 'products:product_list_by_category'
			context['product_detail_url_name'] = 'products:product_detail'
			context['search_url_name'] = 'products:product_search'

		# Categorías con conteo de productos activos
		from django.db.models import Count
		categories_with_count = Categoria.objects.filter(activa=True).annotate(
			total_productos=Count('productos', filter=Q(productos__activo=True))
		).order_by('nombre')

		context['categories'] = categories_with_count
		context['total_all_products'] = Producto.objects.filter(activo=True).count()
		context['active_category'] = self.kwargs.get('categoria_id')
		context['search_query'] = self.request.GET.get('q', '').strip()
		context['active_sort'] = self.request.GET.get('sort', '').strip()
		context['min_price'] = self.request.GET.get('min_price', '').strip()
		context['max_price'] = self.request.GET.get('max_price', '').strip()
		return context


class ProductSearchView(ProductListView):
	pass


class ProductDetailView(DetailView):
	model = Producto
	template_name = 'products/product_detail.html'
	context_object_name = 'product'

	def dispatch(self, request, *args, **kwargs):
		is_client_role = request.user.is_authenticated and getattr(request.user, 'role', '') == 'cliente'
		current_app = getattr(getattr(request, 'resolver_match', None), 'app_name', '')
		if is_client_role and current_app == 'products':
			return redirect('users:portal_cliente_producto', pk=kwargs.get('pk'))
		return super().dispatch(request, *args, **kwargs)

	def get_queryset(self):
		return Producto.objects.select_related('categoria').filter(activo=True)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		is_client_role = self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'cliente'
		if is_client_role:
			context['catalog_url_name'] = 'users:portal_cliente_catalogo'
			context['product_detail_url_name'] = 'users:portal_cliente_producto'
		else:
			context['catalog_url_name'] = 'products:product_list'
			context['product_detail_url_name'] = 'products:product_detail'
		context['related_products'] = (
			Producto.objects.filter(
				categoria=self.object.categoria,
				activo=True,
			)
			.exclude(pk=self.object.pk)
			.order_by('-destacado', '-fecha_creacion')[:4]
		)
		return context
