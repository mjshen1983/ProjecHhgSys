from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count, OuterRef, Subquery
from projects.models import Department
from app.models import UserProfile

from .models import KnowledgeItem, KnowledgeAttachment
from .forms import KnowledgeItemForm
from app.utils import build_base_context
from django.conf import settings
from app.models import AppUser
from django.views.decorators.http import require_POST


def _require_login(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('login')
    session_ctx = build_base_context(request)
    session_ctx['user_id'] = user_id
    return session_ctx, None


def visible_items_for_user(user_id):
    q = Q(visibility=KnowledgeItem.VISIBILITY_PUBLIC)
    # read department from UserProfile (projects.Department FK)
    profile = UserProfile.objects.select_related('department').filter(user_id=user_id).first()
    user_dept_name = None
    if profile and profile.department:
        user_dept_name = profile.department.name
    if user_dept_name:
        q |= Q(visibility=KnowledgeItem.VISIBILITY_DEPT, department=user_dept_name)
    user = AppUser.objects.filter(pk=user_id).first()
    if user:
        q |= Q(visibility=KnowledgeItem.VISIBILITY_PRIVATE, owner=user)
    return KnowledgeItem.objects.filter(q)


def list_items(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    q = request.GET.get('q')
    # annotate attachment counts and prefetch attachments to avoid N+1 queries
    # also annotate uploader's department name via a subquery on UserProfile -> Department
    profile_qs = UserProfile.objects.filter(user_id=OuterRef('owner_id')).values('department__name')[:1]
    items = visible_items_for_user(session_ctx['user_id']).annotate(
        attachments_count=Count('attachments'),
        department_name=Subquery(profile_qs),
    ).prefetch_related('attachments')
    if q:
        items = items.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(tags__icontains=q))
    context = {**session_ctx, 'items': items}
    return render(request, 'knowledge/list.html', context)


def view_item(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    item = get_object_or_404(KnowledgeItem, pk=pk)
    # permission check
    if item.visibility == KnowledgeItem.VISIBILITY_PRIVATE and item.owner_id != session_ctx['user_id']:
        messages.error(request, '无权查看此条目')
        return redirect('knowledge_list')
    if item.visibility == KnowledgeItem.VISIBILITY_DEPT:
        profile = UserProfile.objects.select_related('department').filter(user_id=session_ctx['user_id']).first()
        user_dept_name = None
        if profile and profile.department:
            user_dept_name = profile.department.name
        if user_dept_name != item.department and item.owner_id != session_ctx['user_id']:
            messages.error(request, '无权查看此条目')
            return redirect('knowledge_list')
    context = {**session_ctx, 'item': item}
    return render(request, 'knowledge/detail.html', context)


def create_item(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        form = KnowledgeItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner_id = session_ctx['user_id']
            # if department not set, try user's department
            if not item.department:
                profile = UserProfile.objects.select_related('department').filter(user_id=session_ctx['user_id']).first()
                if profile and profile.department:
                    item.department = profile.department.name
            item.save()
            # handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                att = KnowledgeAttachment(item=item, file=f, filename=f.name)
                att.save()
            messages.success(request, '知识条目已保存')
            return redirect('knowledge_list')
    else:
        form = KnowledgeItemForm()
    context = {**session_ctx, 'form': form}
    return render(request, 'knowledge/form.html', context)


@require_POST
def delete_item(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    item = get_object_or_404(KnowledgeItem, pk=pk)
    # only owner can delete
    if item.owner_id != session_ctx['user_id']:
        messages.error(request, '无权删除此条目')
        return redirect('knowledge_list')
    # delete attachments first (FileFields will be removed by model delete, but remove files if needed)
    for att in item.attachments.all():
        try:
            att.file.delete(save=False)
        except Exception:
            pass
    item.delete()
    messages.success(request, '条目已删除')
    return redirect('knowledge_list')
