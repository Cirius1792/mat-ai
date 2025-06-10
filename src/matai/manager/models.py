from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


@dataclass
class RunConfiguration:
    confidence_threshold: float = 0.85
    configuration_id: Optional[int] = None
    last_run_time: Optional[datetime] = None


class RunStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclass
class ExecutionReport:
    configuration_id: int
    run_status: RunStatus
    retrieved_emails: int
    generated_action_items: int
    report_id: Optional[int] = None
    run_time: datetime = field(default_factory=datetime.now)
    total_execution_time: Optional[float] = 0.0

    def __str__(self):
        """Returns a string conaining a table with all the data stored in the Execution Report"""
        time = 'NA' if self.total_execution_time is None else f"{int(self.total_execution_time//60)} m {int(self.total_execution_time % 60)} s"
        return f"""
        Configuration ID: {self.configuration_id}
        Run Time: {self.run_time}
        Run Status: {self.run_status}
        Retrieved Emails: {self.retrieved_emails}
        Generated Action Items: {self.generated_action_items}
        Total Execution Time: {time}
        """
