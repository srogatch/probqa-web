from django.urls import path

from . import views

app_name = 'pqawV1'

urlpatterns = [
    path('', views.index, name='index'),
]
