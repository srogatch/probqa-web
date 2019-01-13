from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import html
from .admin_actions import AdminActions


def format_message(message : str) -> str:
    message = str(message)
    message = html.escape(message)
    message = message.replace('\n', '<br/>')
    return message


@staff_member_required
def sync_sql_kb(request):
    aa = AdminActions()
    aa.sync_sql_kb()
    context = {'res_msg' : format_message(aa.res_msg)}
    return render(request, 'admin/action_result.html', context)


@staff_member_required
def save_engine(request):
    aa = AdminActions()
    context = {'res_msg': AdminActions.format_engine_save_status(aa.save_engine())}
    return render(request, 'admin/action_result.html', context)


@staff_member_required
def backup_all(request):
    aa = AdminActions()
    aa.start_backup_all()
    context = {'res_msg' : format_message(aa.res_msg)}
    return render(request, 'admin/action_result.html', context)
