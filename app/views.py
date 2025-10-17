import hashlib

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect

from .models import AppUser


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
                return redirect('main')
            else:
                messages.error(request, '密码错误')
        except AppUser.DoesNotExist:
            messages.error(request, '用户不存在')
    return render(request, 'login.html')

# 主页面
def main_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    display_name = request.session.get('display_name')
    return render(request, 'main.html', {'display_name': display_name})

# 登出
def logout_view(request):
    request.session.flush()
    return redirect('login')

# 修改密码
def change_password_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request, '两次输入的新密码不一致')
            return render(request, 'change_password.html')

        user = AppUser.objects.get(id=user_id)
        if not _password_matches(old_password, user.password_hash):
            messages.error(request, '旧密码错误')
            return render(request, 'change_password.html')

        user.password_hash = make_password(new_password)
        user.save(update_fields=['password_hash'])
        request.session.flush()
        messages.success(request, '密码修改成功，请使用新密码重新登录')
        return redirect('login')
    return render(request, 'change_password.html')
