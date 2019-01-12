# Generated by Django 2.1.4 on 2019-01-12 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pqawV1', '0006_knowledgebase'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('pqa_id', models.BigIntegerField(unique=True, verbose_name='Permanent ID in engine')),
                ('user_ip', models.CharField(blank=True, max_length=255, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]