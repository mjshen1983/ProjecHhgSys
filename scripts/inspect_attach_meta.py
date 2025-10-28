import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()
from knowledge.models import KnowledgeAttachment
from app.models import AppUser

try:
    a = KnowledgeAttachment.objects.get(pk=20)
except Exception as e:
    print('Attachment 20 not found:', e)
    raise SystemExit(1)
print('Attachment id', a.id)
print('file path:', getattr(a.file, 'path', None))
print('filename:', a.filename)
print('item id:', a.item_id)
item = a.item
print('item visibility:', item.visibility)
print('item owner_id:', item.owner_id)
print('item department:', item.department)
# print owner username
try:
    owner = AppUser.objects.get(pk=item.owner_id)
    print('owner username:', owner.username)
except Exception as e:
    print('owner lookup failed', e)

# list users and first few ids
print('First AppUser ids:')
for u in AppUser.objects.all()[:5]:
    print('-', u.id, u.username)
