# products/management/commands/regenerate_thumbnails.py
from django.core.management.base import BaseCommand
from easy_thumbnails.files import get_thumbnailer
from products.models import ProductImage
from django.conf import settings

class Command(BaseCommand):
    help = "Re-generate all thumbnails with new quality settings"

    def handle(self, *args, **options):
        images = ProductImage.objects.all()
        total = images.count()
        self.stdout.write(f"Обрабатываем {total} изображений…")
        for i, img in enumerate(images, 1):
            thumb = get_thumbnailer(img.image)
            # удаляем старые миниатюры
            thumb.delete_thumbnails()
            # прогреваем новые:
            thumb.get_thumbnail(settings.THUMBNAIL_ALIASES[""]["default"])
            thumb.get_thumbnail(settings.THUMBNAIL_ALIASES[""]["preview"])
            self.stdout.write(f"[{i}/{total}] {img.image.name}")
        self.stdout.write(self.style.SUCCESS("Готово!"))