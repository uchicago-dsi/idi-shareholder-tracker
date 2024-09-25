"""Models used across the application.
"""

# Standard library imports
import uuid
from datetime import datetime, timezone
from typing import Any

# Third-party imports
from django.db import models


class Task(models.Model):
    """Represents a generic task execution."""

    class TaskType(models.TextChoices):
        """Enumerates types of tasks."""

        FETCH_FORM_13F_STOCK_METADATA = "Fetch Form 13F Stock Metadata"
        SCRAPE_BULK_SUBMISSIONS = "Scrape Bulk Submissions"
        SCRAPE_FORM_13F_COVER_PAGE = "Scrape Form 13F Cover Page"
        SCRAPE_FORM_13F_FILING_DETAILS = "Scrape Form 13F Filing Details"
        SCRAPE_FORM_13F_STOCKS = "Scrape Form 13F Stocks"

    class Status(models.TextChoices):
        """Enumerates potential statuses for a task."""

        NOT_STARTED = "Not Started"
        IN_PROGRESS = "In Progress"
        ERROR = "Error"
        SUCCESS = "Success"

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    """The unique identifier for the job execution."""

    workflow_execution = models.CharField()
    """The id assigned to the larger workflow executing the task."""

    type = models.CharField(choices=TaskType)
    """The task name."""

    status = models.CharField(choices=Status, default=Status.IN_PROGRESS.value)
    """The task status."""

    started_at_utc = models.DateTimeField(auto_now_add=True)
    """The time the task started execution."""

    ended_at_utc = models.DateTimeField(null=True)
    """The time the task finished execution."""

    last_error_at_utc = models.DateTimeField(null=True)
    """The last time the task terminated with an error."""

    error = models.TextField(blank=True, default="")
    """The exception message."""

    num_retries = models.IntegerField(default=0)
    """The number of times the task has been reattempted."""

    url = models.URLField(null=True)
    """The URL associated with the task."""

    class Meta:
        db_table = "task"
        constraints = [
            models.UniqueConstraint(
                name="unique_task",
                fields=["workflow_execution", "type", "url"],
            )
        ]

    def start(self) -> None:
        """Updates the current task to mark its
        status as "In Progress" and its start time
        to the current time.

        Args:
            `None`

        Returns:
            `None`
        """
        self.status = self.Status.IN_PROGRESS.value
        self.started_at_utc = datetime.now(timezone.utc)
        self.save()

    def mark_failure(self, err_msg: Any) -> None:
        """Updates the current task with an error status,
        exception message, and error timestamp.

        Args:
            err_msg (`Any`): The exception.

        Returns:
            `None`
        """
        self.status = self.Status.ERROR.value
        self.error = err_msg
        self.last_error_at_utc = datetime.now(timezone.utc)
        self.save()

    def mark_success(self) -> None:
        """Updates the current job execution
        with a success status and timestamp.

        Args:
            `None`

        Returns:
            `None`
        """
        self.status = self.Status.SUCCESS.value
        self.ended_at_utc = datetime.now(timezone.utc)
        self.save()
