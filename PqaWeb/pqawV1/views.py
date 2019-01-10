from django.shortcuts import render
from django.http import HttpResponse
from .pivot import Pivot


def index(request):
    with Pivot.instance.lock_read() as lr:
        engine = Pivot.instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')

    return HttpResponse("Hello, world. You're at the polls index.")
