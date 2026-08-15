from django.contrib import admin
from django.urls import path, re_path
from main import views

urlpatterns = [
    path('', views.index),
    path('registration/', views.registration, name='registration'),
    path('registration/reg_code/', views.reg_code, name='reg_code'),
]