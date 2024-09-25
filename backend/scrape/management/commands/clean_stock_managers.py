"""Cleans Form 13F stock investments.
"""

# Standard library imports
import os

# Third-party imports
from concurrent.futures import ThreadPoolExecutor
from more_itertools import chunked
from django.core.management.base import BaseCommand

# Application imports
from common.logger import LoggerFactory
from scrape.services import ScrapedForm13FStockService
from scrape.workflows import clean


class Command(BaseCommand):
    """A Django management command that cleans Form 13F stock investments
    by populating a database table linking cleaned names to investment ids.

    References:
    - https://docs.djangoproject.com/en/4.1/howto/custom-management-commands/
    - https://docs.djangoproject.com/en/4.1/topics/settings/
    """

    help = "Associates Form 13F stock investments with cleaned manager names."
    name = "Clean Form 13F Stock Managers"

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
            "Received request to clean Form 13F stock manager names."
        )

        # Iterate through investments
        for batch in ScrapedForm13FStockService.yield_managers(
            batch_size=10_000
        ):
            # Request filing URLs and scrape for data based on form type
            try:
                self._logger.info("Processing batch of manager fields.")
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(clean, chunked(batch, 1000))
            except Exception as e:
                err_msg = f"Failed to execute thread pool executor. {e}"
                self._logger.error(err_msg)
                exit(1)

        # Log success
        self._logger.info(
            "Completed cleaning of Form 13F stock manager names successfully."
        )
