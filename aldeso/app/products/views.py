# views.py
from rest_framework import filters, viewsets
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, OuterRef

from .filters import ProductFilter
from .filters_config import FILTER_CONFIG

from .services import StandardResultsSetPagination
from .models import Product, ProductCategory, ProductAttributeValue, Attribute
from .serializers import ProductSerializer, CategorySerializer
from django_filters.rest_framework import DjangoFilterBackend

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects
        .select_related("category")
        .prefetch_related(
            "images",                     # галерея
            "attribute_values__attribute" # ← правильный путь
        )
    )
    lookup_field = "slug"
    serializer_class = ProductSerializer
    filter_backends   = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class  = ProductFilter
    # ➊ Фильтры django-filter
    filterset_fields = {
        "category__slug": ["exact"],
    }

    # ➋ Полнотекстовый поиск
    search_fields = ["title", "description", "sku"]

    # ➌ Сортировка
    ordering_fields = ["price", "title"]

    # ➍ Стандартная пагинация (если нужна)
    pagination_class = StandardResultsSetPagination



class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer

# --- Получаем slug-и атрибутов ---
def get_attr_slug(attr_name):
    try:
        return Attribute.objects.only("slug").get(name__iexact=attr_name).slug
    except Attribute.DoesNotExist:
        return None

def apply_range_filters(queryset, field, values, attr_slug=None):
    """
    Фильтрация по диапазонам с поддержкой OR для чекбоксов.
    - field: 'price', 'length', 'width', 'height'
    - values: ['0-5000', '10000-', ...]
    - attr_slug: slug атрибута (для length/width/height)
    """
    if not values:
        return queryset

    q_filter = Q()
    for val in values:
        min_val, max_val = None, None
        parts = val.split('-')
        if len(parts) == 2:
            min_val = parts[0] if parts[0] else None
            max_val = parts[1] if parts[1] else None
        elif parts:
            min_val = parts[0]

        if field == 'price':
            cond = Q()
            if min_val:
                cond &= Q(price__gte=float(min_val))
            if max_val:
                cond &= Q(price__lte=float(max_val))
            q_filter |= cond
        else:
            subq = ProductAttributeValue.objects.filter(
                product=OuterRef('pk'),
                attribute__slug=attr_slug
            )
            if min_val:
                subq = subq.filter(value__gte=min_val)
            if max_val:
                subq = subq.filter(value__lte=max_val)
            q_filter |= Q(pk__in=subq.values('product_id'))

    return queryset.filter(q_filter)

def format_number(value):
    try:
        return ('{:.2f}'.format(float(value))).rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)

