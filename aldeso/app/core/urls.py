from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView   # простейший вариант

# noinspection PyUnresolvedReferences
from products.views import catalog, product_detail

urlpatterns = [
    path("", include("contents.urls")),
    path("product/<slug:slug>/", product_detail, name="product-detail"),
    path("catalog/<slug:category_slug>/", catalog, name="catalog-by-slug"),
    path('admin/', admin.site.urls),
    path('api/', include('products.urls', namespace='products')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)