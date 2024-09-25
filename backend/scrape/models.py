"""Database models used throughout the application.
"""

# Third-party imports
from django.db import models
from django_pgviews import view as pg


class ScrapedCompany(models.Model):
    """Represents a company filing to the SEC."""

    class Meta:
        db_table = "scraped_company"
        constraints = [
            models.UniqueConstraint(
                fields=["cik"], name="unique_scraped_company_cik"
            ),
        ]

    cik = models.CharField(max_length=13)
    name = models.TextField()
    former_names = models.JSONField(default=list)
    street = models.CharField(blank=True)
    secondary = models.CharField(blank=True)
    city = models.CharField(blank=True)
    state_or_country = models.CharField()
    zip_code = models.CharField(blank=True)


class ScrapedCompanyFiling(models.Model):
    """Represents a single form submission to the SEC."""

    class FormType(models.TextChoices):
        """Enumerates the possible form types."""

        FORM_13F_HR = "13F-HR"

    class Meta:
        db_table = "scraped_form_submission"
        constraints = [
            models.UniqueConstraint(
                fields=["accession_number"],
                name="unique_scraped_filing_accession_number",
            )
        ]

    company = models.ForeignKey(to="ScrapedCompany", on_delete=models.CASCADE)
    form = models.TextField(choices=FormType)
    accession_number = models.TextField()
    report_date = models.DateField(null=True)
    filing_date = models.DateField(null=True)
    url = models.URLField()


class ScrapedForm13FStock(models.Model):
    """Represents a single investment listed in a Form 13F submission."""

    class Meta:
        db_table = "scraped_form_13f_investment"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "filing",
                    "cusip",
                    "investment_discretion",
                    "other_manager",
                ],
                name="unique_scraped_form_13f_stock",
            )
        ]

    filing = models.ForeignKey(
        to="ScrapedCompanyFiling", on_delete=models.CASCADE
    )
    issuer_name = models.CharField()
    title_class = models.CharField(blank=True)
    cusip = models.CharField(max_length=9)
    value_x1000 = models.BigIntegerField()
    shares_prn_amt = models.BigIntegerField()
    sh_prn = models.CharField()
    put_call = models.CharField(blank=True)
    investment_discretion = models.CharField()
    other_manager = models.CharField(blank=True)
    voting_auth_sole = models.BigIntegerField(null=True)
    voting_auth_shared = models.BigIntegerField(null=True)
    voting_auth_none = models.BigIntegerField(null=True)


