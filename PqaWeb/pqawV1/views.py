from django.shortcuts import render
from django.http import HttpResponse
from .pivot import Pivot
# from .session_helper import


def index(request):
    with Pivot.instance.lock_read() as lr:
        engine = Pivot.instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')

        return render(request, 'pqawV1/index.html', context)
