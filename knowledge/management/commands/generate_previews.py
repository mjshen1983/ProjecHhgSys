"""generate_previews

Management command to find KnowledgeAttachment records for Office files that
lack a preview and generate PDF previews using soffice.
"""
from django.core.management.base import BaseCommand
from knowledge.models import KnowledgeAttachment
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate PDF previews for office attachments (doc/docx/xls/xlsx/ppt/pptx)'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Limit number of conversions (0 = unlimited)')

    def handle(self, *args, **options):
        limit = options.get('limit') or 0
        qs = KnowledgeAttachment.objects.all()
        office_exts = ('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')
        todo = []
        for att in qs:
            try:
                fpath = att.file.path
            except Exception:
                continue
            if not fpath:
                continue
            if not os.path.exists(fpath):
                continue
            if not os.path.splitext(fpath)[1].lower() in office_exts:
                continue
            preview = fpath + '.preview.pdf'
            if os.path.exists(preview):
                continue
            todo.append(att)
            if limit and len(todo) >= limit:
                break

        self.stdout.write('Found %d attachments to process' % len(todo))
        for att in todo:
            self.stdout.write('Processing: %s (id=%s)' % (getattr(att, 'filename', ''), att.pk))
            try:
                from knowledge.views import _maybe_generate_preview
                res = _maybe_generate_preview(att)
                if res:
                    self.stdout.write(self.style.SUCCESS('Created preview: %s' % res))
                else:
                    self.stdout.write(self.style.WARNING('No preview created for: %s' % getattr(att, 'filename', '')))
            except Exception as e:
                logger.exception('Error generating preview for %s', getattr(att, 'filename', None))
                self.stdout.write(self.style.ERROR('Error: %s' % str(e)))
