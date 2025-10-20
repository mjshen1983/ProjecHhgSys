from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('main/', views.main_view, name='main'),
    path('logout/', views.logout_view, name='logout'),
    path('change_password/', views.change_password_view, name='change_password'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('permissions/', views.permission_group_list, name='permission_group_list'),
    path('permissions/create/', views.permission_group_create, name='permission_group_create'),
    path('permissions/<int:pk>/edit/', views.permission_group_update, name='permission_group_update'),
    path('permissions/<int:pk>/delete/', views.permission_group_delete, name='permission_group_delete'),
]
