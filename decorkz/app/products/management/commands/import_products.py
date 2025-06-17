from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from decimal import Decimal, InvalidOperation
import csv
import os
import glob

from products.models import ProductCategory, Product, ProductImage, Attribute, ProductAttributeValue
from core.utils import unique_slug, slug as custom_slugify


class Command(BaseCommand):
    help = "Импорт продуктов из CSV-файла, создание подкатегорий, изображений и атрибутов."

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV-файлу с данными, собранными парсером')
        parser.add_argument('--parent', type=str, required=True, help='Slug родительской категории (обязателен)')
        parser.add_argument('--images-root', type=str, dest='images_root', default=None,
                            help='Абсолютный путь к корневой папке с изображениями продуктов')
        parser.add_argument('--default-attr-type', type=str, dest='default_attr_type', default='str',
                            help='Тип создаваемых атрибутов по умолчанию ("str", "int", "decimal", "bool")')

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        parent_slug = options['parent']
        images_root = options.get('images_root')
        default_attr_type = options.get('default_attr_type', 'str')

        if not os.path.isfile(csv_path):
            raise CommandError(f"CSV файл не найден: {csv_path}")

        try:
            parent_category = ProductCategory.objects.get(slug=parent_slug)
        except ProductCategory.DoesNotExist:
            raise CommandError(f"Родительская категория с slug '{parent_slug}' не найдена")

        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames is None:
                raise CommandError("CSV файл пустой или не содержит заголовков")

            for row in reader:
                title = (row.get('title') or row.get('название') or '').strip()
                category_name = (row.get('category') or row.get('категория') or '').strip()
                price_str = (row.get('price') or row.get('цена') or '').strip()
                description = (row.get('description') or row.get('описание') or '').strip()
                sku = (row.get('sku') or row.get('артикул') or '').strip()

                if not sku:
                    self.stdout.write(self.style.WARNING(f"Строка пропущена: отсутствует артикул товара (название: {title or 'не указано'})"))
                    continue

                if not category_name:
                    self.stdout.write(self.style.WARNING(f"Строка пропущена: не указана категория (товар: {title or sku})"))
                    continue

                subcat_slug = custom_slugify(category_name)
                subcategory, subcat_created = ProductCategory.objects.get_or_create(
                    parent=parent_category, slug=subcat_slug, defaults={'title': category_name})
                if subcat_created:
                    self.stdout.write(self.style.SUCCESS(f"Создана новая подкатегория '{category_name}' (slug: {subcat_slug})"))

                base_slug = custom_slugify(title) if title else sku
                unique_product_slug = unique_slug(None, base_slug, model=Product)

                product_data = {
                    'title': title,
                    'slug': unique_product_slug,
                    'category': subcategory,
                    'sku': sku
                }

                if price_str:
                    price_str = price_str.replace(',', '.')
                    try:
                        product_data['price'] = Decimal(price_str)
                    except InvalidOperation:
                        self.stdout.write(self.style.WARNING(f"Цена '{price_str}' для товара '{title}' не распознана"))

                if description:
                    product_data['description'] = description

                product, created = Product.objects.get_or_create(sku=sku, defaults=product_data)
                if not created:
                    self.stdout.write(self.style.WARNING(f"Товар с артикулом '{sku}' уже существует"))
                    continue

                self.stdout.write(self.style.SUCCESS(f"Создан товар: '{title}' (sku: {sku}, slug: {unique_product_slug})"))

                if images_root:
                    product_img_dir = os.path.join(images_root, sku)
                    if os.path.isdir(product_img_dir):
                        # Список всех файлов-картинок в папке
                        for image_path in sorted(glob.glob(os.path.join(product_img_dir, '*'))):
                            filename = os.path.basename(image_path)

                            # Получаем имя без расширения
                            name, ext = os.path.splitext(filename)
                            ext = ext.lower()
                            # Пропускаем если не картинка
                            if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
                                continue

                            # Пропускаем только main (без цифр), но загружаем main1, main2 и т.п.
                            if name.lower() == 'main':
                                continue

                            image_name = f"{sku}_{filename}"
                            with open(image_path, 'rb') as img_file:
                                product_image = ProductImage(product=product, is_main=False)
                                product_image.image.save(image_name, File(img_file), save=True)
                            self.stdout.write(self.style.SUCCESS(
                                f"Добавлено изображение '{filename}' для товара '{title}'"
                            ))

                for key, value in row.items():
                    if key.endswith('(значение)') and value:
                        attr_name = key[:-len('(значение)')].strip()
                        attribute, attr_created = Attribute.objects.get_or_create(
                            name=attr_name, defaults={'value_type': default_attr_type}
                        )
                        if attr_created:
                            self.stdout.write(self.style.SUCCESS(f"Создан атрибут '{attr_name}'"))

                        try:
                            ProductAttributeValue.objects.create(product=product, attribute=attribute,
                                                                 value=value.strip())
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f"Ошибка при создании атрибута '{attr_name}' для товара '{sku}' (value: '{value}'): {e}"
                            ))

