from django.db import models
from pathlib import Path
from django.conf import settings
from django.utils import timezone


class KnowledgeItem(models.Model):
    VISIBILITY_PRIVATE = 'private'
    VISIBILITY_DEPT = 'department'
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_CHOICES = [
        (VISIBILITY_PRIVATE, '仅自己'),
        (VISIBILITY_DEPT, '部门可见'),
        (VISIBILITY_PUBLIC, '所有人可见'),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    # Use the project's AppUser model (app.AppUser) which is unmanaged in this codebase
    owner = models.ForeignKey('app.AppUser', on_delete=models.CASCADE)
    department = models.CharField(max_length=128, blank=True, null=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PRIVATE)
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_items'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.owner})"


class KnowledgeAttachment(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(KnowledgeItem, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='knowledge/%Y/%m/%d/')
    filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    @property
    def file_basename(self) -> str:
        if not self.file:
            return ''
        return Path(self.file.name).name

    @property
    def file_extension(self) -> str:
        if not self.file:
            return ''
        return Path(self.file.name).suffix.lstrip('.')

    class Meta:
        db_table = 'knowledge_attachments'

    def __str__(self):
        return self.filename or str(self.file)
