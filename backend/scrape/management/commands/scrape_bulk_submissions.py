"""Streams a zipfile of SEC submissions to extract companies with filings.
"""

# Standard library imports
import os
from datetime import datetime, timezone, timedelta

# Third-party imports
from django.db import DatabaseError, IntegrityError
from django.core.management.base import BaseCommand, CommandParser

# Application imports
from common.logger import LoggerFactory
from common.models import Task
from common.services import TaskService
from scrape.scrapers import BulkSubmissionsScraper
from scrape.services import ScrapedCompanyService


class Command(BaseCommand):
    """A Django management command that streams and unzips a bulk
    archive file of submissions from the SEC website, in the process
    scraping and persisting to the database companies with filings of
    a given form type and between a given date range.

    References:
    - https://docs.djangoproject.com/en/4.1/howto/custom-management-commands/
    - https://docs.djangoproject.com/en/4.1/topics/settings/
    """

    help = "Streams and processes SEC bulk submissions data."
    name = "Scrape Bulk Submissions"

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

    def add_arguments(self, parser: CommandParser) -> None:
        """Permits the caller to specify a `--form_types` option
        indicating which SEC form(s) should be scraped and a
        `--lookback-in-days` option to indicate the date range
        that should be scraped—from _N_ days ago through the present,
        inclusive. The defaults are "13F-HR" and 365, respectively.

        Args:
            parser (`CommandParser`)

        Returns:
            `None`
        """
        parser.add_argument(
            "--form-types",
            nargs="+",
            type=str,
            choices=["13F-HR"],
            default=["13F-HR"],
        )
        parser.add_argument(
            "--lookback-in-days",
            nargs=1,
            type=int,
            default=365,
        )

    def handle(self, *args, **options) -> None:
        """Executes the command.

        Args:
            `None`

        Returns:
            `None`
        """
        # Log start of processing
        self._logger.info(
            "Received request to download and scrape company "
            "submissions in bulk from the SEC website."
        )

        # Instantiate scraper
        submissions_scraper = BulkSubmissionsScraper(self._logger)

        # Get or create task related to invocation id
        try:
            task = TaskService.get_or_create(
                workflow_execution=self._workflow_execution,
                task_type=Task.TaskType.SCRAPE_BULK_SUBMISSIONS,
                url=submissions_scraper.submissions_file_url,
            )
        except Exception as e:
            self._logger.error(f"Bulk submissions scrape failed. {e}")
            exit(1)

        # Set date range to query company filings
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=365)

        # Orchestrate scrape
        self._logger.info(
            f"Scraping submissions with form type(s) "
            f"{', '.join(options['form_types'])} and "
            f"filing dates between {start.isoformat()} "
            f"and {end.isoformat()}, inclusive."
        )
        try:
            # Stream file and process companies
            for companies in submissions_scraper.scrape(
                form_types=options["form_types"],
                start_date=start,
                end_date=end,
                batch_size=61,
            ):
                self._logger.info(
                    f"Upserting {len(companies):,} company "
                    "record(s) into the database."
                )
                num_created_companies, num_upserted_companies, num_filings = (
                    ScrapedCompanyService.upsert(companies)
                )
                self._logger.info(
                    f"{num_created_companies} company record(s) "
                    f"successfully created and {num_upserted_companies:,} "
                    f"updated, containing a total of {num_filings:,} "
                    "filing(s)."
                )

        except (DatabaseError, IntegrityError) as e:
            err_msg = (
                f"Error upserting companies with filings into database. {e}"
            )
            self._logger.error(f"Bulk submissions scrape failed. {err_msg}")
            task.mark_failure(err_msg)
            exit(1)
        except Exception as e:
            err_msg = f"Error processing companies with filings. {e}"
            self._logger.error(f"Bulk submissions scrape failed. {err_msg}")
            task.mark_failure(err_msg)
            exit(1)

        # Log success and update task in database
        self._logger.info("Bulk submissions scrape completed successfully.")
        task.mark_success()
