"""Factories used throughout the application.
"""

# Standard library imports
import logging
from abc import ABC, abstractmethod

# Application imports
from common.models import Task
from common.services import TaskService
from scrape.models import ScrapedCompanyFiling
from scrape.scrapers import (
    Form13FCoverPageScraper,
    Form13FFilingDetailsScraper,
    Form13FStockScraper,
)
from scrape.services import (
    ScrapedForm13FManagerService,
    ScrapedForm13FStockService,
)

# Application imports
from scrape.clean import parse_stock_manager_field
from scrape.models import CleanForm13StockManager
from scrape.services import (
    ScrapedForm13FManagerService,
    ScrapedForm13FStockService,
)


class EdgarWorkflow(ABC):
    """A template workflow for completing SEC EDGAR webscraping tasks."""

    @abstractmethod
    def execute(
        self,
        url: str,
        parent_workflow_execution_id: str,
        logger: logging.Logger,
    ) -> None:
        """Executes the workflow.

        Args:
            url (`str`): The URL to request.

            parent_workflow_execution_id (`str`): The id
                of the remote parent workflow orchestrating
                the task.

            logger (`logging.Logger`): A standard logger instance.

        Returns:
            `None`
        """
        raise NotImplementedError


class Form13FFilingDetailWorkflow(EdgarWorkflow):
    """A workflow for scraping stock information
    table URLs from Form 13F filing webpages.
    """

    def execute(
        self,
        url: str,
        parent_workflow_execution_id: str,
        logger: logging.Logger,
    ) -> None:
        """Executes the workflow.

        Args:
            url (`str`): The URL to request.

            parent_workflow_execution_id (`str`): The id
                of the remote parent workflow orchestrating
                the task.

            logger (`logging.Logger`): A standard logger instance.

        Returns:
            `None`
        """
        try:
            # Fetch task or create if doesn't exist
            task = TaskService.get_or_create(
                workflow_execution=parent_workflow_execution_id,
                task_type=Task.TaskType.SCRAPE_FORM_13F_FILING_DETAILS,
                url=url,
            )

            # Mark task in progress
            task.start()

            # Instantiate scraper
            scraper = Form13FFilingDetailsScraper(logger)

            # Scrape webpage for URL
            info_table_url, cover_page_url = scraper.scrape(url)

            # Create new task to scrape information table URL
            TaskService.get_or_create(
                workflow_execution=parent_workflow_execution_id,
                task_type=Task.TaskType.SCRAPE_FORM_13F_STOCKS,
                url=info_table_url,
            )

            # Create new task to scrape cover page URL
            TaskService.get_or_create(
                workflow_execution=parent_workflow_execution_id,
                task_type=Task.TaskType.SCRAPE_FORM_13F_COVER_PAGE,
                url=cover_page_url,
            )

            # Mark existing task as success
            task.mark_success()

        except Exception as e:
            logger.error(
                f"Failed to scrape and process Form 13F filing page. {e}"
            )
            task.mark_failure(str(e))


class Form13FCoverPageWorkflow(EdgarWorkflow):
    """A workflow for scraping manager names
    from a Form 13F information table.
    """

    def execute(
        self,
        url: str,
        parent_workflow_execution_id: str,
        logger: logging.Logger,
    ) -> None:
        """Executes the workflow.

        Args:
            url (`str`): The URL to request.

            parent_workflow_execution_id (`str`): The id
                of the remote parent workflow orchestrating
                the task.

            logger (`logging.Logger`): A standard logger instance.

        Returns:
            `None`
        """
        try:
            # Fetch task
            task = TaskService.get_or_create(
                workflow_execution=parent_workflow_execution_id,
                task_type=Task.TaskType.SCRAPE_FORM_13F_COVER_PAGE,
                url=url,
            )

            # Mark task in progress
            task.start()

            # Instantiate scraper
            scraper = Form13FCoverPageScraper(logger)

            # Scrape webpage for URL
            managers = scraper.scrape(url)

            # Bulk insert investments, while ignoring conflicts
            ScrapedForm13FManagerService.bulk_insert(managers)

            # Mark existing task as success
            task.mark_success()

        except Exception as e:
            logger.error(
                f"Failed to scrape and process Form 13F managers. {e}"
            )
            task.mark_failure(str(e))


