from django.shortcuts import render
from django.http import HttpResponse
from .pivot import Pivot


def index(request):
    engine = Pivot.instance.get_engine()
    if not engine:
        return HttpResponse('Maintenance is in progress.')

    return HttpResponse("Hello, world. You're at the polls index.")
