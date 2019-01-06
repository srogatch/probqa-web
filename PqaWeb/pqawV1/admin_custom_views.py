from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .sql_kb_sync import SqlKbSync


@staff_member_required
def sync_sql_kb(request):
    sks = SqlKbSync()
    sks.go()
    return HttpResponse('Synchronizing SQL and KB has resulted in: ' + str(sks.res_msg))
    # return HttpResponseRedirect(request.META["HTTP_REFERER"])
