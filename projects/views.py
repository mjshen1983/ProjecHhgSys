from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.urls import reverse
from urllib.parse import quote

from .models import Project
from .forms import ProjectForm
from app.models import AppUser
from app.utils import build_base_context
from tasks.models import Task
from django.db.models import Exists, OuterRef, Count, Q
from attachments.models import Attachment


def _require_login(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('login')
    session_ctx = build_base_context(request)
    session_ctx['user_id'] = user_id
    return session_ctx, None


def project_list(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    # Annotate each project with a boolean indicating whether it has attachments.
    attachment_qs = Attachment.objects.filter(project=OuterRef('pk'))
    projects = (
        Project.objects.select_related('owner')
        .annotate(
            has_attachments=Exists(attachment_qs),
            open_tasks=Count('task', filter=~Q(task__status='done'))
        )
        .order_by('-updated_at')
    )
    context = {**session_ctx, 'projects': projects}
    return render(request, 'projects/list.html', context)


def project_detail(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    project = get_object_or_404(Project.objects.select_related('owner'), pk=pk)
    tasks = Task.objects.filter(project=project).select_related('assignee').order_by('-updated_at')
    current_path = request.get_full_path()
    create_task_url = f"{reverse('project_task_create', args=[project.id])}?next={quote(current_path)}"
    context = {
        **session_ctx,
        'project': project,
        'tasks': tasks,
        'current_path': current_path,
        'create_task_url': create_task_url,
    }
    return render(request, 'projects/detail.html', context)


def project_create(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_projects'):
        messages.error(request, '没有权限创建项目')
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            if not project.owner_id:
                project.owner = AppUser.objects.get(pk=session_ctx['user_id'])
            project.save()
            messages.success(request, '项目创建成功')
            return redirect('project_list')
    else:
        current_user = AppUser.objects.filter(pk=session_ctx['user_id']).first()
        form = ProjectForm(initial={'owner': current_user})
    context = {**session_ctx, 'form': form}
    return render(request, 'projects/form.html', context)


def project_update(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_projects'):
        messages.error(request, '没有权限编辑项目')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            # Prevent marking project as completed if it still has unfinished tasks
            new_status = form.cleaned_data.get('status')
            if new_status == 'completed':
                unfinished_exists = Task.objects.filter(project=project).exclude(status='done').exists()
                if unfinished_exists:
                    form.add_error('status', '项目下还有未完成的任务，无法转为“已完成”')
                    # fall through to render form with error
                else:
                    form.save()
                    messages.success(request, '项目已更新')
                    return redirect('project_list')
            else:
                form.save()
                messages.success(request, '项目已更新')
                return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    context = {**session_ctx, 'form': form}
    return render(request, 'projects/form.html', context)


def project_delete(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_projects'):
        messages.error(request, '没有权限删除项目')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, '项目已删除')
        return redirect('project_list')
    messages.error(request, '非法请求')
    return redirect('project_list')
