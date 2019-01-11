from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, Http404
from .pivot import Pivot
from .quiz_page import QuizPage


def index(request: HttpRequest):
    with Pivot.instance.lock_read() as lr:
        engine = Pivot.instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')
        qp = QuizPage(request, engine)
        qp.compute()
    return render(request, 'pqawV1/index.html', qp.context)
