"""
Tool execution handlers.

Each handler takes a Cirro DataPortal instance and the tool input dict,
executes the corresponding SDK operation, and returns a JSON-serializable result.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict

from cirro import DataPortal

from .config import MAX_FILE_READ_BYTES

logger = logging.getLogger(__name__)


def handle_list_projects(portal: DataPortal, _input: Dict[str, Any]) -> str:
    projects = portal.list_projects()
    result = [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in projects
    ]
    return json.dumps(result, indent=2)


def handle_get_project_datasets(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    project_id = tool_input["project_id"]
    project = portal.get_project(project_id)
    datasets = project.list_datasets()
    result = [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "status": d.status.value if hasattr(d.status, "value") else str(d.status),
            "process_id": d.process_id,
            "created_by": d.created_by,
            "created_at": str(d.created_at),
        }
        for d in datasets
    ]
    return json.dumps(result, indent=2)


def handle_get_dataset_files(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    project_id = tool_input["project_id"]
    dataset_id = tool_input["dataset_id"]
    dataset = portal.get_dataset(project=project_id, dataset=dataset_id)
    files = dataset.list_files()
    result = [
        {
            "name": f.name,
            "relative_path": f.relative_path,
            "size": f.size,
        }
        for f in files
    ]
    return json.dumps(result, indent=2)


def handle_read_file_contents(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    project_id = tool_input["project_id"]
    dataset_id = tool_input["dataset_id"]
    file_path = tool_input["file_path"]

    dataset = portal.get_dataset(project=project_id, dataset=dataset_id)
    file_obj = dataset.get_file(file_path)

    # Read raw bytes (up to limit) and decode as text
    raw = file_obj._get()
    content = raw[:MAX_FILE_READ_BYTES]

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return json.dumps({
            "error": "Binary file — cannot display contents as text.",
            "file_path": file_path,
            "size_bytes": len(raw),
        })

    truncated = len(raw) > MAX_FILE_READ_BYTES
    return json.dumps({
        "file_path": file_path,
        "size_bytes": len(raw),
        "truncated": truncated,
        "contents": text,
    }, indent=2)


def handle_list_pipelines(portal: DataPortal, _input: Dict[str, Any]) -> str:
    processes = portal.list_processes(ingest=False)
    result = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
        }
        for p in processes
    ]
    return json.dumps(result, indent=2)


def handle_get_pipeline_parameters(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    pipeline_id = tool_input["pipeline_id"]
    process = portal.get_process(pipeline_id)
    param_spec = process.get_parameter_spec()
    return json.dumps(param_spec.form_spec_json, indent=2)


def handle_launch_pipeline(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    project_id = tool_input["project_id"]
    dataset_id = tool_input["dataset_id"]
    pipeline_id = tool_input["pipeline_id"]
    name = tool_input["name"]
    description = tool_input.get("description", "")
    params = tool_input.get("params", {})
    notification_emails = tool_input.get("notification_emails", [])

    dataset = portal.get_dataset(project=project_id, dataset=dataset_id)
    new_dataset_id = dataset.run_analysis(
        name=name,
        description=description,
        process=pipeline_id,
        params=params,
        notifications_emails=notification_emails,
    )

    return json.dumps({
        "success": True,
        "new_dataset_id": new_dataset_id,
        "message": f"Pipeline launched. New dataset ID: {new_dataset_id}",
    }, indent=2)


def handle_check_dataset_status(portal: DataPortal, tool_input: Dict[str, Any]) -> str:
    project_id = tool_input["project_id"]
    dataset_id = tool_input["dataset_id"]
    dataset = portal.get_dataset(project=project_id, dataset=dataset_id)
    return json.dumps({
        "id": dataset.id,
        "name": dataset.name,
        "status": dataset.status.value if hasattr(dataset.status, "value") else str(dataset.status),
        "process_id": dataset.process_id,
        "description": dataset.description,
    }, indent=2)


# Registry mapping tool names to handler functions
TOOL_HANDLERS: Dict[str, Callable[[DataPortal, Dict[str, Any]], str]] = {
    "list_projects": handle_list_projects,
    "get_project_datasets": handle_get_project_datasets,
    "get_dataset_files": handle_get_dataset_files,
    "read_file_contents": handle_read_file_contents,
    "list_pipelines": handle_list_pipelines,
    "get_pipeline_parameters": handle_get_pipeline_parameters,
    "launch_pipeline": handle_launch_pipeline,
    "check_dataset_status": handle_check_dataset_status,
}


def execute_tool(portal: DataPortal, tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Execute a tool by name with the given input.

    Returns the tool result as a JSON string.
    Raises KeyError if the tool name is not recognized.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise KeyError(f"Unknown tool: {tool_name}")
    try:
        return handler(portal, tool_input)
    except Exception as e:
        logger.exception("Tool execution error: %s", tool_name)
        return json.dumps({"error": str(e)})
