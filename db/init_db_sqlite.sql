-- Create the action_items table
CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL, -- Use TEXT for text fields
    description TEXT NOT NULL,
    due_date TIMESTAMP, -- TIMESTAMP; NULL if not provided
    confidence_score REAL NOT NULL,
    message_id TEXT NOT NULL,
    dismiss BOOLEAN DEFAULT 0,
    metadata TEXT,  -- JSON string for additional metadata
    owners_ids TEXT DEFAULT '[]' NOT NULL,
    waiters_ids TEXT DEFAULT '[]' NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);
-- Create the action_item_participants table to hold both owners and waiters.
CREATE TABLE IF NOT EXISTS action_item_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL
);

-- Create the email_contents table
CREATE TABLE IF NOT EXISTS email_contents (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipients TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS run_configurations (
    configuration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    confidence_threshold FLOAT NOT NULL,
    last_run_time TIMESTAMP DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS execution_reports(
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER NOT NULL,
    run_time TIMESTAMP NOT NULL,
    run_status TEXT NOT NULL,
    retrieved_emails INTEGER NOT NULL,
    generated_action_items INTEGER NOT NULL,
    total_execution_time FLOAT DEFAULT 0,
    FOREIGN KEY (configuration_id) REFERENCES run_configurations(configuration_id)
    )
