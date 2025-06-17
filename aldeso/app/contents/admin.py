# contents/admin.py
from django.contrib import admin
from .models import HomePage, Contact, Document

@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle")

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "link", "order")
    list_editable = ("order",)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "title")