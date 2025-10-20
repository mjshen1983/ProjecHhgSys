import hashlib

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from .forms import UserCreateForm, UserUpdateForm, PermissionGroupForm
from .models import AppUser, PermissionGroup, UserProfile
from .utils import build_base_context
from projects.models import Project
from tasks.models import Task


PROTECTED_PERMISSION_CODES = {'admin', 'dept_manager', 'member'}


def _format_percent(value: float) -> str:
    return f"{value:.1f}".rstrip('0').rstrip('.')


def _build_status_stats(counts: dict[str, int], labels: dict[str, str]):
    total = sum(counts.values())
    if total == 0:
        return [], 0
    ordered_codes = list(labels.keys()) + [code for code in counts.keys() if code not in labels]
    stats = []
    for code in ordered_codes:
        count = counts.get(code)
        if not count:
            continue
        percent = count / total * 100
        percent_display = _format_percent(percent)
        stats.append({
            'code': code or 'unknown',
            'label': labels.get(code, code or '未定义'),
            'count': count,
            'percent': percent,
            'percent_display': percent_display,
            'percent_value': f"{percent:.2f}",
        })
    return stats, total


def _set_session_permissions(request, profile: UserProfile) -> None:
    group = profile.permission_group
    session = request.session
    session['permission_code'] = group.code
    session['can_manage_projects'] = bool(group.can_manage_projects)
    session['can_manage_tasks'] = bool(group.can_manage_tasks)
    session['can_manage_users'] = bool(group.can_manage_users)
    session['can_manage_permissions'] = bool(group.can_manage_permissions)
    session['can_view_all_tasks'] = bool(group.can_view_all_tasks or group.can_manage_tasks)
    session['can_edit_all_tasks'] = bool(group.can_edit_all_tasks or group.can_manage_tasks)
    session['department_id'] = profile.department_id
    session.modified = True


def _ensure_login(request, *, enforce_password_change: bool = False):
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('login')
    if enforce_password_change and request.session.get('force_password_reset'):
        messages.info(request, '请先修改初始密码。')
        return None, redirect('change_password')
    session_ctx = build_base_context(request)
    session_ctx['user_id'] = user_id
    return session_ctx, None


def _permission_denied(request, message: str = '没有权限执行该操作'):
    messages.error(request, message)
    return redirect('main')


def _get_default_permission_group() -> PermissionGroup:
    group, _ = PermissionGroup.objects.get_or_create(
        code='member',
        defaults={
            'name': '普通成员',
            'description': '默认基础权限',
            'can_manage_projects': False,
            'can_manage_tasks': False,
            'can_manage_users': False,
            'can_manage_permissions': False,
            'can_view_all_tasks': True,
            'can_edit_all_tasks': False,
        },
    )
    return group


def _password_matches(raw_password: str, stored_password: str) -> bool:
    """兼容旧系统的明文或简单散列密码格式。"""
    if not stored_password:
        return False
    if check_password(raw_password, stored_password):
        return True
    if raw_password == stored_password:
        return True
    password_bytes = raw_password.encode('utf-8')
    md5_hex = hashlib.md5(password_bytes).hexdigest()
    sha1_hex = hashlib.sha1(password_bytes).hexdigest()
    sha256_hex = hashlib.sha256(password_bytes).hexdigest()
    return stored_password in {md5_hex, sha1_hex, sha256_hex}


def _upgrade_password_hash(user: AppUser, raw_password: str) -> None:
    """若旧密码验证成功但未使用Django默认算法，则升级为安全哈希。"""
    if not user.password_hash.startswith('pbkdf2_'):
        user.password_hash = make_password(raw_password)
        user.save(update_fields=['password_hash'])

