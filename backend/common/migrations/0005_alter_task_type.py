# Generated by Django 5.1.1 on 2024-09-17 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_task_unique_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(choices=[('Fetch Form 13F Stock Metadata', 'Fetch Form 13F Stock Metadata'), ('Scrape Bulk Submissions', 'Scrape Bulk Submissions'), ('Scrape Form 13F Filing Details', 'Scrape Form 13F Filing Details'), ('Scrape Form 13F Stocks', 'Scrape Form 13F Stocks')]),
        ),
    ]
