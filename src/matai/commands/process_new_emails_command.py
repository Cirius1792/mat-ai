import time
import logging
from configuration import FiltersConfig
from matai.integrations.integration_manager import IntegrationManager
from matai.manager.dao import ExecutionReportDAO, RunConfigurationDAO
from matai.manager.manager import EmailFilters, EmailManager
from matai.manager.models import ExecutionReport, RunConfiguration, RunStatus

logger = logging.getLogger(__name__)


class ProcessNewEmailsCommand:
    def __init__(self, run_configuration_dao : RunConfigurationDAO,
                 email_manager: EmailManager,
                filters: FiltersConfig,
                 integration_manager: IntegrationManager,
                 execution_report_dao: ExecutionReportDAO,
                confidence_level: float = 0.85,
                 ):
        self.run_configuration_dao : RunConfigurationDAO =run_configuration_dao
        self.email_manager: EmailManager = email_manager
        self.filters: FiltersConfig = filters
        self.confidence_level: float = confidence_level
        self.integration_manager: IntegrationManager= integration_manager
        self.execution_report_dao : ExecutionReportDAO = execution_report_dao

    def execute(self):
        # Add a meaningful documentation to this method specifiyng all the side effects that it triggers during the execution, for example the update of the run hystory AI!
        start_time = time.perf_counter()
        run_configuration = self.run_configuration_dao.retrieve_last()

        if run_configuration is None:
            run_configuration = RunConfiguration(last_run_time=None)

        managed_emails = self.email_manager.process_new_emails(
            run_configuration,EmailFilters(recipients=self.filters.recipients)
        )

        managed_emails_num=0
        generated_action_items=0
        for email_content, action_items in managed_emails:
            logger.debug("Retrieved Action Items: ", len(action_items))

            filtered_action_items = list(
                filter(lambda x: x.confidence_score >= self.confidence_level, action_items))

            if filtered_action_items:
                managed_emails_num += 1
                generated_action_items += len(filtered_action_items)
                logger.info("%s actionable items found in email %s", len(
                    filtered_action_items), email_content.subject)

                actionable_item = (email_content, filtered_action_items)
                self.integration_manager.create_tasks(actionable_item)
                self.email_manager.store_processed_emails([actionable_item])

        self.run_configuration_dao.store(run_configuration)
        # Store Execution Report
        elapsed_time = time.perf_counter() - start_time
        execution_report = self._build_execution_report(
            run_configuration, managed_emails_num,
            generated_action_items,
            elapsed_time)
        self.execution_report_dao.store(execution_report)
        assert execution_report.report_id is not None, "Execution Report was not stored correctly"

    def _build_execution_report(self, 
                                run_configuration: RunConfiguration,
                               managed_emails_num: int,
                               generated_action_items:int,
                               total_execution_time: float) -> ExecutionReport:

        assert run_configuration.configuration_id is not None, "Can't store an execution report without a valid run configuration"

        return ExecutionReport(
            configuration_id=run_configuration.configuration_id,
            run_status=RunStatus.SUCCESS,
            retrieved_emails=managed_emails_num,
            generated_action_items=generated_action_items,
            total_execution_time=total_execution_time
        )
