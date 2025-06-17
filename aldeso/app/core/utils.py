import os
import uuid
from slugify import slugify as _slugify

# ────────── единый slugify ──────────
def slug(text: str, *, max_len: int = 255) -> str:
    return _slugify(text, lowercase=True, max_length=max_len, separator='-') or "item"

def unique_slug(instance, text, *, model, field_name="slug", max_len=255):
    base = slug(text, max_len=max_len)
    candidate = base
    counter = 1
    while model.objects.exclude(pk=getattr(instance, "pk", None)).filter(**{field_name: candidate}).exists():
        counter += 1
        candidate = f"{base}-{counter}"
    return candidate

# ─────────── upload path ────────────
def product_image_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    product_slug = slug(instance.product.title)
    unique = uuid.uuid4().hex[:8]
    fname = f"{product_slug}-{unique}.{ext}"
    return os.path.join("product_images", product_slug, fname)

def category_image_upload_path(instance, filename):
    """ media/category_images/<slug>/uuid.ext """
    import uuid, os
    ext = filename.split('.')[-1]
    name = f"{instance.slug}-{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("category_images", instance.slug, name)