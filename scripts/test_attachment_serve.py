# quick test script using Django test client to GET the attachment serve endpoint and print headers
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()
from django.test import Client

c = Client()
# set session to simulate logged-in user; the project stores user_id in session
session = c.session
# pick a valid AppUser id from DB
from app.models import AppUser
from knowledge.models import KnowledgeAttachment

# find one existing attachment whose file exists
found = None
for a in KnowledgeAttachment.objects.all():
    try:
        if os.path.exists(a.file.path):
            found = a
            break
    except Exception:
        continue
if not found:
    print('No existing attachment file found on disk')
    raise SystemExit(1)
# use the attachment owner so permission checks pass
owner_id = found.item.owner_id
session['user_id'] = owner_id
session.save()
url = f"/knowledge/{found.item_id}/attachment/{found.id}/"
print('Testing URL:', url, 'as user', owner_id)
# do not follow redirects; expect direct file response 200 when authorized
r = c.get(url, follow=False)
print('Status code:', r.status_code)
print('X-Frame-Options header:', r.get('X-Frame-Options'))
print('Content-Type:', r.get('Content-Type'))
print('Content-Disposition:', r.get('Content-Disposition'))
# For FileResponse, content is streaming; read first chunk
first = b''
try:
    for chunk in r.streaming_content:
        first = chunk
        break
except Exception:
    first = b''
print('First bytes:', first[:16])
