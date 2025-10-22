from django import forms
from .models import KnowledgeItem


class KnowledgeItemForm(forms.ModelForm):
    # Do not declare a multiple-file field here because Django's
    # ClearableFileInput doesn't support multiple uploads. The view
    # will handle request.FILES.getlist('attachments') directly.
    class Meta:
        model = KnowledgeItem
        fields = ['title', 'body', 'visibility', 'tags', 'department']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'title': '标题',
            'body': '正文',
            'visibility': '可见性',
            'tags': '标签',
            'department': '部门',
        }
