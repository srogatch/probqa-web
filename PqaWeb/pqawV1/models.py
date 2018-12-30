from django.db import models
import hashlib
from pathlib import Path

class Target(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField(
        'Permanent ID in engine',
        unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    link = models.TextField(max_length=65535)
    # The limit of 255 characters in the path is not because of Windows path length, but because of
    #   MySQL limitation: https://stackoverflow.com/questions/36953538/mysql-column-size-limit 
    image = models.ImageField(max_length=255,upload_to='Uploads/TargetImages/%Y/%m/%d/')
    description = models.TextField(max_length=65535)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    def __str__(self):
        print(self.image.name)
        return 'Title=[%s], Link=[%s], ImageMD5=[%s], Descr=[%s], Created=[%s], Modified=[%s]' % (
            self.title, self.link,
            hashlib.md5(Path(self.image.storage.path(self.image.name)).read_bytes()).hexdigest(),
            self.description, str(self.created), str(self.modified))

class Question(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField(
        'Permanent ID in engine',
        unique=True, null=True, blank=True)
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    def __str__(self):
        return 'PqaID=[%s], Message=[%s], Created=[%s], Modified=[%s]' % (
            str(self.pqa_id), self.message, str(self.created), str(self.modified))

class Answer(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option_pos = models.BigIntegerField('Option position number')
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    def __str__(self):
        return 'QuestionPqaID=[%s], OptionPos=[%d], Message=[%s], Created=[%s], Modified=[%s]' % (
            str(self.question.pqa_id), self.option_pos, self.message, str(self.created), str(self.modified))
