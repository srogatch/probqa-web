from django.urls import path

from . import admin_custom_views

app_name = 'admin-custom'

urlpatterns = [
    path('sync-sql-kb/', admin_custom_views.sync_sql_kb, name='sync-sql-kb'),
    path('backup-all/', admin_custom_views.backup_all, name='backup-all'),
    path('save-engine/', admin_custom_views.save_engine, name='save-engine'),
]
