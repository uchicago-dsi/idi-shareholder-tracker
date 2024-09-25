# Generated by Django 5.1.1 on 2024-09-23 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrape', '0008_cleanform13stockmanager_clean_form__stock_i_203fb8_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='Form13FStockInvestmentView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_id', models.BigIntegerField()),
                ('investor_cik', models.CharField(max_length=13)),
                ('investor_name', models.TextField()),
                ('investor_former_names', models.JSONField(default=list)),
                ('investor_country', models.CharField()),
                ('investor_region', models.CharField()),
                ('other_investor_numbers', models.JSONField(default=list)),
                ('other_investor_names', models.JSONField(default=list)),
                ('form_accession_number', models.TextField()),
                ('form_report_date', models.DateField(null=True)),
                ('form_filing_date', models.DateField(null=True)),
                ('stock_issuer', models.CharField()),
                ('stock_cusip', models.CharField(max_length=9)),
                ('stock_figi', models.CharField(blank=True, default='')),
                ('stock_ticker', models.CharField(blank=True, default='')),
                ('stock_description', models.CharField(blank=True, default='')),
                ('stock_value_x1000', models.BigIntegerField()),
                ('stock_shares_prn_amt', models.BigIntegerField()),
                ('stock_sh_prn', models.CharField()),
                ('stock_voting_auth_sole', models.BigIntegerField(null=True)),
                ('stock_voting_auth_shared', models.BigIntegerField(null=True)),
                ('stock_voting_auth_none', models.BigIntegerField(null=True)),
                ('stock_exchange_codes', models.JSONField(default=list)),
                ('form_url', models.URLField()),
            ],
            options={
                'db_table': 'form_13f_stock_investment_view',
                'managed': False,
            },
        ),
    ]
