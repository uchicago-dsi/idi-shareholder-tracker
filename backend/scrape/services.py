"""Services used throughout the Django application.
"""

# Standard library imports
from typing import Iterator, List, Tuple

# Third-party imports
from django.conf import settings
from more_itertools import chunked

# Application imports
from common.services import TaskService
from scrape.domain import (
    CusipMapping,
    ScrapedCompany,
    ScrapedFiling,
    ScrapedForm13FCoverPageManager,
    ScrapedForm13FStock,
    ScrapedForm13FStockManagerList,
)
from scrape import models


class ScrapedCompanyService:
    """Provides database operations for scraped
    companies and their filing detail webpages.
    """

    @staticmethod
    def upsert(
        companies: List[ScrapedCompany],
    ) -> Tuple[int, int, int]:
        """Upserts companies and their recent filings into the database.

        References:
        - **[bulk_create | QuerySet API reference | Django documentation | Django](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#bulk-create)**
        - **[update_or_create | QuerySet API reference | Django documentation | Django](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#update-or-create)**

        Args:
            companies (`list` of `ScrapedCompany`): The companies.

        Returns:
            ((`int`, `int`, `int`,)): A three-item tuple consisting of
                the total number of (1) created companies, (2) updated
                companies, and (3) filings across the companies.
        """
        num_created_companies = 0
        num_filings = 0
        for company in companies:

            # Upsert scraped company into database
            db_cmpy, created = models.ScrapedCompany.objects.update_or_create(
                cik=company.cik,
                defaults=dict(
                    name=company.name,
                    former_names=company.former_names,
                    street=company.address.street,
                    secondary=company.address.secondary,
                    city=company.address.city,
                    state_or_country=company.address.state_or_country,
                    zip_code=company.address.zip_code,
                ),
            )

            # Bulk insert company's form submissions, ignoring any conflicts
            db_filings = models.ScrapedCompanyFiling.objects.bulk_create(
                objs=[
                    models.ScrapedCompanyFiling(
                        company=db_cmpy,
                        form=filing.form,
                        accession_number=filing.accession_number,
                        report_date=filing.report_date,
                        filing_date=filing.filing_date,
                        url=filing.url,
                    )
                    for filing in company.recent_filings
                ],
                batch_size=1000,
                ignore_conflicts=True,
            )

            # Update creation statistics for reporting
            num_created_companies += int(created)
            num_filings += len(db_filings)

        # Calculate number of updated companies
        num_updated_companies = len(companies) - num_created_companies

        return num_created_companies, num_updated_companies, num_filings

    @staticmethod
    def get_unprocessed_filings() -> List[ScrapedFiling]:
        """Queries the database for filing URLs
        that have not yet been successfully scraped.

        Args:
            `None`

        Returns:
            (`list` of `ScrapedFiling`): The filings.
        """
        return models.ScrapedCompanyFiling.objects.exclude(
            url__in=TaskService.get_success_urls(),
            num_retries=settings.MAX_TASK_RETRIES,
        )


