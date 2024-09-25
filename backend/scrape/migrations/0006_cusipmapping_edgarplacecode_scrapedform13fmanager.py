# Generated by Django 5.1.1 on 2024-09-17 00:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrape', '0005_alter_scrapedform13fstock_shares_prn_amt_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CusipMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='')),
                ('cusip', models.CharField()),
                ('figi', models.CharField(blank=True, default='')),
                ('composite_figi', models.CharField(blank=True, default='')),
                ('share_class_figi', models.CharField(blank=True, default='')),
                ('ticker', models.CharField(blank=True, default='')),
                ('exchange_codes', models.JSONField(default=list)),
                ('market_sector', models.CharField(blank=True, default='')),
                ('security_type', models.CharField(blank=True, default='')),
                ('security_type_2', models.CharField(blank=True, default='')),
                ('security_description', models.CharField(blank=True, default='')),
            ],
            options={
                'db_table': 'cusip_mapping',
                'constraints': [models.UniqueConstraint(fields=('cusip',), name='unique_cusip_mapping')],
            },
        ),
        migrations.CreateModel(
            name='EdgarPlaceCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField()),
                ('country', models.CharField()),
                ('state', models.CharField()),
            ],
            options={
                'db_table': 'edgar_place_code',
                'constraints': [models.UniqueConstraint(fields=('code',), name='unique_edgar_place_code'), models.UniqueConstraint(fields=('country', 'state'), name='unique_edgar_place')],
            },
        ),
        migrations.CreateModel(
            name='ScrapedForm13FManager',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField()),
                ('number', models.IntegerField()),
                ('filing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrape.scrapedcompanyfiling')),
            ],
        ),
    ]
