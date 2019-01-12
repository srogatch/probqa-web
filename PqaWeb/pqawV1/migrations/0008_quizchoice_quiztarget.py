# Generated by Django 2.1.4 on 2019-01-12 15:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pqawV1', '0007_quiz'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizChoice',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Answer')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Question')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Quiz')),
            ],
        ),
        migrations.CreateModel(
            name='QuizTarget',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('last_choice_id', models.BigIntegerField()),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Quiz')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqawV1.Target')),
            ],
        ),
    ]