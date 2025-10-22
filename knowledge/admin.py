from django.contrib import admin
from .models import KnowledgeItem, KnowledgeAttachment

@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'visibility', 'department', 'updated_at')
    search_fields = ('title', 'body', 'tags')


@admin.register(KnowledgeAttachment)
class KnowledgeAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'filename', 'uploaded_at')
    search_fields = ('filename',)
