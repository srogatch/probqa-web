from django.db import models

class Target(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField(
        'Permanent target identifier inside the engine',
        unique=True, null=True)
    title = models.CharField(max_length=255)
    link = models.TextField(max_length=65535)
    image = models.BinaryField(max_length=(1<<24)-1)
    description = models.TextField(max_length=65535)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class Question(models.Model):
    id = models.BigAutoField(primary_key=True)
    pqa_id = models.BigIntegerField(
        'Permanent question identifier inside the engine',
        unique=True, null=True)
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class Answer(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option_pos = models.BigIntegerField('Option position number')
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
