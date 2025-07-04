Feature: Email Server Authentication
  As a user, I want to authenticate the application with the email server from the cli,
  so that I can fetch and process emails.

  Background:
    Given a valid configuration file exists with Outlook settings

  Scenario: First time authentication
    Given the application is not authenticated
    When I run the "authenticate" command
    Then I should see "Please visit this URL to authenticate:"
    And I should be prompted to paste the URL
    And I should see "Authentication completed successfully"

  Scenario: Already authenticated
    Given the application is already authenticated
    When I run the "authenticate" command
    Then I should see "Already authenticated"