def catalog(request, category_slug=None):
    category = None
    categories = list(ProductCategory.objects.values("id", "title", "slug").order_by("title"))
    seo_title = "Каталог товаров aldeso.kz"
    seo_description = "Aluminium decorative solution - производим алюминиевые декоративные решения, карнизы, плинтусы, рейки"
    allowed_orderings = ["title", "-title", "price", "-price"]
    filter_config = FILTER_CONFIG.get(category_slug, FILTER_CONFIG['default'])

    products = []
    col1, col2, col3 = [], [], []
    attribute_values = {}
    vid_values = []

    # Инициализация списков фильтров заранее
    price_values = request.GET.getlist('price') if category_slug else []
    length_values = request.GET.getlist('length') if category_slug else []
    width_values = request.GET.getlist('width') if category_slug else []
    height_values = request.GET.getlist('height') if category_slug else []
    vid_selected = request.GET.getlist('vid') if category_slug else []
    podsvetka_selected = request.GET.getlist('podsvetka') if category_slug else []

    if category_slug:
        category = ProductCategory.objects.filter(slug=category_slug).first()
        if not category:
            category = None

        products_qs = Product.objects.filter(category=category).prefetch_related(
            'images', 'attribute_values__attribute'
        )

        # --- Получаем уникальные значения атрибутов для фильтров по категории ---
        for attr_name in filter_config.get('attributes', []):
            values = ProductAttributeValue.objects.filter(
                attribute__name__iexact=attr_name,
                product__category=category
            ).values_list('value', flat=True).distinct()
            attribute_values[attr_name] = list(values)

        # --- Получаем слаги атрибутов ---
        def get_attr_slug(attr_name):
            try:
                return Attribute.objects.only("slug").get(name__iexact=attr_name).slug
            except Attribute.DoesNotExist:
                return None

        length_slug = get_attr_slug('длина')
        width_slug = get_attr_slug('ширина')
        height_slug = get_attr_slug('высота')

        # --- Применяем фильтры ---
        products_qs = apply_range_filters(products_qs, 'price', price_values)
        products_qs = apply_range_filters(products_qs, 'length', length_values, length_slug)
        products_qs = apply_range_filters(products_qs, 'width', width_values, width_slug)
        products_qs = apply_range_filters(products_qs, 'height', height_values, height_slug)
        # --- Фильтр по "Вид" ---
        if 'вид' in filter_config.get('attributes', []) and vid_selected:
            products_qs = products_qs.filter(
                attribute_values__attribute__name__iexact='вид',
                attribute_values__value__in=vid_selected
            ).distinct()

        if 'подсветка' in filter_config.get('attributes', []) and podsvetka_selected:
            products_qs = products_qs.filter(
                attribute_values__attribute__name__iexact='подсветка',
                attribute_values__value__in=podsvetka_selected
            ).distinct()

        # --- Сортировка ---
        ordering = request.GET.get("ordering")
        if ordering in allowed_orderings:
            products_qs = products_qs.order_by(ordering)
        else:
            products_qs = products_qs.order_by('id')


        products = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "price": int(p.price),
                "image": p.images.first().thumb("preview") if p.images.exists() else "",
                "alt": f"{p.category.title} {p.title}",
                "title_attr": f"{p.category.title} {p.title}",
                "size": " × ".join([
                    format_number(next((a.value for a in p.attribute_values.all() if a.attribute.name.lower() == 'ширина'), '')),
                    format_number(next((a.value for a in p.attribute_values.all() if a.attribute.name.lower() == 'высота'), '')),
                    format_number(next((a.value for a in p.attribute_values.all() if a.attribute.name.lower() == 'длина'), '')),
                ]),
                "type": next((a.value for a in p.attribute_values.all() if a.attribute.name.lower() == 'вид'), 'не указан'),
            }
            for p in products_qs
        ]

        col1, col2, col3 = products[::3], products[1::3], products[2::3]

        seo_title = f"{category.title} — Купить по лучшей цене"
        seo_description = f"{category.title}: широкий ассортимент по доступным ценам."

        # Для шаблона, чтобы проще было сравнивать выбранные значения
        vid_values = attribute_values.get('вид', [])

    context = {
        "categories": categories,
        "products": products,
        "col1": col1,
        "col2": col2,
        "col3": col3,
        "current_category": category,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "attribute_values": attribute_values,
        "filter_config": filter_config,
        "length_values": length_values,
        "width_values": width_values,
        "height_values": height_values,
        "price_values": price_values,
        "vid_selected": vid_selected,
        "vid_values": vid_values,
        "podsvetka_selected": podsvetka_selected,
        "podsvetka_values": attribute_values.get('подсветка', []),
    }
    return render(request, "catalog.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Загружаем все связанные атрибуты одной строкой:
    attributes = product.attribute_values.select_related('attribute')

    # Сортируем их по привычному порядку (чтобы всегда было В, Ш, Д, потом остальные):
    attrs_map = {a.attribute.name.lower(): a.value for a in attributes}

    # Формируем структуру для шаблона
    sizes = {
        'height': format_number(attrs_map.get('высота')),
        'width': format_number(attrs_map.get('ширина')),
        'length': format_number(attrs_map.get('длина')),
    }
    vid = attrs_map.get('вид')
    podsvetka = attrs_map.get('подсветка')

    # Выводим остальные (не размеры, не вид, не подсветка) как "прочие характеристики":
    other_attributes = [
        {'name': a.attribute.name, 'value': a.value}
        for a in attributes
        if a.attribute.name.lower() not in ['высота', 'ширина', 'длина', 'вид', 'подсветка']
    ]

    seo_title = f"{product.title} — купить по лучшей цене"
    seo_description = (product.description or f"Купить {product.title} по доступной цене. Характеристики, фото, доставка.")

    context = {
        "product": product,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "sizes": sizes,
        "vid": vid,
        "podsvetka": podsvetka,
        "other_attributes": other_attributes,
    }
    return render(request, "product.html", context)