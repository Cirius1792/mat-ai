import time
from datetime import datetime

import pytest

from configuration import FiltersConfig
from matai.commands.process_new_emails_command import ProcessNewEmailsCommand
from matai.manager.models import RunConfiguration, ExecutionReport, RunStatus


class DummyRunConfigDAO:
    def __init__(self, last=None):
        self._last = last
        self.stored = []

    def retrieve_last(self):
        return self._last

    def store(self, run_config: RunConfiguration):
        # simulate assigning an ID on store
        run_config.configuration_id = 123
        self._last = run_config
        self.stored.append(run_config)


class DummyExecutionReportDAO:
    def __init__(self):
        self.stored = []

    def store(self, report: ExecutionReport):
        # simulate assigning an ID on store
        report.report_id = 321
        self.stored.append(report)


class DummyIntegrationManager:
    def __init__(self):
        self.created = []

    def create_tasks(self, actionable_item):
        self.created.append(actionable_item)


class DummyEmailManager:
    def __init__(self, to_process):
        self.to_process = to_process
        self.stored = []

    def process_new_emails(self, run_conf, filters):
        return list(self.to_process)

    def store_processed_emails(self, processed):
        self.stored.append(processed)


@pytest.fixture(autouse=True)
def freeze_time(monkeypatch):
    # freeze time.perf_counter for deterministic execution time
    monkeypatch.setattr(time, 'perf_counter', lambda: 1.0)
    yield


def make_action(email, score):
    from matai.email_processing.model import ActionItem, ActionType, Participant
    return ActionItem(
        action_type=ActionType.TASK,
        description='desc',
        confidence_score=score,
        message_id=email.message_id,
        due_date=None,
        owners=[Participant(alias='o')],
        waiters=[],
        metadata={}
    )


def make_email(mid='e1'):
    from matai.email_processing.model import EmailContent, EmailAddress
    return EmailContent(
        message_id=mid,
        subject='subj',
        sender=EmailAddress.from_string('a@b.com'),
        recipients=[],
        thread_id=mid,
        timestamp=datetime(2025,1,1),
        raw_content='body'
    )


class TestProcessNewEmailsCommand:
    """Integration tests for ProcessNewEmailsCommand."""

    def setup_method(self):
        # common fakes
        self.run_dao = DummyRunConfigDAO(last=None)
        self.exec_dao = DummyExecutionReportDAO()
        self.integration = DummyIntegrationManager()
        self.filters = FiltersConfig(recipients=[])

    @pytest.mark.parametrize('items,threshold,exp_emails,exp_actions', [
        ([], 0.5, 0, 0),
        ([('e1', 0.4)], 0.5, 0, 0),
        ([('e1', 0.6)], 0.5, 1, 1),
        ([('e1', 0.6), ('e2', 0.7)], 0.5, 2, 2),
    ])
    def test_execute_various_confidences(self, items, threshold, exp_emails, exp_actions):
        # prepare dummy managed_emails
        managed = [(make_email(mid), [make_action(make_email(mid), score)])
                   for mid, score in items]
        email_mgr = DummyEmailManager(managed)

        cmd = ProcessNewEmailsCommand(
            run_configuration_dao=self.run_dao,
            email_manager=email_mgr,
            filters=self.filters,
            integration_manager=self.integration,
            execution_report_dao=self.exec_dao,
            confidence_level=threshold
        )
        cmd.execute()

        # verify run configuration & execution report stored
        assert len(self.run_dao.stored) == 1
        assert len(self.exec_dao.stored) == 1
        report = self.exec_dao.stored[0]
        assert report.run_status == RunStatus.SUCCESS
        assert report.retrieved_emails == exp_emails
        assert report.generated_action_items == exp_actions
        assert report.report_id == 321

        # integration & storage calls reflect threshold
        assert len(self.integration.created) == exp_emails
        assert len(email_mgr.stored) == exp_emails

    def test_run_history_filters_by_last_run(self, monkeypatch):
        # patch datetime.now in the command module for controlled timestamps
        import matai.commands.process_new_emails_command as cmd_mod
        t1 = datetime(2025, 1, 1, 10, 0, 0)
        t2 = datetime(2025, 1, 1, 11, 0, 0)
        times = [t1, t2]
        class DummyDateTime:
            @classmethod
            def now(cls):
                return times.pop(0)
        monkeypatch.setattr(cmd_mod, 'datetime', DummyDateTime)

        seen = []
        class CaptureEmailManager:
            def process_new_emails(self, run_conf, filters):
                seen.append(run_conf.last_run_time)
                return []
            def store_processed_emails(self, processed): pass

        email_mgr = CaptureEmailManager()
        cmd = ProcessNewEmailsCommand(
            run_configuration_dao=self.run_dao,
            email_manager=email_mgr,
            filters=self.filters,
            integration_manager=self.integration,
            execution_report_dao=self.exec_dao,
            confidence_level=0.0
        )
        # first execution => last_run_time None
        cmd.execute(); assert seen[0] is None
        # second execution => last_run_time == t1
        cmd.execute(); assert seen[1] == t1