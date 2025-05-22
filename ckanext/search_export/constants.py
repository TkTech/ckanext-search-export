import enum


class Status(enum.StrEnum):
    """
    Enum for the status of the export job.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