class ScrapedForm13FManager(models.Model):
    """Represents an "Other Manager" entry
    scraped from a Form 13F cover page.
    """

    class Meta:
        db_table = "scraped_form_13f_manager"
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=[
        #             "filing",
        #             "number",
        #         ],
        #         name="unique_scraped_form_13f_manager",
        #     )
        # ]

    filing = models.ForeignKey(
        to="ScrapedCompanyFiling", on_delete=models.CASCADE
    )
    name = models.CharField()
    number = models.IntegerField()


class EdgarPlaceCode(models.Model):
    """A reference for codes internally assigned to states or countries."""

    class Meta:
        db_table = "edgar_place_code"
        constraints = [
            models.UniqueConstraint(
                fields=["code"], name="unique_edgar_place_code"
            ),
            models.UniqueConstraint(
                fields=["country", "state"], name="unique_edgar_place"
            ),
        ]

    code = models.CharField()
    country = models.CharField()
    state = models.CharField()


class EdgarCusipMapping(models.Model):
    """Externally-sourced metadata for a CUSIP scraped from SEC EDGAR."""

    class Meta:
        db_table = "edgar_cusip_mapping"
        constraints = [
            models.UniqueConstraint(
                fields=["cusip"], name="unique_edgar_cusip_mapping"
            ),
        ]

    name = models.CharField(blank=True, default="")
    cusip = models.CharField()
    figi = models.CharField(blank=True, default="")
    composite_figi = models.CharField(blank=True, default="")
    share_class_figi = models.CharField(blank=True, default="")
    ticker = models.CharField(blank=True, default="")
    exchange_codes = models.JSONField(default=list)
    market_sector = models.CharField(blank=True, default="")
    security_type = models.CharField(blank=True, default="")
    security_type_2 = models.CharField(blank=True, default="")
    security_description = models.CharField(blank=True, default="")


class CleanForm13StockManager(models.Model):
    """Represents a clean entry for a manager of a stock investment."""

    class Meta:
        db_table = "clean_form_13f_stock_manager"
        constraints = [
            models.UniqueConstraint(
                fields=["stock", "name"],
                name="unique_clean_form_13f_stock_manager",
            )
        ]
        indexes = [
            models.Index(fields=["stock"]),
        ]

    stock = models.ForeignKey(
        to="ScrapedForm13FStock", on_delete=models.CASCADE
    )
    name = models.CharField()


class Form13FStockInvestmentView(pg.MaterializedView):
    """A materialized view of cleaned Form 13F
    stock investments and related metadata.
    """

    sql = """
        SELECT
            investment.id AS stock_id,
            cmpy.cik AS investor_cik,
            cmpy.name AS investor_name,
            cmpy.former_names AS investor_former_names,
            place.country AS investor_country,
            place.state AS investor_region,
            TO_JSONB(STRING_TO_ARRAY(TRIM(investment.other_manager), ',')) AS other_investor_numbers,
            managers.names AS other_investor_names,
            form.accession_number AS form_accession_number,
            form.report_date AS form_report_date,
            form.filing_date AS form_filing_date,
            UPPER(investment.issuer_name) AS stock_issuer,
            investment.cusip AS stock_cusip,
            cusip_mapping.figi AS stock_figi,
            cusip_mapping.ticker AS stock_ticker,
            UPPER(cusip_mapping.security_type) AS stock_description,
            investment.value_x1000 AS stock_value_x1000,
            investment.shares_prn_amt AS stock_shares_prn_amt,
            investment.sh_prn AS stock_prn_amt,
            investment.voting_auth_sole AS stock_voting_auth_sole,
            investment.voting_auth_shared AS stock_voting_auth_shared,
            investment.voting_auth_none AS stock_voting_auth_none,
            cusip_mapping.exchange_codes AS stock_exchange_codes,
            form.url AS form_url
        FROM (
            SELECT
                id,
                cik,
                UPPER(name) AS name,
                JSONB_AGG(upper(elem)) AS former_names,
                state_or_country
            FROM scraped_company
            LEFT JOIN 
                LATERAL JSONB_ARRAY_ELEMENTS_TEXT(scraped_company.former_names) AS elem
                ON true
            GROUP BY scraped_company.id
        ) AS cmpy
        JOIN scraped_form_submission AS form
            ON cmpy.id = form.company_id
        LEFT JOIN edgar_place_code AS place
            ON cmpy.state_or_country = place.code
        JOIN scraped_form_13f_investment AS investment
            ON form.id = investment.filing_id
        LEFT JOIN edgar_cusip_mapping AS cusip_mapping
            ON investment.cusip = cusip_mapping.cusip
        LEFT JOIN (
            SELECT
                stock_id,
                ARRAY_AGG(name) AS names
            FROM public.clean_form_13f_stock_manager
            GROUP BY stock_id
        ) AS managers
            ON investment.id = managers.stock_id;
        """

    stock_id = models.BigIntegerField()
    investor_cik = models.CharField(max_length=13)
    investor_name = models.TextField()
    investor_former_names = models.JSONField(default=list)
    investor_country = models.CharField()
    investor_region = models.CharField()
    other_investor_numbers = models.JSONField(default=list)
    other_investor_names = models.JSONField(default=list)
    form_accession_number = models.TextField()
    form_report_date = models.DateField(null=True)
    form_filing_date = models.DateField(null=True)
    stock_issuer = models.CharField()
    stock_cusip = models.CharField(max_length=9)
    stock_figi = models.CharField(blank=True, default="")
    stock_ticker = models.CharField(blank=True, default="")
    stock_description = models.CharField(blank=True, default="")
    stock_value_x1000 = models.BigIntegerField()
    stock_shares_prn_amt = models.BigIntegerField()
    stock_sh_prn = models.CharField()
    stock_voting_auth_sole = models.BigIntegerField(null=True)
    stock_voting_auth_shared = models.BigIntegerField(null=True)
    stock_voting_auth_none = models.BigIntegerField(null=True)
    stock_exchange_codes = models.JSONField(default=list)
    form_url = models.URLField()

    concurrent_index = "stock_id"

    class Meta:
        managed = False
        db_table = "form_13f_stock_investment_view"
