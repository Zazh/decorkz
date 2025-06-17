# contents/views.py
from django.shortcuts import render, get_object_or_404
from .models import HomePage, Contact, Document

def home_view(request):
    homepage = HomePage.objects.first()  # предполагаем, что одна запись
    contacts = Contact.objects.all()

    context = {
        "homepage": homepage,
        "contacts": contacts,
    }
    return render(request, "home.html", context)

def privacy_view(request):
    doc = get_object_or_404(Document, doc_type="privacy")
    return render(request, "documents/privacy.html", {"document": doc})

def cookies_view(request):
    doc = get_object_or_404(Document, doc_type="cookies")
    return render(request, "documents/cookies.html", {"document": doc})