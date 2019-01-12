# Generated by Django 2.1.4 on 2019-01-12 21:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('option_pos', models.BigIntegerField(verbose_name='Option position number')),
                ('message', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='KnowledgeBase',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('path', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('pqa_id', models.BigIntegerField(blank=True, null=True, unique=True, verbose_name='Permanent ID in engine')),
                ('retain', models.BooleanField(default=True)),
                ('message', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('pqa_id', models.BigIntegerField(unique=True, verbose_name='Permanent ID in engine')),
                ('user_ip', models.CharField(blank=True, max_length=255, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('active_question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pqawV1.Question')),
            ],
        ),
        migrations.CreateModel(
            name='QuizChoice',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('question_pqa_id', models.BigIntegerField()),
                ('i_answer', models.BigIntegerField()),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Quiz')),
            ],
        ),
        migrations.CreateModel(
            name='QuizTarget',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('target_pqa_id', models.BigIntegerField()),
                ('last_choice_id', models.BigIntegerField()),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Quiz')),
            ],
        ),
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('pqa_id', models.BigIntegerField(blank=True, null=True, unique=True, verbose_name='Permanent ID in engine')),
                ('retain', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=255)),
                ('link', models.TextField(max_length=65535)),
                ('image', models.ImageField(max_length=255, upload_to='Uploads/TargetImages/%Y/%m/%d/')),
                ('description', models.TextField(max_length=65535)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Question'),
        ),
    ]