class Form13FStockWorkflow(EdgarWorkflow):
    """A workflow for scraping stock metadata
    from a Form 13F information table.
    """

    def execute(
        self,
        url: str,
        parent_workflow_execution_id: str,
        logger: logging.Logger,
    ) -> None:
        """Executes the workflow.

        Args:
            url (`str`): The URL to request.

            parent_workflow_execution_id (`str`): The id
                of the remote parent workflow orchestrating
                the task.

            logger (`logging.Logger`): A standard logger instance.

        Returns:
            `None`
        """
        try:
            # Fetch task
            task = TaskService.get_or_create(
                workflow_execution=parent_workflow_execution_id,
                task_type=Task.TaskType.SCRAPE_FORM_13F_STOCKS,
                url=url,
            )

            # Mark task in progress
            task.start()

            # Instantiate scraper
            scraper = Form13FStockScraper(logger)

            # Scrape webpage for URL
            investments = scraper.scrape(url)

            # Bulk insert investments, while ignoring conflicts
            ScrapedForm13FStockService.bulk_insert(investments)

            # Mark existing task as success
            task.mark_success()

        except Exception as e:
            logger.error(f"Failed to scrape and process Form 13F stocks. {e}")
            task.mark_failure(str(e))


class FilingDetailWorkflowFactory:
    """A simple factory for selecting filing detail scraping workflows."""

    @staticmethod
    def create(form_type: str) -> EdgarWorkflow:
        """Creates the appropriate SEC EDGAR workflow based on form type.

        Raises:
            `ValueError` if the given form type is not
                associated with a workflow.

        Args:
            form_type (`str`): The form type (e.g., "13F-HR").

        Returns:
            (`EdgarScraper`): A concrete instance of an EDGAR scraper.
        """
        if ScrapedCompanyFiling.FormType.FORM_13F_HR.value == form_type:
            return Form13FFilingDetailWorkflow()
        else:
            raise ValueError(
                f'The given form type, "{form_type}", '
                "is not associated with a workflow."
            )


class FilingDataWorkflowFactory:
    """A simple factory for selecting filing data scraping workflows."""

    @staticmethod
    def create(task_type: str) -> EdgarWorkflow:
        """Creates the appropriate SEC EDGAR workflow based on task type.

        Raises:
            `ValueError` if the given task type is not
                associated with a workflow.

        Args:
            task_type (`str`): The task type (e.g., "Scrape Form 13F Stocks").

        Returns:
            (`EdgarScraper`): A concrete instance of an EDGAR scraper.
        """
        if Task.TaskType.SCRAPE_FORM_13F_STOCKS.value == task_type:
            return Form13FStockWorkflow()
        elif Task.TaskType.SCRAPE_FORM_13F_COVER_PAGE.value == task_type:
            return Form13FCoverPageWorkflow()
        else:
            raise ValueError(
                f'The given task type, "{task_type}", '
                "is not associated with a workflow."
            )


def process_filing_task(
    filing: ScrapedCompanyFiling, workflow_execution, logger
) -> None:
    """Executes the workflow corresponding to the filing."""
    workflow = FilingDetailWorkflowFactory.create(filing.form)
    workflow.execute(filing.url, workflow_execution, logger)
    from django.db import connection

    connection.close()


def process_data_task(task: Task, workflow_execution, logger) -> None:
    """Executes the workflow corresponding to the filing."""
    workflow = FilingDataWorkflowFactory.create(task.type)
    workflow.execute(task.url, workflow_execution, logger)
    from django.db import connection

    connection.close()


def clean(batch):
    cleaned = []
    for stock in batch:
        for manager in parse_stock_manager_field(stock.names):
            if isinstance(manager, int):
                name = ScrapedForm13FManagerService.get_manager_name(
                    form_id=stock.form_id, manager_number=manager
                )
            else:
                name = manager

            if name:
                cleaned.append(
                    CleanForm13StockManager(stock_id=stock.stock_id, name=name)
                )

    CleanForm13StockManager.objects.bulk_create(
        objs=cleaned,
        batch_size=10_000,
        ignore_conflicts=True,
    )
    from django.db import connection

    connection.close()
