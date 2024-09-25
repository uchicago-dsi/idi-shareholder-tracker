# Generated by Django 5.1.1 on 2024-09-14 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_alter_task_type'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(fields=('workflow_execution', 'type', 'url'), name='unique_task'),
        ),
    ]
