import os

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .pivot import pivot_instance
from .quiz_page import QuizPage


@require_http_methods(['GET', 'POST', 'HEAD'])
def index(request: HttpRequest):
    with pivot_instance.lock_shared() as lr:
        engine = pivot_instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')
        qp = QuizPage(request, engine)
        qp.compute()
    return render(request, 'pqawV1/index.html', qp.context)


def about(request: HttpRequest):
    return render(request, 'pqawV1/about.html')


def google_site_verification(request: HttpRequest):
    return HttpResponse('google-site-verification: google139b7e8eec9d86dd.html', content_type='text/plain')


def bing_site_verification(request: HttpRequest):
    return HttpResponse(
        """<?xml version="1.0"?>
            <users>
                <user>1217CBD47131F7CEE334D9169E9ADB09</user>
            </users>""",
        content_type='text/xml')


def yandex_site_verification(request: HttpRequest):
    return HttpResponse(
        """<html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            </head>
            <body>Verification: c54f5245983f4a2a</body>
           </html>""")


def robots_txt(request: HttpRequest):
    return HttpResponse('User-agent: *\nDisallow:\n', content_type='text/plain')


# https://www.sitemaps.org/faq.html#faq_sitemap_location
# https://www.sitemaps.org/protocol.html
def sitemap_xml(request: HttpRequest):
    file_path = os.path.join(settings.STATIC_ROOT, 'pqawV1/sitemap.xml')
    with open(file_path, 'r') as file:
        content = file.read()
    return HttpResponse(content, content_type='text/xml')
