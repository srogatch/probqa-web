from django.urls import path

from . import admin_custom_views

urlpatterns = [
    path('sync-sql-kb/', admin_custom_views.sync_sql_kb, name='sync-sql-kb'),
]
