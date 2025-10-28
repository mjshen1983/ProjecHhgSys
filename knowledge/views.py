from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count, OuterRef, Subquery
from projects.models import Department
from app.models import UserProfile

from .models import KnowledgeItem, KnowledgeAttachment
from .forms import KnowledgeItemForm
from app.utils import build_base_context
from django.conf import settings
from app.models import AppUser
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
import os
from django.http import FileResponse, Http404, HttpResponse
from attachments.models import Attachment as GenericAttachment
from django.views.decorators.clickjacking import xframe_options_exempt
import shutil
import subprocess
import tempfile
import time
import logging
import pathlib


def _require_login(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None, redirect('login')
    session_ctx = build_base_context(request)
    session_ctx['user_id'] = user_id
    return session_ctx, None


def visible_items_for_user(user_id):
    q = Q(visibility=KnowledgeItem.VISIBILITY_PUBLIC)
    # read department from UserProfile (projects.Department FK)
    profile = UserProfile.objects.select_related('department').filter(user_id=user_id).first()
    user_dept_name = None
    if profile and profile.department:
        user_dept_name = profile.department.name
    if user_dept_name:
        q |= Q(visibility=KnowledgeItem.VISIBILITY_DEPT, department=user_dept_name)
    user = AppUser.objects.filter(pk=user_id).first()
    if user:
        q |= Q(visibility=KnowledgeItem.VISIBILITY_PRIVATE, owner=user)
    return KnowledgeItem.objects.filter(q)


def list_items(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    q = request.GET.get('q')
    # annotate attachment counts and prefetch attachments to avoid N+1 queries
    # also annotate uploader's department name via a subquery on UserProfile -> Department
    profile_qs = UserProfile.objects.filter(user_id=OuterRef('owner_id')).values('department__name')[:1]
    items = visible_items_for_user(session_ctx['user_id']).annotate(
        attachments_count=Count('attachments'),
        department_name=Subquery(profile_qs),
    ).prefetch_related('attachments')
    if q:
        items = items.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(tags__icontains=q))
    context = {**session_ctx, 'items': items}
    return render(request, 'knowledge/list.html', context)


@xframe_options_exempt
def view_item(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    item = get_object_or_404(KnowledgeItem, pk=pk)
    # permission check
    if item.visibility == KnowledgeItem.VISIBILITY_PRIVATE and item.owner_id != session_ctx['user_id']:
        messages.error(request, '无权查看此条目')
        return redirect('knowledge_list')
    if item.visibility == KnowledgeItem.VISIBILITY_DEPT:
        profile = UserProfile.objects.select_related('department').filter(user_id=session_ctx['user_id']).first()
        user_dept_name = None
        if profile and profile.department:
            user_dept_name = profile.department.name
        if user_dept_name != item.department and item.owner_id != session_ctx['user_id']:
            messages.error(request, '无权查看此条目')
            return redirect('knowledge_list')
    context = {**session_ctx, 'item': item}
    return render(request, 'knowledge/detail.html', context)


def create_item(request):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        form = KnowledgeItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner_id = session_ctx['user_id']
            # if department not set, try user's department
            if not item.department:
                profile = UserProfile.objects.select_related('department').filter(user_id=session_ctx['user_id']).first()
                if profile and profile.department:
                    item.department = profile.department.name
            item.save()
            # handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                att = KnowledgeAttachment(item=item, file=f, filename=f.name)
                att.save()
                # try to generate preview synchronously (will catch/log errors)
                try:
                    _maybe_generate_preview(att)
                except Exception:
                    logging.getLogger(__name__).exception('Failed to generate preview for %s', getattr(att, 'filename', None))
            messages.success(request, '知识条目已保存')
            return redirect('knowledge_list')
    else:
        form = KnowledgeItemForm()
    context = {**session_ctx, 'form': form}
    return render(request, 'knowledge/form.html', context)


@xframe_options_exempt
def attachment_serve(request, pk, aid):
    """Serve a specific KnowledgeAttachment file while allowing embedding in iframe.
    pk: KnowledgeItem id, aid: KnowledgeAttachment id
    Performs similar permission checks as view_item before serving the file.
    """
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    item = get_object_or_404(KnowledgeItem, pk=pk)
    # permission checks (reuse logic from view_item)
    if item.visibility == KnowledgeItem.VISIBILITY_PRIVATE and item.owner_id != session_ctx['user_id']:
        messages.error(request, '无权查看此附件')
        return redirect('knowledge_list')
    if item.visibility == KnowledgeItem.VISIBILITY_DEPT:
        profile = UserProfile.objects.select_related('department').filter(user_id=session_ctx['user_id']).first()
        user_dept_name = None
        if profile and profile.department:
            user_dept_name = profile.department.name
        if user_dept_name != item.department and item.owner_id != session_ctx['user_id']:
            messages.error(request, '无权查看此附件')
            return redirect('knowledge_list')
    # fetch attachment
    attachment = get_object_or_404(KnowledgeAttachment, pk=aid, item=item)
    # ensure file exists
    try:
        fpath = attachment.file.path
    except Exception:
        raise Http404('File not found')
    if not os.path.exists(fpath):
        raise Http404('File not found')
    # if this is an office file and a preview PDF exists, serve the preview instead
    ext = os.path.splitext(fpath)[1].lower()
    preview_path = fpath + '.preview.pdf'
    office_exts = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
    if ext in office_exts:
        if os.path.exists(preview_path):
            response = FileResponse(open(preview_path, 'rb'), as_attachment=False, filename=os.path.basename(preview_path))
        else:
            # Preview not ready yet — return a small HTML page (will render inside iframe)
            html = (
                '<html><head><meta charset="utf-8"><title>预览生成中</title></head>'
                '<body style="font-family: sans-serif; padding: 1rem;">'
                '<h3>预览生成中…</h3>'
                '<p>正在生成预览，请稍候或点击下面下载原始文件。</p>'
                f'<p><a href="{attachment.file.url}" download>下载原始文件 ({attachment.filename or os.path.basename(fpath)})</a></p>'
                '</body></html>'
            )
            response = HttpResponse(html)
    else:
        response = FileResponse(open(fpath, 'rb'), as_attachment=False, filename=attachment.filename or os.path.basename(fpath))
    return response


def _find_soffice():
    # Try PATH first, then common install locations
    soffice = shutil.which('soffice')
    if soffice:
        return soffice
    # common Windows path
    win_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    if os.path.exists(win_path):
        return win_path
    # specific older install folder (user-provided)
    win_path_v5 = r"C:\Program Files\LibreOffice 5\program\soffice.exe"
    if os.path.exists(win_path_v5):
        return win_path_v5

    win_path_x86 = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    if os.path.exists(win_path_x86):
        return win_path_x86
    # common unix path
    if os.path.exists('/usr/bin/soffice'):
        return '/usr/bin/soffice'
    # try to find any LibreOffice* folder under Program Files
    try:
        pf = os.environ.get('ProgramFiles', r'C:\Program Files')
        for name in os.listdir(pf):
            if name.lower().startswith('libreoffice'):
                candidate = os.path.join(pf, name, 'program', 'soffice.exe')
                if os.path.exists(candidate):
                    return candidate
    except Exception:
        pass
    return None


def _maybe_generate_preview(attachment, timeout=60):
    """Attempt to generate a PDF preview for an attachment using soffice.
    Generated preview path: original_file_path + '.preview.pdf'
    Returns path to preview on success, None on failure.
    """
    logger = logging.getLogger(__name__)
    try:
        fpath = attachment.file.path
    except Exception:
        logger.debug('Attachment has no file path')
        return None
    if not os.path.exists(fpath):
        logger.debug('Attachment file not found: %s', fpath)
        return None

    ext = os.path.splitext(fpath)[1].lower()
    office_exts = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
    if ext not in office_exts:
        logger.debug('Not an office file: %s', fpath)
        return None

    soffice = _find_soffice()
    if not soffice:
        logger.warning('soffice not found; cannot convert %s', fpath)
        return None

    # create temporary output dir to avoid clashes
    outdir = tempfile.mkdtemp(prefix='soffice-out-')
    base = os.path.splitext(os.path.basename(fpath))[0]
    cmd = [soffice, '--headless', '--convert-to', 'pdf', '--outdir', outdir, fpath]
    logger.info('Running soffice for %s, cmd=%s', fpath, cmd)
    start = time.time()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=timeout)
        duration = time.time() - start
        logger.info('soffice exit=%s duration=%.1fs stdout=%s stderr=%s', proc.returncode, duration, proc.stdout[:1000], proc.stderr[:1000])
        if proc.returncode != 0:
            logger.warning('soffice failed for %s', fpath)
            return None
        src = os.path.join(outdir, base + '.pdf')
        if not os.path.exists(src):
            logger.warning('soffice did not produce expected output: %s', src)
            return None
        dest = fpath + '.preview.pdf'
        # move/overwrite
        try:
            shutil.move(src, dest)
        except Exception:
            # fallback to copy
            shutil.copyfile(src, dest)
        logger.info('Created preview: %s', dest)
        return dest
    except subprocess.TimeoutExpired:
        logger.exception('soffice timed out for %s', fpath)
        return None
    finally:
        try:
            shutil.rmtree(outdir)
        except Exception:
            pass


@require_POST
def delete_item(request, pk):
    session_ctx, redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    item = get_object_or_404(KnowledgeItem, pk=pk)
    # only owner can delete
    if item.owner_id != session_ctx['user_id']:
        messages.error(request, '无权删除此条目')
        return redirect('knowledge_list')
    # delete attachments first (FileFields will be removed by model delete, but remove files if needed)
    for att in item.attachments.all():
        try:
            att.file.delete(save=False)
        except Exception:
            pass
    item.delete()
    messages.success(request, '条目已删除')
    return redirect('knowledge_list')
