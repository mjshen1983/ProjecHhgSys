from django.db import models
from app.models import AppUser


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'departments'
        ordering = ['name']

class Project(models.Model):
    STATUS_LABELS = {
        'ongoing': '进行中',
        'completed': '已完成',
        'paused': '暂停',
    }

    STATUS_STYLES = {
        'ongoing': 'status-badge--ongoing',
        'completed': 'status-badge--completed',
        'paused': 'status-badge--paused',
    }

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, default='ongoing')
    owner = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    lead_department = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def status_css(self) -> str:
        return self.STATUS_STYLES.get(self.status, 'status-badge--default')

    class Meta:
        db_table = 'projects'