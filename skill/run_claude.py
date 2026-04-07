"""
Runner that executes the bioinformatics pipeline skill using the Anthropic Claude API.

Usage:
    python -m skill.run_claude [--base-url URL] [--project PROJECT] [--model MODEL]

Requires:
    pip install anthropic cirro
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

from __future__ import annotations

import argparse
import json
import sys

import anthropic

from cirro import DataPortal

from .config import CIRRO_BASE_URL, CLAUDE_MODEL, MAX_TURNS
from .system_prompt import SYSTEM_PROMPT
from .tools import TOOLS
from .tool_handlers import execute_tool


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
    client: anthropic.Anthropic,
    model: str,
    initial_message: str,
) -> None:
    """
    Run the interactive tool-use conversation loop.

    The loop sends messages to Claude, executes any tool calls, feeds results
    back, and prints assistant text to the user. It continues until the model
    stops issuing tool calls or the turn limit is reached.
    """
    messages: list[dict] = [{"role": "user", "content": initial_message}]
    print(f"\nYou: {initial_message}\n")

    for _turn in range(MAX_TURNS):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect assistant content blocks
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Print any text blocks
        for block in assistant_content:
            if block.type == "text":
                print(f"Assistant: {block.text}\n")

        # If the model is done (no tool use), wait for user input
        if response.stop_reason == "end_turn":
            user_input = input("You: ").strip()
            if not user_input or user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                return
            messages.append({"role": "user", "content": user_input})
            continue

        # Process tool calls
        tool_results = []
        for block in assistant_content:
            if block.type == "tool_use":
                print(f"  [Calling tool: {block.name}]")
                result = execute_tool(portal, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})


def main():
    parser = argparse.ArgumentParser(
        description="Launch bioinformatics pipelines with AI assistance (Claude API)"
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
        "--model",
        default=CLAUDE_MODEL,
        help=f"Claude model ID (default: {CLAUDE_MODEL})",
    )
    args = parser.parse_args()

    # Initialize Cirro SDK (will prompt for device-code auth if needed)
    print(f"Connecting to Cirro at {args.base_url}...")
    portal = DataPortal(base_url=args.base_url)
    print("Connected.\n")

    # Initialize Anthropic client
    client = anthropic.Anthropic()

    initial_message = build_initial_message(args.project)
    run_conversation(portal, client, args.model, initial_message)


if __name__ == "__main__":
    main()
