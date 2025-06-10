from typing import Optional, List
from matai.manager.dao import ExecutionReportDAO, RunConfigurationDAO
from matai.manager.models import RunConfiguration, ExecutionReport

from datetime import datetime
from matai.manager.models import RunStatus


class SQliteRunConfigurationDAO(RunConfigurationDAO):
    def __init__(self, connection):
        self._connection = connection

    def store(self, run_configuration: RunConfiguration) -> RunConfiguration:
        cursor = self._connection.cursor()

        if run_configuration.configuration_id is None:
            cursor.execute(
                """
                INSERT INTO run_configurations (confidence_threshold, last_run_time )
                VALUES (?, ?)
                """,
                (
                    run_configuration.confidence_threshold,
                    run_configuration.last_run_time or datetime.now(),
                ),
            )
            run_configuration.configuration_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                UPDATE run_configurations
                SET confidence_threshold = ?, last_run_time = ?
                WHERE configuration_id = ?
                """,
                (
                    run_configuration.confidence_threshold,
                    run_configuration.last_run_time or datetime.now(),
                    run_configuration.configuration_id,
                ),
            )

        self._connection.commit()
        return run_configuration

    def retrieve_last(self) -> Optional[RunConfiguration]:
        cursor = self._connection.cursor()

        cursor.execute(
            """
            SELECT configuration_id, confidence_threshold, last_run_time
            FROM run_configurations
            ORDER BY last_run_time DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if row:
            configuration_id, confidence_threshold, last_run_time  = row
            return RunConfiguration(
                configuration_id=configuration_id,
                confidence_threshold=confidence_threshold,
                last_run_time=datetime.fromisoformat(last_run_time),
            )
        else:
            return None


class SQLiteExecutionReportDAO(ExecutionReportDAO):
    def __init__(self, connection):
        self._connection = connection

    def store(self, execution_report: ExecutionReport) -> ExecutionReport:
        cursor = self._connection.cursor()
        # Check if execution_report has a report_id attribute; insert if not, update otherwise.
        if execution_report.report_id is None:
            cursor.execute(
                """
                INSERT INTO execution_reports (configuration_id, run_time, run_status, retrieved_emails, generated_action_items, total_execution_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_report.configuration_id,
                    execution_report.run_time.isoformat() if isinstance(
                        execution_report.run_time, datetime) else execution_report.run_time,
                    execution_report.run_status.value if hasattr(
                        execution_report.run_status, 'value') else execution_report.run_status,
                    execution_report.retrieved_emails,
                    execution_report.generated_action_items,
                    execution_report.total_execution_time
                ),
            )
            execution_report.report_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                UPDATE execution_reports
                SET configuration_id = ?, run_time = ?, run_status = ?, retrieved_emails = ?, generated_action_items = ?, total_execution_time = ?
                WHERE report_id = ?
                """,
                (
                    execution_report.configuration_id,
                    execution_report.run_time.isoformat() if isinstance(
                        execution_report.run_time, datetime) else execution_report.run_time,
                    execution_report.run_status.value if hasattr(
                        execution_report.run_status, 'value') else execution_report.run_status,
                    execution_report.retrieved_emails,
                    execution_report.generated_action_items,
                    execution_report.total_execution_time,
                    execution_report.report_id
                ),
            )
        self._connection.commit()
        return execution_report

    def retrieve_last(self, num: int = 1) -> List[ExecutionReport]:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT report_id, configuration_id, run_time, run_status, retrieved_emails, generated_action_items, total_execution_time
            FROM execution_reports
            ORDER BY run_time DESC
            LIMIT ?
            """,
            (num,)
        )
        rows = cursor.fetchall()
        if not rows:
            return []
        reports = []
        for row in rows:
            report_id, configuration_id, run_time, run_status_str, retrieved_emails, generated_action_items, total_execution_time = row
            reports.append(
                ExecutionReport(
                    configuration_id=configuration_id,
                    run_status=RunStatus(run_status_str),
                    retrieved_emails=retrieved_emails,
                    generated_action_items=generated_action_items,
                    report_id=report_id,
                    run_time=datetime.fromisoformat(run_time) if isinstance(run_time, str) else run_time,
                    total_execution_time=total_execution_time
                )
            )
        return reports