class ScrapedForm13FStockService:
    """Provides database operations for scraped Form 13F Stocks."""

    @staticmethod
    def bulk_insert(stocks: List[ScrapedForm13FStock]) -> int:
        """Bulk inserts stocks scraped from submitted
        Form 13F filings into the database.

        Args:
            stocks (`list` of `ScrapedForm13FStock`): The stocks.

        Returns:
            (`int`): The number of inserted records,
                while ignoring conflicts.
        """
        # Fetch filings corresponding to disclosed stocks
        filings = models.ScrapedCompanyFiling.objects.filter(
            accession_number__in=[s.form_accession_number for s in stocks]
        )

        # Create filing lookup
        filing_lookup = {filing.accession_number: filing for filing in filings}

        # Bulk insert stocks, ignoring any conflicts
        inserted = models.ScrapedForm13FStock.objects.bulk_create(
            objs=[
                models.ScrapedForm13FStock(
                    filing=filing_lookup[stock.form_accession_number],
                    issuer_name=stock.issuer_name,
                    title_class=stock.title_class,
                    cusip=stock.cusip,
                    value_x1000=stock.value_x1000,
                    shares_prn_amt=stock.shares_prn_amt,
                    sh_prn=stock.sh_prn,
                    put_call=stock.put_call,
                    investment_discretion=stock.investment_discretion,
                    other_manager=stock.other_manager,
                    voting_auth_sole=stock.voting_auth_sole,
                    voting_auth_shared=stock.voting_auth_shared,
                    voting_auth_none=stock.voting_auth_none,
                )
                for stock in stocks
            ],
            batch_size=1000,
            ignore_conflicts=True,
        )

        return len(inserted)

    @staticmethod
    def get_unprocessed_cusips() -> List[str]:
        """Fetches the CUSIPs of all stocks that are
        not yet associated with financial metadata.

        Args:
            `None`

        Returns:
            (`list` of `str`): The CUSIPs.
        """
        processed_cusips = models.EdgarCusipMapping.objects.values_list(
            "cusip", flat=True
        )
        return [
            cusip
            for cusip in models.ScrapedForm13FStock.objects.exclude(
                cusip__in=processed_cusips
            )
            .values_list("cusip", flat=True)
            .distinct()
        ]

    def yield_managers(
        batch_size: int,
    ) -> Iterator[List[ScrapedForm13FStockManagerList]]:
        """"""
        # Fetch clean stock ids and convert to set
        cleaned_stocks = set(
            models.CleanForm13StockManager.objects.values_list(
                "stock_id", flat=True
            ).distinct()
        )

        # Fetch all stock ids and convert to set
        all_stocks = set(
            models.ScrapedForm13FStock.objects.values_list("id", flat=True)
        )

        # Take set difference to get ids of unclean stocks
        unclean_stocks = all_stocks.difference(cleaned_stocks)

        # Create iterator for select fields from unclean stocks
        iterator = (
            models.ScrapedForm13FStock.objects.filter(pk__in=unclean_stocks)
            .exclude(other_manager="")
            .only("id", "filing", "other_manager")
            .iterator()
        )

        # Yield results in batches
        for batch in chunked(iterator, batch_size):
            yield [
                ScrapedForm13FStockManagerList(
                    form_id=stock.filing.id,
                    stock_id=stock.id,
                    names=stock.other_manager,
                )
                for stock in batch
            ]


class ScrapedForm13FManagerService:
    """Provides database operations for scraped Form 13F managers."""

    @staticmethod
    def bulk_insert(managers: List[ScrapedForm13FCoverPageManager]) -> int:
        """Bulk inserts managers scraped from submitted
        Form 13F cover pages into the database.

        Args:
            managers (`list` of `ScrapedForm13FManager`): The managers.

        Returns:
            (`int`): The number of inserted records,
                while ignoring conflicts.
        """
        # Fetch filings corresponding to disclosed stocks
        filings = models.ScrapedCompanyFiling.objects.filter(
            accession_number__in=[m.form_accession_number for m in managers]
        )

        # Create filing lookup
        filing_lookup = {filing.accession_number: filing for filing in filings}

        # Bulk insert stocks, ignoring any conflicts
        inserted = models.ScrapedForm13FManager.objects.bulk_create(
            objs=[
                models.ScrapedForm13FManager(
                    filing=filing_lookup[manager.form_accession_number],
                    name=manager.name,
                    number=manager.number,
                )
                for manager in managers
            ],
            batch_size=1000,
            ignore_conflicts=True,
        )

        return len(inserted)

    def get_manager_name(
        form_id: int, manager_number: int
    ) -> ScrapedForm13FCoverPageManager:
        """ """
        try:
            return models.ScrapedForm13FManager.objects.get(
                filing_id=form_id, number=manager_number
            ).name
        except models.ScrapedForm13FManager.DoesNotExist:
            return None


class CusipMappingService:
    """Provides database operations for retrieved CUSIP mappings."""

    @staticmethod
    def bulk_insert(cusip_mappings: List[CusipMapping]) -> int:
        """Bulk inserts additional financial
        metadata for CUSIPs into the database.

        Args:
            stocks (`list` of `CusipMapping`): The metadata.

        Returns:
            (`int`): The number of inserted records,
                while ignoring conflicts.
        """
        inserted = models.EdgarCusipMapping.objects.bulk_create(
            objs=[
                models.EdgarCusipMapping(**mapping.model_dump())
                for mapping in cusip_mappings
            ],
            batch_size=1000,
            ignore_conflicts=True,
        )
        return len(inserted)
