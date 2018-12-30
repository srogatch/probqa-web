from django.contrib import admin

from .models import Question, Target, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 5 #TODO: instead, put here the number of answer options in the engine

class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ('pqa_id', 'message', 'created', 'modified')
    list_filter = ['pqa_id', 'created', 'modified']
    search_fields = ['pqa_id', 'message']

class TargetAdmin(admin.ModelAdmin):
    list_display = ('pqa_id', 'title', 'link', 'image', 'description', 'created', 'modified')
    list_filter = ('pqa_id', 'created', 'modified')
    search_fields = ['pqa_id', 'title', 'link', 'image', 'description']

admin.site.register(Question, QuestionAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(Answer)
