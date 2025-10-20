from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django import forms

from django.http import HttpResponseRedirect

from .models import Task
from .forms import TaskForm
from app.models import AppUser
from app.utils import build_base_context
from projects.models import Project


def _require_login(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('login')
    session_ctx = build_base_context(request)
    session_ctx['user_id'] = user_id
    return session_ctx, None


def task_list(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    tasks = Task.objects.select_related('project', 'assignee').order_by('-updated_at')
    context = {
        **session_ctx,
        'tasks': tasks,
        'task_list_url': reverse('task_list'),
    }
    return render(request, 'tasks/list.html', context)


def task_detail(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    task = get_object_or_404(Task.objects.select_related('project', 'assignee'), pk=pk)
    return_url = request.GET.get('next') or reverse('task_list')
    context = {
        **session_ctx,
        'task': task,
        'return_url': return_url,
    }
    return render(request, 'tasks/detail.html', context)


def task_create(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    task_list_url = reverse('task_list')
    next_url = request.GET.get('next') or request.POST.get('next') or task_list_url
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = AppUser.objects.get(pk=session_ctx['user_id'])
            task.save()
            messages.success(request, '任务创建成功')
            return HttpResponseRedirect(next_url)
    else:
        form = TaskForm()
    context = {
        **session_ctx,
        'form': form,
        'task_list_url': task_list_url,
        'next_url': next_url,
        'cancel_url': next_url,
    }
    return render(request, 'tasks/form.html', context)


def project_task_create(request, project_id):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    project = get_object_or_404(Project, pk=project_id)
    fallback_next = reverse('project_detail', args=[project.id])
    next_url = request.GET.get('next') or request.POST.get('next') or fallback_next
    task_list_url = reverse('task_list')
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = AppUser.objects.get(pk=session_ctx['user_id'])
            task.project = project
            task.save()
            messages.success(request, '任务创建成功')
            return HttpResponseRedirect(next_url)
    else:
        form = TaskForm(initial={'project': project})
    if 'project' in form.fields:
        form.fields['project'].queryset = Project.objects.filter(pk=project.id)
        form.fields['project'].initial = project
        form.fields['project'].widget = forms.HiddenInput()
    context = {
        **session_ctx,
        'form': form,
        'next_url': next_url,
        'project': project,
        'form_title': f"为 {project.name} 新建任务",
        'task_list_url': task_list_url,
        'cancel_url': next_url,
        'fixed_project': project,
    }
    return render(request, 'tasks/form.html', context)


def task_update(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    task = get_object_or_404(Task, pk=pk)
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('task_detail', args=[task.id])
    task_list_url = reverse('task_list')
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, '任务已更新')
            return HttpResponseRedirect(next_url)
    else:
        form = TaskForm(instance=task)
    context = {
        **session_ctx,
        'form': form,
        'task': task,
        'next_url': next_url,
        'form_title': '编辑任务',
        'task_list_url': task_list_url,
        'cancel_url': next_url,
    }
    return render(request, 'tasks/form.html', context)


def task_delete(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    task = get_object_or_404(Task, pk=pk)
    next_url = request.POST.get('next') or request.GET.get('next') or reverse('task_list')
    if request.method == 'POST':
        task.delete()
        messages.success(request, '任务已删除')
        return HttpResponseRedirect(next_url)
    messages.error(request, '非法请求')
    return HttpResponseRedirect(next_url)
