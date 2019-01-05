# Generated by Django 2.1.4 on 2019-01-05 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pqawV1', '0004_question_to_delete'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='to_delete',
        ),
        migrations.RemoveField(
            model_name='target',
            name='to_delete',
        ),
        migrations.AddField(
            model_name='question',
            name='retain',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='target',
            name='retain',
            field=models.BooleanField(default=True),
        ),
    ]
