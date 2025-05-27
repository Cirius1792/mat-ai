from abc import ABC, abstractmethod
from typing import Optional, List

from matai.manager.models import ExecutionReport, RunConfiguration


class RunConfigurationDAO(ABC):

    @abstractmethod
    def store(self, run_configuration: RunConfiguration) -> RunConfiguration:
        """Creates a run configuration or updates an existing one if the run_configuration provided already has an id 
        Args:
            run_configuration (RunConfiguration): The run configuration to be stored
        Returns:
            RunConfiguration: The created or updated run configuration
        """
        pass

    @abstractmethod
    def retrieve_last(self) -> Optional[RunConfiguration]:
        """Retrieves the last run configuration stored
        Returns:
            RunConfiguration: The last run configuration stored
        """
        pass


class ExecutionReportDAO(ABC):

    @abstractmethod
    def store(self, execution_report: ExecutionReport) -> ExecutionReport:
        """ Creates an execution report or updates an existing one if the execution_report provided already has an id
        Args: 
            execution_report: the execution report to be stored
        Returns:
            ExecutionReport: the stored execution report
            """
        pass

    @abstractmethod
    def retrieve_last(self, num:int = 1) -> List[ExecutionReport]:
        """Retrieves the last execution reports stored
        Arggs:
            num (int): The number of execution reports to be retrieved
        Returns:
            ExecutionReport: The last execution report stored
        """
        pass
