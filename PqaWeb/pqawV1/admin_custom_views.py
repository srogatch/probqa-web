from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .sql_kb_sync import SqlKbSync
from django.utils import html
from .pivot import Pivot


@staff_member_required
def sync_sql_kb(request):
    with Pivot.instance.lock_write():
        sks = SqlKbSync()
        sks.go()
    message = 'Synchronizing SQL and KB has resulted in: ' + str(sks.res_msg)
    message = html.escape(message)
    message = message.replace('\n', '<br/>')
    return HttpResponse(message)
    # return HttpResponseRedirect(request.META["HTTP_REFERER"])
