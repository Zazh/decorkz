# contents/urls.py
from django.urls import path
from .views import home_view, privacy_view, cookies_view

app_name = "contents"

urlpatterns = [
    path("", home_view, name="home"),
    path("documents/privacy/", privacy_view, name="privacy"),
    path("documents/cookies/", cookies_view, name="cookies"),
]