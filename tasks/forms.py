from django import forms

from .models import Task
from app.models import AppUser


class TaskForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('todo', '待处理'),
        ('in_progress', '进行中'),
        ('blocked', '阻塞'),
        ('done', '已完成'),
    ]

    PRIORITY_CHOICES = [
        (1, '1 · 低'),
        (2, '2 · 普通'),
        (3, '3 · 重要'),
        (4, '4 · 紧急'),
        (5, '5 · 最高'),
    ]

    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'assignee', 'priority', 'due_date', 'status']
        labels = {
            'project': '所属项目',
            'title': '任务标题',
            'description': '任务描述',
            'assignee': '负责人',
            'priority': '优先级',
            'due_date': '截止日期',
            'status': '任务状态',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': '说明任务目标、背景与验收标准'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'title': '如：完成硬件采购需求汇总',
        }
        self.fields['assignee'].queryset = AppUser.objects.order_by('display_name')
        self.fields['assignee'].label_from_instance = (
            lambda obj: f"{obj.display_name or obj.username} ({obj.username})"
        )
        self.fields['priority'].widget = forms.Select(choices=self.PRIORITY_CHOICES)
        self.fields['status'].widget = forms.Select(choices=self.STATUS_CHOICES)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('autocomplete', 'off')
            if field_name in placeholders:
                field.widget.attrs.setdefault('placeholder', placeholders[field_name])
