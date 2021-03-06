from django.urls import path, re_path

from . import views

app_name = 'pqawV1'

urlpatterns = [
    # https://www.gun.io/blog/setting-up-google-webmaster-tools-with-python-django
    re_path(r'^google139b7e8eec9d86dd\.html$', views.google_site_verification),
    re_path(r'^BingSiteAuth\.xml$', views.bing_site_verification),
    re_path(r'^yandex_c54f5245983f4a2a\.html$', views.yandex_site_verification),
    re_path(r'^robots\.txt$', views.robots_txt),
    re_path(r'^sitemap\.xml$', views.sitemap_xml),
    re_path(r'^ads\.txt$', views.ads_txt),
    re_path(r'^pinterest\-4cc33\.html$', views.pinterest),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
]
