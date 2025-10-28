from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_items, name='knowledge_list'),
    path('create/', views.create_item, name='knowledge_create'),
    path('<int:pk>/', views.view_item, name='knowledge_detail'),
    path('<int:pk>/delete/', views.delete_item, name='knowledge_delete'),
    path('<int:pk>/attachment/<int:aid>/', views.attachment_serve, name='knowledge_attachment_serve'),
]
