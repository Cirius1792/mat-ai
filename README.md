# MAT.AI: an AI Powered Mail Activity Tracker
![Tests](https://github.com/cirius1792/mat-ai/actions/workflows/tests.yml/badge.svg)
## Overview

This project is designed to automate the extraction and management of action items from email communications. It leverages AI to parse emails, identify actionable tasks, and store them on a Trello board. 

The main goal is to create an assistant that helps you track your deadlines. 

## Features
- ✅ **Email Parsing and Activity Tracking**: Utilizes AI to read and understand email content, extracting requests and tasks with details such as due date, owners, and priority.
- ✅ **Outlook Integration**: Support Outlook mailboxes integration with [O365](https://github.com/O365/python-o365)
- ✅ **Trello Integration**: Support Trello boards to track the activities extracted from your emails
- ✅ **Database Integration**: Stores email content and action items in a local database.
- ✅ **Logging and Configuration**: Includes robust logging and configuration management for easy deployment and maintenance.
- ✅ **Use the your preferred LLM locally or from a provider**: You can use any OpenAI compliant API server and any model you want

## Use it as CLI tool

### Prerequisites

- Python 3.8+
- Access to Microsoft O365 API

### Run It

1. Start the application by running `uv run mat-ai`.

## Configuration
You can use the sample config.yml file to configure the tool. 

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.

