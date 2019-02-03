from django.contrib import admin

from .models import Question, Target, Answer
from django.conf import settings

from .thumbnails import refresh_thumbnail


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = settings.PQA_N_ANSWERS


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ('message', 'retain', 'pqa_id', 'created', 'modified')
    list_filter = ['created', 'modified']
    search_fields = ['pqa_id', 'message']
    readonly_fields = ('pqa_id',)

    def has_delete_permission(self, request, obj=None):
        return False


class TargetAdmin(admin.ModelAdmin):
    list_display = ('title', 'retain', 'pqa_id', 'link', 'image', 'created', 'modified')
    list_filter = ('created', 'modified')
    search_fields = ['pqa_id', 'title', 'link', 'image', 'description']
    readonly_fields = ('pqa_id', 'thumbnail')

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj: Target, form, change):
        refresh_thumbnail(obj)
        super().save_model(request, obj, form, change)


admin.site.register(Question, QuestionAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(Answer)
