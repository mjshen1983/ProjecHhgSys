from django import forms

from .models import Project, Department
from app.models import AppUser


class ProjectForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('paused', '暂停'),
    ]

    class Meta:
        model = Project
        fields = ['name', 'code', 'lead_department', 'description', 'start_date', 'end_date', 'status', 'owner']
        labels = {
            'name': '项目名称',
            'code': '项目编码',
            'lead_department': '牵头部门',
            'description': '项目描述',
            'start_date': '开始日期',
            'end_date': '结束日期',
            'status': '项目状态',
            'owner': '负责人',
        }
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': '请输入项目背景、目标或范围', 'rows': 4}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'name': '如：智慧工厂改造项目',
            'code': '如：PRJ-2025-001',
        }
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('autocomplete', 'off')
            if field_name in placeholders:
                field.widget.attrs.setdefault('placeholder', placeholders[field_name])
        departments = Department.objects.filter(is_active=True).order_by('name')
        dept_choices = [('', '请选择牵头部门')]
        dept_choices.extend((dept.name, f"{dept.code} · {dept.name}" if dept.code else dept.name) for dept in departments)
        existing_value = self.initial.get('lead_department') or getattr(self.instance, 'lead_department', '')
        if existing_value and not any(choice[0] == existing_value for choice in dept_choices):
            dept_choices.append((existing_value, f"{existing_value} (未配置)"))
        self.fields['lead_department'].widget = forms.Select(choices=dept_choices)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['owner'].queryset = AppUser.objects.order_by('display_name')
        self.fields['owner'].label_from_instance = (
            lambda obj: f"{obj.display_name or obj.username} ({obj.username})"
        )
        self.fields['status'].widget = forms.Select(choices=self.STATUS_CHOICES)