from __future__ import annotations

from typing import Optional

from django import forms
from django.contrib.auth.hashers import make_password

from .models import AppUser, UserProfile, PermissionGroup
from projects.models import Department


class UserCreateForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=64)
    display_name = forms.CharField(label='用户显示名', max_length=64)
    department = forms.ModelChoiceField(
        label='所属部门',
        queryset=Department.objects.none(),
        required=False,
        empty_label='未指定',
    )
    permission_group = forms.ModelChoiceField(
        label='权限等级',
        queryset=PermissionGroup.objects.none(),
        required=True,
    )
    password = forms.CharField(label='初始密码', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='确认密码', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['permission_group'].queryset = PermissionGroup.objects.order_by('name')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if AppUser.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已存在')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', '两次密码输入不一致')
        return cleaned

    def save(self) -> AppUser:
        username = self.cleaned_data['username'].strip()
        display_name = self.cleaned_data['display_name'].strip() or username
        password_hash = make_password(self.cleaned_data['password'])
        user = AppUser.objects.create(
            username=username,
            display_name=display_name,
            password_hash=password_hash,
            needs_password_reset=True,
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'department': self.cleaned_data.get('department'),
                'permission_group': self.cleaned_data['permission_group'],
                'is_active': True,
            },
        )
        return user


class UserUpdateForm(forms.Form):
    display_name = forms.CharField(label='用户显示名', max_length=64)
    department = forms.ModelChoiceField(
        label='所属部门',
        queryset=Department.objects.none(),
        required=False,
        empty_label='未指定',
    )
    permission_group = forms.ModelChoiceField(
        label='权限等级',
        queryset=PermissionGroup.objects.none(),
        required=True,
    )
    new_password = forms.CharField(label='重置密码', widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(label='确认密码', widget=forms.PasswordInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['permission_group'].queryset = PermissionGroup.objects.order_by('name')

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if pwd or confirm:
            if not pwd:
                self.add_error('new_password', '请输入新密码')
            elif not confirm:
                self.add_error('confirm_password', '请确认新密码')
            elif pwd != confirm:
                self.add_error('confirm_password', '两次密码输入不一致')
        return cleaned

    def save(self, user: AppUser, profile: Optional[UserProfile]) -> AppUser:
        display_name = self.cleaned_data['display_name'].strip() or user.username
        user.display_name = display_name
        new_password = self.cleaned_data.get('new_password')
        update_fields = ['display_name']
        if new_password:
            user.password_hash = make_password(new_password)
            user.needs_password_reset = True
            update_fields.extend(['password_hash', 'needs_password_reset'])
        user.save(update_fields=update_fields)

        profile_defaults = {
            'department': self.cleaned_data.get('department'),
            'permission_group': self.cleaned_data['permission_group'],
            'is_active': True,
        }
        UserProfile.objects.update_or_create(user=user, defaults=profile_defaults)
        return user


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        fields = [
            'code',
            'name',
            'description',
            'can_manage_projects',
            'can_manage_tasks',
            'can_manage_users',
            'can_manage_permissions',
            'can_view_all_tasks',
            'can_edit_all_tasks',
        ]
        labels = {
            'code': '权限代号',
            'name': '权限名称',
            'description': '说明',
            'can_manage_projects': '可管理项目',
            'can_manage_tasks': '可管理任务',
            'can_manage_users': '可管理用户',
            'can_manage_permissions': '可管理权限组',
            'can_view_all_tasks': '可查看所有任务',
            'can_edit_all_tasks': '可编辑所有任务',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_code(self):
        return self.cleaned_data['code'].strip().lower()

    def clean_name(self):
        return self.cleaned_data['name'].strip()
