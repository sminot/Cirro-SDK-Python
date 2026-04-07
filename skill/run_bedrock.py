"""
Runner that executes the bioinformatics pipeline skill using AWS Bedrock.

Usage:
    python -m skill.run_bedrock [--base-url URL] [--project PROJECT] \
                                [--region REGION] [--model MODEL]

Requires:
    pip install boto3 cirro
    AWS credentials configured (environment, ~/.aws/credentials, or IAM role)
"""

from __future__ import annotations

import argparse
import json
import sys

import boto3

from cirro import DataPortal

from .config import CIRRO_BASE_URL, BEDROCK_MODEL, MAX_TURNS
from .system_prompt import SYSTEM_PROMPT
from .tools import TOOLS
from .tool_handlers import execute_tool


def _convert_tools_for_bedrock(tools: list[dict]) -> list[dict]:
    """
    Convert Anthropic-format tool definitions to Bedrock Converse format.

    Anthropic format uses "input_schema", Bedrock uses nested "toolSpec.inputSchema.json".
    """
    bedrock_tools = []
    for tool in tools:
        bedrock_tools.append({
            "toolSpec": {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": {
                    "json": tool["input_schema"],
                },
            }
        })
    return bedrock_tools


def _extract_text(content_blocks: list[dict]) -> str:
    """Extract concatenated text from Bedrock response content blocks."""
    parts = []
    for block in content_blocks:
        if "text" in block:
            parts.append(block["text"])
    return "\n".join(parts)


def _extract_tool_calls(content_blocks: list[dict]) -> list[dict]:
    """Extract tool-use blocks from Bedrock response content."""
    calls = []
    for block in content_blocks:
        if "toolUse" in block:
            calls.append(block["toolUse"])
    return calls


def build_initial_message(project: str | None) -> str:
    """Build the first user message based on CLI arguments."""
    if project:
        return (
            f"I want to launch a bioinformatics pipeline in the project "
            f'"{project}". Please look at the available datasets and help me '
            f"pick the right pipeline and parameters."
        )
    return (
        "I want to launch a bioinformatics pipeline. "
        "Please list the available projects so I can pick one."
    )


def run_conversation(
    portal: DataPortal,
    bedrock_client,
    model: str,
    initial_message: str,
) -> None:
    """
    Run the interactive tool-use conversation loop using Bedrock Converse API.
    """
    bedrock_tools = _convert_tools_for_bedrock(TOOLS)

    messages: list[dict] = [
        {"role": "user", "content": [{"text": initial_message}]}
    ]
    print(f"\nYou: {initial_message}\n")

    for _turn in range(MAX_TURNS):
        response = bedrock_client.converse(
            modelId=model,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": bedrock_tools},
            inferenceConfig={"maxTokens": 4096},
        )

        output = response["output"]["message"]
        assistant_content = output["content"]
        messages.append({"role": "assistant", "content": assistant_content})

        # Print text
        text = _extract_text(assistant_content)
        if text:
            print(f"Assistant: {text}\n")

        # Check stop reason
        stop_reason = response["stopReason"]

        if stop_reason == "end_turn":
            user_input = input("You: ").strip()
            if not user_input or user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                return
            messages.append({"role": "user", "content": [{"text": user_input}]})
            continue

        # Process tool calls
        tool_calls = _extract_tool_calls(assistant_content)
        if tool_calls:
            tool_result_blocks = []
            for call in tool_calls:
                tool_name = call["name"]
                tool_input = call["input"]
                tool_use_id = call["toolUseId"]
                print(f"  [Calling tool: {tool_name}]")
                result = execute_tool(portal, tool_name, tool_input)
                tool_result_blocks.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"json": json.loads(result)}],
                    }
                })
            messages.append({"role": "user", "content": tool_result_blocks})


def main():
    parser = argparse.ArgumentParser(
        description="Launch bioinformatics pipelines with AI assistance (AWS Bedrock)"
    )
    parser.add_argument(
        "--base-url",
        default=CIRRO_BASE_URL,
        help=f"Cirro platform URL (default: {CIRRO_BASE_URL})",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Project name or ID to start with",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region for Bedrock (default: us-east-1)",
    )
    parser.add_argument(
        "--model",
        default=BEDROCK_MODEL,
        help=f"Bedrock model ID (default: {BEDROCK_MODEL})",
    )
    args = parser.parse_args()

    # Initialize Cirro SDK
    print(f"Connecting to Cirro at {args.base_url}...")
    portal = DataPortal(base_url=args.base_url)
    print("Connected.\n")

    # Initialize Bedrock client
    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=args.region,
    )

    initial_message = build_initial_message(args.project)
    run_conversation(portal, bedrock_client, args.model, initial_message)


if __name__ == "__main__":
    main()
