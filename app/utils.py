from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from typing import Any
import subprocess
import json


def handle_read(
    tool_call: ChatCompletionMessageToolCall,
    messages: list[ChatCompletionMessageParam],
) -> None:
    func_args: dict[str, Any] = json.loads(
        tool_call.function.arguments
    )

    file_name: str = func_args["file_path"]

    with open(file_name, "r") as file:
        content: str = file.read()

    return content


def handle_write(
    tool_call: ChatCompletionMessageToolCall,
    messages: list[ChatCompletionMessageParam],
) -> None:
    func_args: dict[str, Any] = json.loads(
        tool_call.function.arguments
    )

    file_path: str = func_args["file_path"]
    file_content: str = func_args["content"]

    with open(file_path, "w") as file:
        file.write(file_content)

    return file_content


def handle_bash(
    tool_call: ChatCompletionMessageToolCall,
    messages: list[ChatCompletionMessageParam],
) -> None:
    func_args: dict[str, Any] = json.loads(
        tool_call.function.arguments
    )

    command: list[str] = func_args["command"].split()

    result: subprocess.CompletedProcess[str] = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    content: str = result.stdout

    if result.stderr:
        content = result.stderr

    return content
