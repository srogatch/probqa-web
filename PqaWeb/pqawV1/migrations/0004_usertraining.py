# Generated by Django 2.1.4 on 2019-09-13 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pqawV1', '0003_target_thumbnail'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTraining',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user_ip', models.CharField(blank=True, max_length=255, null=True)),
                ('username', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('target_pqa_id', models.BigIntegerField()),
                ('query_url', models.TextField(max_length=16777211)),
            ],
        ),
    ]