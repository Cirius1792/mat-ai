import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
from collections import namedtuple
"""Implement an SQLite DAO to store the processed emails. No sensible informations will be stored in the database, but only the minimal set of information required to keep track of what email has been elaborated and when. 

The database table, named PROCESSED_EMAIL contains the following information: 
    - message_id: the unique identifier of the email
    - message_date: the date of the email
    - processed: the status of the email, can be one of the following: 
        - PROCESSED
        - FAILED
        - SKIPPED
    - process_date: the date when the email has been processed, if not provided, the current datetime will be used.
"""

ProcessedEmails = namedtuple('ProcessedEmails', ['message_id', 'message_date', 'process_state', 'process_date'])

class EmailStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS PROCESSED_EMAIL (
                message_id TEXT PRIMARY KEY,
                message_date TEXT NOT NULL,
                process_state TEXT NOT NULL,
                process_date TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def store(self, message_id: str,
              message_date: datetime,
              process_state: str,
              process_date: Optional[datetime] = None):
        """ Store a record containing the message id, the message date and the processed status. 
        The status can be: 
            - PROCESSED
            - FAILED
            - SKIPPED
        If no process datetime is provided, the current datetime will be used. 
        """
        if process_date is None:
            process_date = datetime.now()

        self.cursor.execute("""
            INSERT OR REPLACE INTO PROCESSED_EMAIL (message_id, message_date, process_state, process_date)
            VALUES (?, ?, ?, ?)
        """, (message_id, message_date.isoformat(), process_state, process_date.isoformat()))
        self.conn.commit()

    def retrieve_from(self, message_date: datetime, state_in:List[str]=[]) -> List[ProcessedEmails]:
        """ Retrieve all records from the store that are newer than the given date."""
        query = """
            SELECT message_id, message_date, process_state, process_date 
            FROM PROCESSED_EMAIL 
            WHERE message_date >= ?
        """
        parameters = (message_date.isoformat(),)
        if state_in:
            query += " AND process_state IN ({})".format(','.join('?' for _ in state_in))
            parameters = (parameters[0], *state_in)
        self.cursor.execute(query, parameters)

        return self.cursor.fetchall()

    def was_processed(self, message_id: str, process_state: str = 'PROCESSED') -> bool:
        """Check if an email with the given message_id has already been processed."""
        self.cursor.execute(
            "SELECT 1 FROM PROCESSED_EMAIL WHERE message_id = ? and process_state = ?", (message_id, process_state,))
        return self.cursor.fetchone() is not None

    def close(self):
        self.conn.close()


class ActionItemStore:
    def get_all_action_items(self):
        pass

    def get_all_emails(self):
        pass

    def get_email_by_id(self, email_id):
        pass

    def get_last_n_runs(self, num_runs):
        pass
