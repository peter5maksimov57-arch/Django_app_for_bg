from django.contrib import admin
from django.urls import path, re_path
from main import views

urlpatterns = [
    path('', views.index),
    re_path(r'^about', views.about),
    re_path(r'^contact', views.contact),
]
