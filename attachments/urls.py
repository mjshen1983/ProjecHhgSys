from django.urls import path
from . import views

urlpatterns = [
    path('', views.attachment_list, name='attachment_list'),
    path('project/<int:project_id>/', views.project_attachment_list, name='attachment_project_list'),
    path('project/<int:project_id>/upload/', views.project_attachment_upload, name='attachment_project_upload'),
    path('project/<int:project_id>/<int:pk>/delete/', views.project_attachment_delete, name='attachment_project_delete'),
]