# 登录页面
def login_view(request):
    if request.session.get('user_id'):
        return redirect('main')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = AppUser.objects.get(username=username)
            if _password_matches(password, user.password_hash):
                _upgrade_password_hash(user, password)
                request.session['user_id'] = user.id
                request.session['display_name'] = user.display_name or user.username
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'permission_group': _get_default_permission_group(),
                        'is_active': True,
                    },
                )
                if not profile.is_active:
                    request.session.flush()
                    messages.error(request, '账户已被停用，请联系管理员')
                    return render(request, 'login.html')
                if not profile.permission_group_id:
                    profile.permission_group = _get_default_permission_group()
                    profile.save(update_fields=['permission_group'])
                _set_session_permissions(request, profile)
                if getattr(user, 'needs_password_reset', False):
                    request.session['force_password_reset'] = True
                    messages.info(request, '首次登录需先修改密码。')
                    return redirect('change_password')
                request.session.pop('force_password_reset', None)
                return redirect('main')
            else:
                messages.error(request, '密码错误')
        except AppUser.DoesNotExist:
            messages.error(request, '用户不存在')
    return render(request, 'login.html')

# 主页面
def main_view(request):
    session_ctx, redirect_response = _ensure_login(request, enforce_password_change=True)
    if redirect_response:
        return redirect_response
    user_id = session_ctx['user_id']
    project_counts_qs = Project.objects.values('status').annotate(total=Count('id'))
    project_counts = {entry['status']: entry['total'] for entry in project_counts_qs}
    project_status_stats, project_count = _build_status_stats(project_counts, Project.STATUS_LABELS)

    task_counts_qs = Task.objects.values('status').annotate(total=Count('id'))
    task_counts = {entry['status']: entry['total'] for entry in task_counts_qs}
    task_status_stats, task_count = _build_status_stats(task_counts, Task.STATUS_LABELS)

    todo_tasks = (
        Task.objects.filter(assignee_id=user_id)
        .exclude(status='done')
        .select_related('project')
        .order_by('-priority', '-due_date')[:10]
    )
    current_path = request.path
    context = build_base_context(request)
    context.update({
        'project_status_stats': project_status_stats,
        'task_status_stats': task_status_stats,
        'project_count': project_count,
        'task_count': task_count,
        'todo_tasks': todo_tasks,
        'current_path': current_path,
    })
    return render(request, 'main.html', context)

# 登出
def logout_view(request):
    keys_to_clear = [
        'user_id',
        'display_name',
        'permission_code',
        'can_manage_projects',
        'can_manage_tasks',
        'can_manage_users',
        'can_manage_permissions',
        'can_view_all_tasks',
        'can_edit_all_tasks',
        'department_id',
        'force_password_reset',
    ]
    for key in keys_to_clear:
        request.session.pop(key, None)
    request.session.cycle_key()
    messages.success(request, '您已安全退出系统')
    return redirect('login')

# 修改密码
def change_password_view(request):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    user_id = session_ctx['user_id']
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request, '两次输入的新密码不一致')
            return render(request, 'change_password.html', build_base_context(request))

        user = AppUser.objects.get(id=user_id)
        if not _password_matches(old_password, user.password_hash):
            messages.error(request, '旧密码错误')
            return render(request, 'change_password.html', build_base_context(request))

        user.password_hash = make_password(new_password)
        update_fields = ['password_hash']
        if getattr(user, 'needs_password_reset', False):
            user.needs_password_reset = False
            update_fields.append('needs_password_reset')
        user.save(update_fields=update_fields)
        request.session.flush()
        messages.success(request, '密码修改成功，请使用新密码重新登录')
        return redirect('login')
    return render(request, 'change_password.html', build_base_context(request))


def user_list(request):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_users'):
        return _permission_denied(request)
    profiles_qs = UserProfile.objects.select_related('user', 'department', 'permission_group')
    profiles = list(profiles_qs)
    user_ids_with_profile = {profile.user_id for profile in profiles}
    extra_users = AppUser.objects.exclude(id__in=user_ids_with_profile).order_by('username')
    rows = [
        {
            'user': profile.user,
            'profile': profile,
            'department': profile.department,
            'permission_group': profile.permission_group,
        }
        for profile in profiles
    ]
    for user in extra_users:
        rows.append({
            'user': user,
            'profile': None,
            'department': None,
            'permission_group': None,
        })
    rows.sort(key=lambda item: item['user'].username.lower())
    context = build_base_context(request)
    context.update({'users': rows})
    return render(request, 'users/list.html', context)


