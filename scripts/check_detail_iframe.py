# quick script to fetch the knowledge detail HTML and look for the attachment iframe
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()
from django.test import Client

c = Client()
# set session as the owner of the attachment we know exists (owner id 5 for item 28)
session = c.session
session['user_id'] = 5
session.save()

url = '/knowledge/28/'
print('Requesting', url)
r = c.get(url)
print('Status', r.status_code)
if r.status_code != 200:
    print('Body preview:\n', r.content[:200])
else:
    html = r.content.decode('utf-8')
    # naive search for iframe URL
    search = '/knowledge/28/attachment/20/'
    if search in html:
        start = html.find(search)
        snippet = html[max(0, start-60):start+len(search)+60]
        print('Found iframe snippet:', snippet)
    else:
        print('Did not find expected iframe src in HTML')
