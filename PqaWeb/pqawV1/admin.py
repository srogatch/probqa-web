from django.contrib import admin

from .models import Question, Target, Answer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 5  # TODO: instead, put here the number of answer options in the engine


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ('message', 'retain', 'pqa_id', 'created', 'modified')
    list_filter = ['pqa_id', 'created', 'modified']
    search_fields = ['pqa_id', 'message']
    readonly_fields = ('pqa_id',)

    def has_delete_permission(self, request, obj=None):
        return False


class TargetAdmin(admin.ModelAdmin):
    list_display = ('title', 'retain', 'pqa_id', 'link', 'image', 'description', 'created', 'modified')
    list_filter = ('pqa_id', 'created', 'modified')
    search_fields = ['pqa_id', 'title', 'link', 'image', 'description']
    readonly_fields = ('pqa_id',)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Question, QuestionAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(Answer)