def user_create(request):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_users'):
        return _permission_denied(request)
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '用户创建成功，已设置为首次登录需修改密码')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    context = build_base_context(request)
    context.update({'form': form, 'form_title': '新建用户'})
    return render(request, 'users/form.html', context)


def user_update(request, user_id):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_users'):
        return _permission_denied(request)
    user = get_object_or_404(AppUser, pk=user_id)
    profile = UserProfile.objects.filter(user=user).select_related('permission_group', 'department').first()
    if request.method == 'POST':
        form = UserUpdateForm(request.POST)
        if form.is_valid():
            form.save(user, profile)
            if user.id == session_ctx['user_id']:
                updated_profile = UserProfile.objects.get(user=user)
                _set_session_permissions(request, updated_profile)
            messages.success(request, '用户信息已更新')
            return redirect('user_list')
    else:
        initial_group = profile.permission_group_id if profile else _get_default_permission_group().id
        initial_department = profile.department_id if profile else None
        form = UserUpdateForm(initial={
            'display_name': user.display_name,
            'department': initial_department,
            'permission_group': initial_group,
        })
    context = build_base_context(request)
    context.update({'form': form, 'form_title': f'编辑用户 · {user.username}', 'user_obj': user})
    return render(request, 'users/form.html', context)


def user_delete(request, user_id):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_users'):
        return _permission_denied(request)
    user = get_object_or_404(AppUser, pk=user_id)
    if request.method != 'POST':
        return _permission_denied(request, '非法请求方式')
    if user.id == session_ctx['user_id']:
        messages.error(request, '不能删除当前登录用户')
        return redirect('user_list')
    profile = UserProfile.objects.filter(user=user).select_related('permission_group').first()
    if profile and profile.permission_group.code == 'admin':
        admin_count = UserProfile.objects.filter(permission_group__code='admin').count()
        if admin_count <= 1:
            messages.error(request, '至少保留一名管理员账号')
            return redirect('user_list')
    user.delete()
    messages.success(request, '用户已删除')
    return redirect('user_list')


def permission_group_list(request):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_permissions'):
        return _permission_denied(request)
    groups = PermissionGroup.objects.order_by('name')
    context = build_base_context(request)
    context.update({'groups': groups, 'protected_codes': PROTECTED_PERMISSION_CODES})
    return render(request, 'permissions/list.html', context)


def permission_group_create(request):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_permissions'):
        return _permission_denied(request)
    if request.method == 'POST':
        form = PermissionGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '权限组创建成功')
            return redirect('permission_group_list')
    else:
        form = PermissionGroupForm()
    context = build_base_context(request)
    context.update({'form': form, 'form_title': '新建权限组'})
    return render(request, 'permissions/form.html', context)


def permission_group_update(request, pk):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_permissions'):
        return _permission_denied(request)
    group = get_object_or_404(PermissionGroup, pk=pk)
    if request.method == 'POST':
        form = PermissionGroupForm(request.POST, instance=group)
        if group.code in PROTECTED_PERMISSION_CODES:
            form.fields['code'].disabled = True
        if form.is_valid():
            form.save()
            messages.success(request, '权限组已更新')
            return redirect('permission_group_list')
    else:
        form = PermissionGroupForm(instance=group)
        if group.code in PROTECTED_PERMISSION_CODES:
            form.fields['code'].disabled = True
    context = build_base_context(request)
    context.update({'form': form, 'form_title': f'编辑权限组 · {group.name}'})
    return render(request, 'permissions/form.html', context)


def permission_group_delete(request, pk):
    session_ctx, redirect_response = _ensure_login(request)
    if redirect_response:
        return redirect_response
    if not session_ctx.get('can_manage_permissions'):
        return _permission_denied(request)
    group = get_object_or_404(PermissionGroup, pk=pk)
    if request.method != 'POST':
        return _permission_denied(request, '非法请求方式')
    if group.code in PROTECTED_PERMISSION_CODES:
        messages.error(request, '系统内置权限组不可删除')
        return redirect('permission_group_list')
    if UserProfile.objects.filter(permission_group=group).exists():
        messages.error(request, '仍有用户隶属于该权限组，无法删除')
        return redirect('permission_group_list')
    group.delete()
    messages.success(request, '权限组已删除')
    return redirect('permission_group_list')
