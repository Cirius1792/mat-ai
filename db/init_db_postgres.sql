DROP VIEW IF EXISTS action_items_with_email_subjects;
DROP TABLE IF EXISTS action_item_participants;
DROP TABLE IF EXISTS action_items;
DROP TABLE IF EXISTS email_contents;

-- Create the email_contents table
CREATE TABLE IF NOT EXISTS email_contents (
    message_id VARCHAR PRIMARY KEY,
    thread_id VARCHAR NOT NULL,
    subject TEXT NOT NULL,
    sender VARCHAR NOT NULL,
    recipients TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

-- Create the action_items table
CREATE TABLE IF NOT EXISTS action_items (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR NOT NULL, -- Use VARCHAR for text fields
    description TEXT NOT NULL,
    due_date TIMESTAMP, -- TIMESTAMP is the same in PostgreSQL
    confidence_score REAL NOT NULL,
    message_id VARCHAR NOT NULL REFERENCES email_contents(message_id),
    dismiss BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Use JSONB type for JSON data
    owners_ids VARCHAR[] DEFAULT '{}' NOT NULL,
    waiters_ids VARCHAR[] DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the action_item_participants table to hold both owners and waiters.
CREATE TABLE IF NOT EXISTS action_item_participants (
    id SERIAL PRIMARY KEY,
    alias VARCHAR NOT NULL
);


-- Create a view to combine action items with email subjects
CREATE VIEW action_items_with_email_subjects AS
SELECT 
    ai.id AS action_item_id,
    ai.action_type,
    ai.description,
    ai.due_date,
    ai.confidence_score,
    ai.dismiss,
    ai.metadata,
    ai.created_at,
    ec.subject AS email_subject
FROM 
    action_items ai
JOIN 
    email_contents ec ON ai.message_id = ec.message_id;
