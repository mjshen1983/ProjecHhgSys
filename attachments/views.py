from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Attachment
from projects.models import Project
from app.models import AppUser


def attachment_list(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    attachments = Attachment.objects.select_related('uploaded_by', 'project').order_by('-created_at')
    context = {
        'attachments': attachments,
        'display_name': request.session.get('display_name'),
    }
    return render(request, 'attachments/list.html', context)


def project_attachment_list(request, project_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    attachments = Attachment.objects.filter(project=project).select_related('uploaded_by').order_by('-created_at')
    context = {
        'project': project,
        'attachments': attachments,
        'display_name': request.session.get('display_name'),
    }
    return render(request, 'attachments/projects/list.html', context)


def project_attachment_upload(request, project_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    name_value = ''
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        name_value = name
        file_obj = request.FILES.get('file')
        if not name:
            messages.error(request, '请填写附件名称')
        elif not file_obj:
            messages.error(request, '请选择要上传的文件')
        else:
            Attachment.objects.create(
                name=name,
                file=file_obj,
                uploaded_by=AppUser.objects.get(pk=user_id),
                project=project,
                content_object=project,
            )
            messages.success(request, '项目文件上传成功')
            return redirect('attachment_project_list', project_id=project.id)
    return render(request, 'attachments/projects/upload.html', {
        'project': project,
        'display_name': request.session.get('display_name'),
        'name_value': name_value,
    })


def project_attachment_delete(request, project_id, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    attachment = get_object_or_404(Attachment, pk=pk, project=project)
    if request.method == 'POST':
        storage = attachment.file.storage
        file_path = attachment.file.name
        attachment.delete()
        if storage.exists(file_path):
            storage.delete(file_path)
        messages.success(request, '附件已删除')
    else:
        messages.error(request, '非法请求')
    return redirect('attachment_project_list', project_id=project.id)