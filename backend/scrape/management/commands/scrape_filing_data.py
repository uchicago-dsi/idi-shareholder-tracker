"""Scrapes SEC filing data.
"""

# Standard library imports
import os
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from more_itertools import chunked

# Third-party imports
from django.db import connections
from django.core.management.base import BaseCommand

# Application imports
from common.logger import LoggerFactory
from common.services import TaskService
from scrape.scrapers import EDGAR_RATE_LIMIT_IN_SECONDS
from scrape.workflows import process_data_task


class Command(BaseCommand):
    """A Django management command that requests and scrapes
    a filing detail webpage to get one or more URLs leading
    to data (e.g., Form 13F stock information tables).

    References:
    - https://docs.djangoproject.com/en/4.1/howto/custom-management-commands/
    - https://docs.djangoproject.com/en/4.1/topics/settings/
    """

    help = "Scrapes SEC filing data."
    name = "Scrape Filing Details"

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
        self._logger.info("Received request to scrape SEC filing data.")

        # Fetch uncompleted data scraping tasks
        self._logger.info("Fetching active data scraping tasks.")
        tasks = TaskService.get_active_data_tasks(self._workflow_execution)
        self._logger.info(f"{len(tasks):,} task(s) found.")

        # End successfully if no tasks exist
        if not tasks:
            self._logger.info("Process completed successfully.")
            exit(0)

        # Otherwise, close all active database connections
        connections.close_all()

        # Process batches of filings in parallel
        for batch in chunked(tasks, n=EDGAR_RATE_LIMIT_IN_SECONDS):

            # Request filing URLs and scrape for data based on form type
            try:
                with ThreadPoolExecutor(
                    max_workers=EDGAR_RATE_LIMIT_IN_SECONDS
                ) as executor:
                    executor.map(
                        process_data_task,
                        batch,
                        repeat(self._workflow_execution),
                        repeat(self._logger),
                    )
            except Exception as e:
                err_msg = f"Failed to execute thread pool executor. {e}"
                self._logger.error(err_msg)
                exit(1)

            # Sleep for one second between batch of calls
            time.sleep(1)

        # Log success
        self._logger.info("Filing data scrape completed successfully.")
