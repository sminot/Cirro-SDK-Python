# Bioinformatics Pipeline Launcher Skill

An AI skill that guides users through launching bioinformatics pipeline runs on the
[Cirro](https://cirro.bio) platform. The skill can be executed using the **Claude API**
(Anthropic) or the **AWS Bedrock API**.

## Overview

This skill acts as an interactive bioinformatics assistant that:

1. **Discovers** available projects, datasets, and pipelines in a Cirro workspace
2. **Inspects** input files (sample sheets, FASTQ manifests, metadata) to understand the data
3. **Recommends** an appropriate pipeline and parameters based on file contents
4. **Confirms** the analysis plan with the user before launching
5. **Launches** the pipeline and reports status

## Workflow

```
User provides project / dataset
        |
        v
Skill lists files in the dataset
        |
        v
Skill inspects key files (sample sheets, manifests, metadata)
        |
        v
Skill identifies data type and recommends pipeline + parameters
        |
        v
User reviews and adjusts the plan
        |
        v
Skill launches the pipeline via Cirro SDK
        |
        v
Skill reports the new dataset ID and status
```

## Directory Structure

```
skill/
├── README.md                # This file
├── __init__.py
├── system_prompt.py         # System prompt defining the skill behavior
├── tools.py                 # Tool definitions (JSON schema) for the AI
├── tool_handlers.py         # Tool execution handlers using Cirro SDK
├── run_claude.py            # Runner using Claude (Anthropic) API
├── run_bedrock.py           # Runner using AWS Bedrock API
└── config.py                # Configuration (base URL, model selection)
```

## Prerequisites

```bash
pip install cirro anthropic boto3
```

- **Cirro account** with valid credentials (device-code auth or access token)
- **Anthropic API key** (for Claude runner) or **AWS credentials** (for Bedrock runner)

## Quick Start

### Using Claude (Anthropic API)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python -m skill.run_claude \
    --base-url app.cirro.bio \
    --project "My Project"
```

### Using AWS Bedrock

```bash
# AWS credentials must be configured (e.g., via ~/.aws/credentials or environment)
python -m skill.run_bedrock \
    --base-url app.cirro.bio \
    --project "My Project" \
    --region us-east-1
```

## How It Works

### System Prompt

The system prompt (`system_prompt.py`) defines the AI's role as a bioinformatics
pipeline specialist. It instructs the model to:

- Always inspect input data before recommending a pipeline
- Explain its reasoning about data types and pipeline selection
- Never launch a pipeline without explicit user confirmation
- Provide clear summaries of what will be run and with what parameters

### Tools

The skill exposes these tools to the AI model:

| Tool | Description |
|------|-------------|
| `list_projects` | List available Cirro projects |
| `get_project_datasets` | List datasets in a project |
| `get_dataset_files` | List files in a dataset |
| `read_file_contents` | Read the contents of a file (CSV, TSV, JSON, TXT) |
| `list_pipelines` | List available analysis pipelines |
| `get_pipeline_parameters` | Get the parameter schema for a pipeline |
| `launch_pipeline` | Launch a pipeline on a dataset with given parameters |
| `check_dataset_status` | Check the status of a dataset / running analysis |

### Execution Model

Both runners follow the same pattern:

1. Initialize Cirro SDK with user credentials
2. Build the message history with the system prompt
3. Send user messages to the AI model
4. When the model calls a tool, execute it via `tool_handlers.py`
5. Return tool results to the model
6. Repeat until the model produces a final text response
7. Print the response and wait for the next user input

## Configuration

See `config.py` for available settings:

- `CIRRO_BASE_URL` - Cirro platform URL (default: `app.cirro.bio`)
- `CLAUDE_MODEL` - Claude model ID for Anthropic API
- `BEDROCK_MODEL` - Model ID for Bedrock
- `MAX_FILE_READ_BYTES` - Maximum bytes to read when inspecting files (default: 50KB)

## Extending the Skill

To add new tools:

1. Add the JSON schema to `tools.py`
2. Add the handler function to `tool_handlers.py`
3. Register it in the `TOOL_HANDLERS` dictionary

To modify the AI behavior, edit the system prompt in `system_prompt.py`.
