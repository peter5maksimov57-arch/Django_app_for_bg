from django.contrib import admin
from django.urls import path, re_path
from main import views

urlpatterns = [
    path('', views.index),
    path('registration/', views.registration, name='registration'),
    path('registration/reg_code/', views.reg_code, name='reg_code'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('password_reset/res_code/', views.res_code, name='res_code'),
    path('password_reset/res_code/new_pas/', views.new_pas, name='new_pas'),
    path('main_page', views.main_page, name='main_page'),
    path('logout/', views.logout_view, name='logout'),
    path('main_page/create_tr/', views.create_tr, name='create_tr'),
    # path('main_page/view_transactions/', views.view_transactions, name="view_transactions")
]