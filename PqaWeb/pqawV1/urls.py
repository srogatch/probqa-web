from django.urls import path, re_path

from . import views

app_name = 'pqawV1'

urlpatterns = [
    # https://www.gun.io/blog/setting-up-google-webmaster-tools-with-python-django
    re_path(r'^google139b7e8eec9d86dd\.html$', views.google_site_verification),
    re_path(r'^BingSiteAuth.xml$', views.bing_site_verification),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
]
