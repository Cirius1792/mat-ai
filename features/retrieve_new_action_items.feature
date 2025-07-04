Feature: Process emails to extract action items
  As a user already authenticated with the email provider
  I want to process emails to extract action items
  So that I can track my tasks and deadlines

  Background:
    Given the user is authenticated with the email provider

  Scenario: First-time run with default configuration
    Given no emails have been processed yet
    And no email retrieval timeframe is configured
    And there are emails from the last 5 days in the inbox
    And some of these emails contain clear action items with due dates
    When I run the application with the "run" command
    Then the system should retrieve emails from the last 5 days
    And action items should be extracted from emails containing actionable content
    And each extracted action item should have a non-empty description
    And each extracted action item should have a non-empty due date
    And the action items should be stored in the local database
    And all processed emails should be marked as processed in the local database

  Scenario: First-time run with custom configuration
    Given no emails have been processed yet
    And the email retrieval timeframe is configured to 10 days
    And there are emails from the last 10 days in the inbox
    And some of these emails contain clear action items with due dates
    When I run the application with the "run" command
    Then the system should retrieve emails from the last 10 days
    And action items should be extracted from emails containing actionable content
    And each extracted action item should have a non-empty description
    And each extracted action item should have a non-empty due date
    And the action items should be stored in the local database
    And all processed emails should be marked as processed in the local database

  Scenario: Subsequent run - only process new emails
    Given some emails have been processed already
    And there are new unprocessed emails in the inbox
    And some of these new emails contain clear action items with due dates
    When I run the application with the "run" command
    Then the system should only process emails not already marked as processed
    And action items should be extracted from the new emails containing actionable content
    And each extracted action item should have a non-empty description
    And each extracted action item should have a non-empty due date
    And the new action items should be stored in the local database
    And the newly processed emails should be marked as processed in the local database
    And previously processed emails should remain unchanged

  Scenario: Processing emails with no actionable content
    Given there are new emails in the inbox
    And these emails contain no clear action items or deadlines
    When I run the application with the "run" command
    Then the system should process these emails
    And no action items should be extracted from these emails
    And these emails should be marked as processed in the local database
    And the system should continue processing other emails normally

  Scenario: Processing spam or irrelevant emails
    Given there are new emails in the inbox
    And some of these emails are spam or promotional content
    When I run the application with the "run" command
    Then the system should process these emails
    And no action items should be extracted from spam or promotional emails
    And these emails should be marked as processed in the local database
    And the system should continue processing other emails normally

  Scenario: Mixed email content processing
    Given there are new emails in the inbox
    And some emails contain clear action items
    And some emails contain no actionable content
    And some emails are spam or promotional content
    When I run the application with the "run" command
    Then action items should only be extracted from emails with clear actionable content
    And all emails should be marked as processed in the local database
    And the extracted action items should have non-empty descriptions and due dates
