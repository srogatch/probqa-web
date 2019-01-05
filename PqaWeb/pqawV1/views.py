from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .pivot import Pivot


@staff_member_required
def sync_sql_kb(request):
    return HttpResponse('Synchronizing SQL and KB.')


def index(request):
    engine = Pivot.instance.get_engine()
    if not engine:
        return HttpResponse('Maintenance is in progress.')
    return HttpResponse("Hello, world. You're at the polls index.")
