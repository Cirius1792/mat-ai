import json
from datetime import datetime
from typing import List, Optional
from matai.email_processing.model import ActionItem, EmailContent, ActionType, EmailAddress, Participant
from matai.dao.interface import ActionItemDAO, EmailContentDAO, ParticipantDAO


class SQLiteActionItemDAO(ActionItemDAO):
    def __init__(self, connection):
        self._connection = connection

    def _connect(self):
        return self._connection

    def create_action_item(self, action_item: ActionItem) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO action_items (action_type, description, due_date, confidence_score, message_id, metadata, owners_ids, waiters_ids) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    action_item.action_type.name,
                    action_item.description,
                    action_item.due_date.strftime('%Y-%m-%d %H:%M:%S') if action_item.due_date else None,
                    action_item.confidence_score,
                    action_item.message_id,
                    json.dumps(action_item.metadata),
                    json.dumps([o.alias for o in action_item.owners]),
                    json.dumps([w.alias for w in action_item.waiters])
                )
            )
            conn.commit()
            action_item.id = cursor.lastrowid

    def get_action_item(self, action_item_id: int) -> Optional[ActionItem]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM action_items WHERE id = ?", (action_item_id,))
            row = cursor.fetchone()
            if row:
                owners = [Participant(alias=a) for a in json.loads(row[8])] if row[8] else []
                waiters = [Participant(alias=a) for a in json.loads(row[9])] if row[9] else []
                return ActionItem(
                    id=row[0],
                    action_type=ActionType[row[1]],
                    description=row[2],
                    due_date=datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S') if row[3] else None,
                    owners=owners,
                    waiters=waiters,
                    metadata=json.loads(row[7]),
                    confidence_score=row[4],
                    message_id=row[5]
                )
            return None

    def update_action_item(self, action_item: ActionItem) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE action_items SET action_type = ?, description = ?, due_date = ?, confidence_score = ?, message_id = ?, metadata = ?, owners_ids = ?, waiters_ids = ? WHERE id = ?",
                (
                    action_item.action_type.name,
                    action_item.description,
                    action_item.due_date.strftime('%Y-%m-%d %H:%M:%S') if action_item.due_date else None,
                    action_item.confidence_score,
                    action_item.message_id,
                    json.dumps(action_item.metadata),
                    json.dumps([o.alias for o in action_item.owners]),
                    json.dumps([w.alias for w in action_item.waiters]),
                    action_item.id
                )
            )
            conn.commit()

    def delete_action_item(self, action_item_id: int) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM action_items WHERE id = ?", (action_item_id,))
            conn.commit()

    def delete_all_action_items(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM action_items")
            conn.commit()

    def list_action_items(self) -> List[ActionItem]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM action_items")
            rows = cursor.fetchall()
            return_items = []
            for row in rows:
                owners = [Participant(alias=a) for a in json.loads(row[8])] if row[8] else []
                waiters = [Participant(alias=a) for a in json.loads(row[9])] if row[9] else []
                return_items.append(ActionItem(
                    id=row[0],
                    action_type=ActionType[row[1]],
                    description=row[2],
                    due_date=datetime.fromisoformat(row[3]) if row[3] else None,
                    owners=owners,
                    waiters=waiters,
                    metadata=json.loads(row[7]),
                    confidence_score=row[4],
                    message_id=row[5]
                ))
            return return_items


class SQLiteParticipantDAO(ParticipantDAO):
    def __init__(self, connection):
        self._connection = connection

    def _connect(self):
        return self._connection

    def create_participant(self, participant: Participant) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO action_item_participants (alias) VALUES (?)",
                (participant.alias,)
            )
            conn.commit()

    def get_participant(self, alias: str) -> Optional[Participant]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT alias FROM action_item_participants WHERE alias = ?",
                (alias,)
            )
            row = cursor.fetchone()
            return Participant(alias=row[0]) if row else None

    def update_participant(self, participant: Participant) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE action_item_participants SET alias = ? WHERE alias = ?",
                (participant.alias, participant.alias)
            )
            conn.commit()

    def delete_participant(self, alias: str) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM action_item_participants WHERE alias = ?",
                (alias,)
            )
            conn.commit()

    def delete_all_participants(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM action_item_participants")
            conn.commit()

    def list_participants(self) -> List[Participant]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alias FROM action_item_participants")
            rows = cursor.fetchall()
            return [Participant(alias=row[0]) for row in rows]
            action_item.id = cursor.lastrowid

    def get_action_item(self, action_item_id: int) -> Optional[ActionItem]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM action_items WHERE id = ?", (action_item_id,))
            row = cursor.fetchone()
            if row:
                owners = [Participant(alias=a) for a in json.loads(row[8])] if row[8] else []
                waiters = [Participant(alias=a) for a in json.loads(row[9])] if row[9] else []
                return ActionItem(
                    id=row[0],
                    action_type=ActionType[row[1]],
                    description=row[2],
                    due_date=datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S') if row[3] else None,
                    owners=owners,
                    waiters=waiters,
                    metadata=json.loads(row[7]),
                    confidence_score=row[4],
                    message_id=row[5]
                )
            return None

    def update_action_item(self, action_item: ActionItem) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE action_items SET action_type = ?, description = ?, due_date = ?, confidence_score = ?, message_id = ?, metadata = ?, owners_ids = ?, waiters_ids = ? WHERE id = ?",
                (
                    action_item.action_type.name,
                    action_item.description,
                    action_item.due_date.strftime('%Y-%m-%d %H:%M:%S') if action_item.due_date else None,
                    action_item.confidence_score,
                    action_item.message_id,
                    json.dumps(action_item.metadata),
                    json.dumps([o.alias for o in action_item.owners]),
                    json.dumps([w.alias for w in action_item.waiters]),
                    action_item.id
                )
            )
            conn.commit()

    def delete_action_item(self, action_item_id: int) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM action_items WHERE id = ?", (action_item_id,))
            conn.commit()

    def delete_all_action_items(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM action_items")
            conn.commit()

    def list_action_items(self) -> List[ActionItem]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM action_items")
            rows = cursor.fetchall()
            return_items = []
            for row in rows:
                owners = [Participant(alias=a) for a in json.loads(row[8])] if row[8] else []
                waiters = [Participant(alias=a) for a in json.loads(row[9])] if row[9] else []
                return_items.append(ActionItem(
                    id=row[0],
                    action_type=ActionType[row[1]],
                    description=row[2],
                    due_date=datetime.fromisoformat(row[3]) if row[3] else None,
                    owners=owners,
                    waiters=waiters,
                    metadata=json.loads(row[7]),
                    confidence_score=row[4],
                    message_id=row[5]
                ))
            return return_items


class SQLiteEmailContentDAO(EmailContentDAO):
    def __init__(self, connection):
        self._connection = connection

    def _connect(self):
        return self._connection

    def create_email_content(self, email_content: EmailContent) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO email_contents (message_id, subject, sender, recipients, thread_id, timestamp, raw_content) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (email_content.message_id, email_content.subject, email_content.sender.to_string(), json.dumps([r.to_string(
                ) for r in email_content.recipients]), email_content.thread_id, email_content.timestamp.strftime('%Y-%m-%d %H:%M:%S'), email_content.raw_content)
            )
            conn.commit()

    def get_email_content(self, message_id: str) -> Optional[EmailContent]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id, subject, sender, recipients, thread_id, timestamp, raw_content FROM email_contents WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            if row:
                return EmailContent(
                    message_id=row[0],
                    subject=row[1],
                    sender=EmailAddress.from_string(row[2]),
                    recipients=[EmailAddress.from_string(
                        r) for r in json.loads(row[3])],
                    thread_id=row[4],
                    timestamp=datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S'),
                    raw_content=row[6]
                )
            return None

    def update_email_content(self, email_content: EmailContent) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE email_contents SET subject = ?, sender = ?, recipients = ?, thread_id = ?, timestamp = ?, raw_content = ? WHERE message_id = ?",
                (email_content.subject, email_content.sender.to_string(), json.dumps([r.to_string(
                ) for r in email_content.recipients]), email_content.thread_id, email_content.timestamp.strftime('%Y-%m-%d %H:%M:%S'), email_content.raw_content, email_content.message_id)
            )
            conn.commit()

    def delete_email_content(self, message_id: str) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM email_contents WHERE message_id = ?", (message_id,))
            conn.commit()

    def list_email_contents(self, timestamp_from: Optional[datetime] = None) -> List[EmailContent]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if timestamp_from:
                cursor.execute("SELECT message_id, subject, sender, recipients, thread_id, timestamp, raw_content FROM email_contents WHERE timestamp > ?", (timestamp_from.strftime('%Y-%m-%d %H:%M:%S'),))
            else:
                cursor.execute("SELECT message_id, subject, sender, recipients, thread_id, timestamp, raw_content FROM email_contents")
            rows = cursor.fetchall()
            return [
                EmailContent(
                    message_id=row[0],
                    subject=row[1],
                    sender=EmailAddress.from_string(row[2]),
                    recipients=[EmailAddress.from_string(
                        r) for r in json.loads(row[3])],
                    thread_id=row[4],
                    timestamp=datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S'),
                    raw_content=row[6]
                )
                for row in rows
            ]

    def delete_all_email_contents(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM email_contents")
            conn.commit()
