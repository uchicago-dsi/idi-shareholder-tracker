"""Services used throughout the Django project.
"""

# Application imports
from common.models import Task
from typing import List

# Third-party imports
from django.core.exceptions import MultipleObjectsReturned
from django.db import (
    DatabaseError,
    IntegrityError,
    OperationalError,
)


class TaskService:
    """Provides CRUD operations against `Task` entities."""

    @staticmethod
    def get_or_create(
        workflow_execution: str, task_type: str, url: str
    ) -> Task:
        """Fetches a task with the given name and
        workflow execution id from the database or
        creates it if it doesn't exist.

        Args:
            workflow_execution (`str`): The id of
                the parent workflow execution.

            task_type (`str`): The type of task to execute.

            url (`str`): The URL to process.

        Returns:
            (`Task`): The task.
        """
        try:
            task, _ = Task.objects.get_or_create(
                workflow_execution=workflow_execution,
                type=task_type,
                url=url,
                defaults=dict(
                    status=Task.Status.NOT_STARTED,
                ),
            )
            return task
        except (
            DatabaseError,
            IntegrityError,
            MultipleObjectsReturned,
            OperationalError,
        ) as e:
            raise RuntimeError(
                f'Error getting or creating new task "{task_type}" with '
                f'parent workflow execution id "{workflow_execution}". {e}'
            )

    @staticmethod
    def get_success_urls() -> List[str]:
        """Fetches the URLs of succeeded tasks.

        Args:
            `None`

        Returns:
            (`list` of `str`): The URLs.
        """
        return Task.objects.filter(
            status=Task.Status.SUCCESS.value
        ).values_list("url", flat=True)

    @staticmethod
    def get_active_data_tasks(workflow_execution: str) -> None:
        """ """
        return Task.objects.filter(
            workflow_execution=workflow_execution,
            type__in=[
                Task.TaskType.SCRAPE_FORM_13F_STOCKS.value,
                Task.TaskType.SCRAPE_FORM_13F_COVER_PAGE,
            ],
        ).exclude(status=Task.Status.SUCCESS)
