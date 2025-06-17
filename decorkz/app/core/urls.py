from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from products.views import catalog, product_detail, catalog_root
from blog.views import home



urlpatterns = [
    path('', home, name='home'),
    path("product/<slug:slug>/", product_detail, name="product-detail"),
    path("catalog/<slug:category_slug>/", catalog, name="catalog-by-slug"),
    path("catalog/", catalog_root, name="catalog"),
    path('admin/', admin.site.urls),
    path('api/', include('products.urls', namespace='products')),
    path('blog/', include('blog.urls')),
    path('', include('contacts.urls')),  # Контакты

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
