from django.db import models
from django.utils.safestring import mark_safe
from easy_thumbnails.files import get_thumbnailer
from image_cropping import ImageRatioField
from django.core.exceptions import ValidationError

from decimal import Decimal, InvalidOperation
import random
import string

# noinspection PyUnresolvedReferences
from core.utils import slug, unique_slug, product_image_upload_path, category_image_upload_path

# ---- CATEGORY -----------------------------------------------------------
class ProductCategory(models.Model):
    title  = models.CharField("Название категории", max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True,
                               related_name="children", on_delete=models.CASCADE)
    slug   = models.SlugField(unique=True, blank=True)

    # ───── NEW ─────
    image    = models.ImageField("Изображение", blank=True,
                                 upload_to=category_image_upload_path)
    cropping = ImageRatioField("image", "600x600", allow_fullsize=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title, model=ProductCategory)
        super().save(*args, **kwargs)

        # после обычного save прогреваем thumbnail-ы
        if self.image and self.cropping:
            t = get_thumbnailer(self.image)
            t['default']   # 600×600, crop = self.cropping
            t['preview']   # 320×320, crop = False

    # маленькая утилита
    def thumb(self, alias="preview"):
        if not self.image:
            return ""
        try:
            return get_thumbnailer(self.image)[alias].url
        except Exception:
            # Файла нет — просто возвращаем пусто, чтобы не падало
            return ""

    # чтобы видеть превью в админке
    def thumbnail_preview(self):
        try:
            url = self.thumb("preview")
            if url:
                return mark_safe(f'<img src="{url}" style="height:80px">')
        except Exception:
            pass
        return "—"

    thumbnail_preview.short_description = "Превью"

    def __str__(self):
        return self.title

# ---- ATTRIBUTE ----------------------------------------------------------
class Attribute(models.Model):
    VALUE_TYPES = [
        ("str",     "Строка"),
        ("int",     "Целое число"),
        ("decimal", "Десятичное"),
        ("bool",    "Да / Нет"),
    ]

    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    value_type = models.CharField("Тип", max_length=10, choices=VALUE_TYPES, default="str")

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, model=Attribute)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ---- PRODUCT ------------------------------------------------------------
class Product(models.Model):
    title = models.CharField("Название товара", max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(ProductCategory, related_name="products",
                                 on_delete=models.PROTECT)
    # description = models.TextField(blank=True)
    description = models.TextField(blank=True)


    sku = models.CharField(unique=True, blank=True, max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["title"]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def save(self, *args, **kwargs):
        old_slug = self.slug
        if not self.slug:
            self.slug = unique_slug(self, self.title, model=Product)
            
        # Генерация SKU если он не задан
        if not self.sku:
            while True:
                # Генерируем случайный 8-значный код
                random_sku = ''.join(random.choices(string.digits, k=8))
                # Проверяем, что такого SKU еще нет в базе
                if not Product.objects.filter(sku=random_sku).exists():
                    self.sku = random_sku
                    break
                
        super().save(*args, **kwargs)

        # переименование картинок при смене slug
        if old_slug and old_slug != self.slug:
            for img in self.images.all():
                img.rename_file(self.slug)

    def __str__(self):
        return self.title

# ---- PRODUCT IMAGE ------------------------------------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images",
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_image_upload_path)
    cropping = ImageRatioField("image", "600x600", allow_fullsize=True)
    is_main = models.BooleanField("Главное", default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_main", "id"]
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"

    # ---------- служебные -------------------------------------------------
    def thumb(self, alias="default"):
        return get_thumbnailer(self.image)[alias].url

    def rename_file(self, new_product_slug: str):
        if not self.image:
            return
        from django.core.files.storage import default_storage
        import os, uuid
        ext = self.image.name.split('.')[-1]
        new_name = f"{new_product_slug}-{uuid.uuid4().hex[:8]}.{ext}"
        new_path = os.path.join("product_images", new_product_slug, new_name)
        if default_storage.exists(self.image.name):
            with default_storage.open(self.image.name, "rb") as f:
                default_storage.save(new_path, f)
            default_storage.delete(self.image.name)
        get_thumbnailer(self.image).clear()
        self.image.name = new_path
        super().save(update_fields=["image"])

    # ---------- admin preview --------------------------------------------
    def thumbnail_preview(self):
        return mark_safe(f'<img src="{self.thumb("preview")}" style="height:80px">')
    thumbnail_preview.short_description = "Превью"

    def save(self, *args, **kwargs):
        # 1. сохраняем сам файл / модель
        super().save(*args, **kwargs)

        # 2. если координаты уже заданы – прогреваем алиасы
        if self.cropping:
            thumb = get_thumbnailer(self.image)
            thumb['default']  # 600×600, crop = self.cropping
            thumb['preview']  # 320×320, crop = False

    def __str__(self):
        return f"{self.product} | {self.pk}"

# ---- PRODUCT ↔ ATTRIBUTE VALUE -----------------------------------------
class ProductAttributeValue(models.Model):
    product   = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey("Attribute", on_delete=models.PROTECT)

    value     = models.CharField("Значение", max_length=255)

    class Meta:
        unique_together = ("product", "attribute")
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товара"

    # ───── валидация ─────
    def clean(self):
        if not self.attribute:        # нужен при сохранении через shell
            return

        vt = self.attribute.value_type   # str / int / decimal / bool
        v  = (self.value or "").strip()

        if vt == "int":
            if not v.isdigit():
                raise ValidationError({"value": "Ожидается целое число"})
            # нормализуем
            self.value = str(int(v))

        elif vt == "decimal":
            try:
                # «3,5» → «3.5», далее проверка
                d = Decimal(v.replace(",", "."))
            except (InvalidOperation, ValueError):
                raise ValidationError({"value": "Ожидается десятичное число"})
            # нормализуем до строки: '3.50' → '3.5'
            self.value = str(d.normalize())

        elif vt == "bool":
            norm = v.lower()
            if norm in ("да", "yes", "true", "1"):
                self.value = "Да"
            elif norm in ("нет", "no", "false", "0"):
                self.value = "Нет"
            else:
                raise ValidationError({"value": "Введите Да / Нет"})

    def save(self, *args, **kwargs):
        self.full_clean()           # вызывает clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"