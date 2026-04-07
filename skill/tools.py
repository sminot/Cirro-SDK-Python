"""
Tool definitions (JSON schema) exposed to the AI model.

Each tool is defined as a dict matching the Anthropic tool-use schema,
which is also compatible with the Bedrock converse API tool format.
"""

TOOLS = [
    {
        "name": "list_projects",
        "description": (
            "List all projects accessible to the current user. "
            "Returns project names and IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_project_datasets",
        "description": (
            "List all datasets in a given project. "
            "Returns dataset names, IDs, status, and the process that created them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID (or name) to list datasets for.",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_dataset_files",
        "description": (
            "List all files in a dataset. "
            "Returns file names, relative paths, and sizes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID.",
                },
                "dataset_id": {
                    "type": "string",
                    "description": "The dataset ID.",
                },
            },
            "required": ["project_id", "dataset_id"],
        },
    },
    {
        "name": "read_file_contents",
        "description": (
            "Read the contents of a file from a dataset. "
            "Supports text-based files: CSV, TSV, JSON, TXT, LOG, MD, YAML, and similar. "
            "Returns the first portion of the file (up to the configured size limit). "
            "Use this to inspect sample sheets, metadata, and configuration files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID.",
                },
                "dataset_id": {
                    "type": "string",
                    "description": "The dataset ID.",
                },
                "file_path": {
                    "type": "string",
                    "description": (
                        "The relative path of the file within the dataset "
                        "(as returned by get_dataset_files)."
                    ),
                },
            },
            "required": ["project_id", "dataset_id", "file_path"],
        },
    },
    {
        "name": "list_pipelines",
        "description": (
            "List all available analysis pipelines (processes). "
            "Returns pipeline names, IDs, descriptions, and categories. "
            "Excludes ingest-only processes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_pipeline_parameters",
        "description": (
            "Get the parameter specification (JSON Schema) for a pipeline. "
            "This describes all configurable parameters, their types, defaults, "
            "and valid values."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pipeline_id": {
                    "type": "string",
                    "description": "The pipeline (process) ID.",
                },
            },
            "required": ["pipeline_id"],
        },
    },
    {
        "name": "launch_pipeline",
        "description": (
            "Launch an analysis pipeline on a source dataset. "
            "This creates a new dataset containing the analysis results. "
            "IMPORTANT: Only call this after the user has explicitly confirmed "
            "the pipeline, parameters, and input dataset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID.",
                },
                "dataset_id": {
                    "type": "string",
                    "description": "The source dataset ID to analyze.",
                },
                "pipeline_id": {
                    "type": "string",
                    "description": "The pipeline (process) ID to run.",
                },
                "name": {
                    "type": "string",
                    "description": "Name for the newly created results dataset.",
                },
                "description": {
                    "type": "string",
                    "description": "Description for the results dataset.",
                    "default": "",
                },
                "params": {
                    "type": "object",
                    "description": (
                        "Pipeline parameters as key-value pairs. "
                        "Must conform to the pipeline's parameter schema."
                    ),
                },
                "notification_emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Email addresses to notify when the analysis completes.",
                    "default": [],
                },
            },
            "required": ["project_id", "dataset_id", "pipeline_id", "name"],
        },
    },
    {
        "name": "check_dataset_status",
        "description": (
            "Check the current status of a dataset (e.g., a running analysis). "
            "Returns the dataset status, name, and process information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID.",
                },
                "dataset_id": {
                    "type": "string",
                    "description": "The dataset ID to check.",
                },
            },
            "required": ["project_id", "dataset_id"],
        },
    },
]
