import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','project.settings')
django.setup()
from knowledge.models import KnowledgeItem, KnowledgeAttachment

print('Searching for attachments linked to knowledge items (KnowledgeAttachment)...')
qs = KnowledgeAttachment.objects.select_related('item').order_by('-uploaded_at')[:50]
if not qs:
    print('No attachments linked to knowledge found')
else:
    for a in qs:
        try:
            file_url = a.file.url
        except Exception as e:
            file_url = f'ERROR getting url: {e}'
        try:
            file_path = a.file.path
            exists = os.path.exists(file_path)
        except Exception as e:
            file_path = f'ERROR getting path: {e}'
            exists = False
        basename = os.path.basename(a.file.name) if a.file else ''
        extension = os.path.splitext(basename)[1].lstrip('.').lower()
        print('---')
        print('id:', a.id)
        print('filename field:', a.filename)
        print('basename:', basename)
        print('extension:', extension)
        print('url:', file_url)
        print('path:', file_path)
        print('exists on disk:', exists)
