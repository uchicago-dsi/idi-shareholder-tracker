"""Fetches stock metadata from the Open FIGI API
to supplement Form 13F data scraped from the SEC.
"""

# Standard library imports
import os

# Third-party imports
from django.core.management.base import BaseCommand

# Application imports
from common.logger import LoggerFactory
from scrape.scrapers import OpenFigiApiClient
from scrape.services import (
    CusipMappingService,
    ScrapedForm13FStockService,
)


class Command(BaseCommand):
    """A Django management command that requests Form
    13F stock metadata by CUSIP from the Open FIGI API.

    References:
    - https://docs.djangoproject.com/en/4.1/howto/custom-management-commands/
    - https://docs.djangoproject.com/en/4.1/topics/settings/
    """

    help = "Fetches Form 13F stock metadata from the Open FIGI API."
    name = "Fetch Form 13F Stock Metadata"

    def __init__(self, *args, **kwargs) -> None:
        """Initializes a new instance of the `Command`.

        Args:
            *The default positional arguments for the base class.

        Kwargs:
            **The default keyword arguments for the base class.

        Returns:
            `None`
        """
        self._workflow_execution = os.getenv(
            "GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID", ""
        )
        self._logger = LoggerFactory.get(
            f"{Command.name.upper()} - {self._workflow_execution}"
        )
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options) -> None:
        """Executes the command.

        Args:
            `None`

        Returns:
            `None`
        """
        # Log start of processing
        self._logger.info(
            "Received request to fetch stock metadata from the Open FIGI API."
        )

        # Fetch CUSIPs of form 13f stock investments that lack metadata
        self._logger.info("Fetching Form 13F stocks missing metadata.")
        cusips = ScrapedForm13FStockService.get_unprocessed_cusips()
        self._logger.info(f"{len(cusips):,} CUSIP(s) found.")

        # End successfully if no filings exist
        if not cusips:
            self._logger.info("Process completed successfully.")
            exit(0)

        # Otherwise, instantiate client
        self._logger.info("Instantiating Open FIGI API Client.")
        client = OpenFigiApiClient(self._logger)

        # Collect metadata by CUSIP and persist to database
        try:
            for metadata in client.fetch_stock_metadata(cusips):
                CusipMappingService.bulk_insert(metadata)
        except Exception as e:
            self._logger.error(
                f"Failed to fetch stock metadata from Open FIGI API. {e}"
            )
            exit(1)

        # Log success
        self._logger.info(
            "Retrieval of stock metadata through "
            "Open FIGI API completed successfully."
        )
