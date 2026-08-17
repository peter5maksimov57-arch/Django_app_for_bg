from django.contrib import admin
from django.urls import path, re_path
from main import views

urlpatterns = [
    path('', views.index),
    path('registration/', views.registration, name='registration'),
    path('registration/reg_code/', views.reg_code, name='reg_code'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('password_reset/res_code/', views.res_code, name='res_code'),
    path('password_reset/res_code/new_pas/', views.new_pas, name='new_pas')
]