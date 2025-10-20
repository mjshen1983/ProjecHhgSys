from pathlib import Path

from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class UnicodeFileSystemStorage(FileSystemStorage):
    """Preserve original filename (including 中文字符) when saving attachments."""

    def get_valid_name(self, name: str) -> str:
        # 仅移除目录信息，保留原始文件名中的 Unicode 字符。
        return Path(name).name


attachment_storage = UnicodeFileSystemStorage()

class Attachment(models.Model):
    name = models.CharField(max_length=128, default='')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/', storage=attachment_storage)
    uploaded_by = models.ForeignKey('app.AppUser', on_delete=models.CASCADE)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.file.name

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
        db_table = 'attachments'