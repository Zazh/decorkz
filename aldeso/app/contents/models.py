# contents/models.py
from symtable import Class

from django.db import models


class HomePage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    subtitle = models.CharField("Подзаголовок", max_length=255, blank=True)
    seo_title = models.CharField("SEO Title", max_length=255, blank=True)
    seo_description = models.TextField("SEO Description", blank=True)

    def __str__(self):
        return "Главная страница"

    class Meta:
        verbose_name = "Главная страница"
        verbose_name_plural = "Главная страница"


class Contact(models.Model):
    name = models.CharField("Название контакта", max_length=100)
    value = models.CharField("Значение", max_length=255)
    link = models.CharField("Ссылка", max_length=255, default="Nulle")
    order = models.PositiveIntegerField(default=0)  # Новое поле для порядка

    def __str__(self):
        return f"{self.name}: {self.value}"

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        ordering = ["order", "name"]

class Document(models.Model):
    DOC_TYPES = [
        ('privacy', 'Политика конфиденциальности'),
        ('cookies', 'Политика куки'),
        # Можно добавить еще
    ]
    doc_type = models.CharField("Тип документа", max_length=20, choices=DOC_TYPES, unique=True)
    title = models.CharField("Заголовок", max_length=255)
    content = models.TextField("Текст документа")

    def __str__(self):
        return self.get_doc_type_display()

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"