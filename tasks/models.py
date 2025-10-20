from django.db import models
from app.models import AppUser
from projects.models import Project

class Task(models.Model):
    STATUS_LABELS = {
        'todo': '待处理',
        'in_progress': '进行中',
        'blocked': '阻塞',
        'done': '已完成',
    }

    STATUS_STYLES = {
        'todo': 'status-badge--default',
        'in_progress': 'status-badge--ongoing',
        'blocked': 'status-badge--blocked',
        'done': 'status-badge--done',
    }

    PRIORITY_LABELS = {
        1: '1 · 低',
        2: '2 · 普通',
        3: '3 · 重要',
        4: '4 · 紧急',
        5: '5 · 最高',
    }

    PRIORITY_STYLES = {
        0: 'priority-badge--0',
        1: 'priority-badge--1',
        2: 'priority-badge--2',
        3: 'priority-badge--3',
        4: 'priority-badge--4',
        5: 'priority-badge--5',
    }

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    assignee = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)
    priority = models.IntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, default='todo')
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.project.code}] {self.title}"

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def priority_label(self) -> str:
        return self.PRIORITY_LABELS.get(self.priority, str(self.priority))

    @property
    def status_css(self) -> str:
        return self.STATUS_STYLES.get(self.status, 'status-badge--default')

    @property
    def priority_css(self) -> str:
        return self.PRIORITY_STYLES.get(self.priority, 'priority-badge--0')

    class Meta:
        db_table = 'tasks'