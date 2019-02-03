from django.db import models
import hashlib
from pathlib import Path


class Target(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField('Permanent ID in engine', unique=True, null=True, blank=True, db_index=True)
    retain = models.BooleanField(default=True)
    title = models.CharField(max_length=255)
    link = models.TextField(max_length=65535)
    # The limit of 255 characters in the path is not because of Windows path length, but because of
    #   MySQL limitation: https://stackoverflow.com/questions/36953538/mysql-column-size-limit 
    image = models.ImageField(max_length=255,upload_to='Uploads/TargetImages/%Y/%m/%d/')
    thumbnail = models.ImageField(max_length=255,upload_to='Uploads/TargetThumbnails/%Y/%m/%d/', null=True, blank=True)
    description = models.TextField(max_length=65535)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Title=[%s], Link=[%s], ImageMD5=[%s], Created=[%s], Modified=[%s]' % (
            self.title, self.link,
            hashlib.md5(Path(self.image.storage.path(self.image.name)).read_bytes()).hexdigest(),
            str(self.created), str(self.modified))


class Question(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField('Permanent ID in engine', unique=True, null=True, blank=True, db_index=True)
    retain = models.BooleanField(default=True)
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'PqaID=[%s], Message=[%s], Created=[%s], Modified=[%s]' % (
            str(self.pqa_id), self.message, str(self.created), str(self.modified))


class Answer(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # For quiz resuming to work, answer options must not change their positions once created.
    option_pos = models.BigIntegerField('Option position number')
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'QuestionPqaID=[%s], OptionPos=[%d], Message=[%s], Created=[%s], Modified=[%s]' % (
            str(self.question.pqa_id), self.option_pos, self.message, str(self.created), str(self.modified))


class Quiz(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField('Permanent ID in engine', unique=True, db_index=True)
    active_question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True)
    # https://github.com/un33k/django-ipware
    # https://stackoverflow.com/a/16203978/1915854
    user_ip = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)


class QuizChoice(models.Model):
    id = models.BigAutoField(primary_key=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_pqa_id = models.BigIntegerField()
    i_answer = models.BigIntegerField()


class QuizTarget(models.Model):
    id = models.BigAutoField(primary_key=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    target_pqa_id = models.BigIntegerField()
    # It's not entirely a foreign key because it marks the end for a range of choices
    last_choice_id = models.BigIntegerField()


class KnowledgeBase(models.Model):
    id = models.BigAutoField(primary_key=True)
    path = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return 'path=[%s], timestamp=[%s]' % (self.path, str(self.timestamp))
