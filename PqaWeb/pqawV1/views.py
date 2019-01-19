from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, Http404
from .pivot import pivot_instance
from .quiz_page import QuizPage


def index(request: HttpRequest):
    with pivot_instance.lock_shared() as lr:
        engine = pivot_instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')
        qp = QuizPage(request, engine)
        qp.compute()
    return render(request, 'pqawV1/index.html', qp.context)


def google_site_verification(request: HttpRequest):
    return HttpResponse('google-site-verification: google139b7e8eec9d86dd.html', content_type="text/plain")
