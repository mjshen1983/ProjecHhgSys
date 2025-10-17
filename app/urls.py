from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('main/', views.main_view, name='main'),
    path('logout/', views.logout_view, name='logout'),
    path('change_password/', views.change_password_view, name='change_password'),
]
