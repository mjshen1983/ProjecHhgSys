from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Attachment
from projects.models import Project
from app.models import AppUser
from app.utils import build_base_context


def attachment_list(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    session_ctx = build_base_context(request)
    attachments = Attachment.objects.select_related('uploaded_by', 'project').order_by('-created_at')
    context = {
        **session_ctx,
        'attachments': attachments,
    }
    return render(request, 'attachments/list.html', context)


def project_attachment_list(request, project_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    session_ctx = build_base_context(request)
    attachments = Attachment.objects.filter(project=project).select_related('uploaded_by').order_by('-created_at')
    context = {
        **session_ctx,
        'project': project,
        'attachments': attachments,
    }
    return render(request, 'attachments/projects/list.html', context)


def project_attachment_upload(request, project_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    session_ctx = build_base_context(request)
    if not session_ctx.get('can_manage_projects'):
        messages.error(request, '没有权限上传附件')
        return redirect('attachment_project_list', project_id=project.id)
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
        **session_ctx,
        'project': project,
        'name_value': name_value,
    })


def project_attachment_delete(request, project_id, pk):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    project = get_object_or_404(Project, pk=project_id)
    session_ctx = build_base_context(request)
    if not session_ctx.get('can_manage_projects'):
        messages.error(request, '没有权限删除附件')
        return redirect('attachment_project_list', project_id=project.id)
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