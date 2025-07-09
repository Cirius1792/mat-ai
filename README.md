# MAT.AI: an AI Powered Mail Activity Tracker
![Tests](https://github.com/cirius1792/matai-v2/actions/workflows/tests.yml/badge.svg)
## Overview

This project is designed to automate the extraction and management of action items from email communications.
It leverages AI to parse emails, identify actionable tasks, and store them on a Trello board. 

The main goal is to create an assistant that helps you track your tasks and deadlines.
MAT.AI  automates turning email threads into tracked tasks, extracting deadlines, action items, and meeting requests directly from your inbox and pushing them into a Trello board.

I also found a similar approach to time managemnt described by [Ben Vallack](https://youtu.be/dNcf3cyXakI?t=799) in his video, I strongly suggest you to have a look at it if the topic does matter to you. 


## Features
- ✅ **Email Parsing and Activity Tracking**: Utilizes AI to read and understand email content, extracting requests and tasks with details such as due date, owners, and priority.
- ✅ **Outlook Integration**: Supports integrating with Outlook mailboxes via [O365](https://github.com/O365/python-o365).
- ✅ **Trello Integration**: Supports Trello boards to track the activities extracted from your emails.
- ✅ **Database Integration**: Stores email IDs to keep track of already parsed emails. No personal information is stored.
- ✅ **Logging and Configuration**: Includes robust logging and configuration management for easy deployment and maintenance.
- ✅ **Use your preferred LLM locally or from a provider**: You can use any OpenAI-compliant API server and any model you want.

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
- `benchmark-judge` – Benchmark an AI judge against a set of well-known test cases.
- `init` – Creates a sample config file.

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
To generate Outlook credentials, have a look at the [O365 documentation](https://o365.github.io/python-o365/latest/getting_started.html#oauth-setup-prerequisite).
To generate Trello credentials, refer to the official [Trello API documentation](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/).
Once added the trello api key and token to the configuration file, when using the `authenticate` command you will be prompted to chose the Trello board on which a new list will be created. 

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.

⚠️ This project is still under active development. ⚠️

The next major improvement planned is the development of a benchmark methodology to score widely available LLMs, helping users decide which model to use based on their needs and resources.
A small part of this has already been implemented in the benchmark.py script, including the skeleton for using an LLM as a judge, as well as a benchmark to assess which LLM can effectively serve as a judge for this task.
