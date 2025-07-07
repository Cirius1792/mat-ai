# MAT.AI: an AI Powered Mail Activity Tracker
![Tests](https://github.com/cirius1792/matai-v2/actions/workflows/tests.yml/badge.svg)
## Overview

This project is designed to automate the extraction and management of action items from email communications. It leverages AI to parse emails, identify actionable tasks, and store them on a Trello board. 

The main goal is to create an assistant that helps you track your deadlines. 

## Features
- ✅ **Email Parsing and Activity Tracking**: Utilizes AI to read and understand email content, extracting requests and tasks with details such as due date, owners, and priority.
- ✅ **Outlook Integration**: Support Outlook mailboxes integration with [O365](https://github.com/O365/python-o365)
- ✅ **Trello Integration**: Support Trello boards to track the activities extracted from your emails
- ✅ **Database Integration**: Stores email id to keep track of the already parsed emails, no personal informations are store here
- ✅ **Logging and Configuration**: Includes robust logging and configuration management for easy deployment and maintenance.
- ✅ **Use the your preferred LLM locally or from a provider**: You can use any OpenAI compliant API server and any model you want

## Use it as a CLI tool

### Prerequisites

- Python 3.8+
- Access to Microsoft O365 API

### Run It

You can run the CLI tool using the `uv` package manager:

```bash
uv run matai <command> [options]
```

For example:

```bash
uv run matai authenticate
uv run matai run
```

#### Available Commands

- `authenticate` – Authenticate the application with the email server.
- `run` – Process new emails and extract action items.
- `benchmark-judge` - benchmark an ai judge with the a set of well known test cases
- `init` - Creates a sample config file

## Configuration
You can use the sample config.yml file below to configure the tool. 
A config file similar to the following can also be automatically generated using the command `uv matai init`
```yaml
database:
  path: matai.db
llm_config:
  api_key: your_llm_api_key
  host: http://<openai-compatible-server>/v1
  model: qwen2.5:7b
outlook_config:
  client_id: your_client_id
  client_secret: your_client_secret
  tenant_id: your_tenant_id
filters: 
  recipients: 
  - "my-email@domain.com"
trello_config:
  api_key: your_api_key
  api_token: your_api_token
  board: your_board_id
```
To generate the outlook credentials have a look at the [o365 documentation](https://o365.github.io/python-o365/latest/getting_started.html#oauth-setup-prerequisite)
To generate the trello credentials refer to the official [Trello API documentation](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/)

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.


