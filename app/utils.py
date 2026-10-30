from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from typing import Any
import subprocess
import json
import os
import re


import json
from pathlib import Path
from typing import Any


def handle_read(
    tool_call: ChatCompletionMessageToolCall,
    messages: list[ChatCompletionMessageToolParam],
) -> str:
    func_args: dict[str, Any] = json.loads(
        tool_call.function.arguments
    )

    path = Path(func_args["file_path"])

    if path.is_dir():
        path = path / "SKILL.md"

    with path.open("r") as file:
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


def scan_skills(skills_folder: str = ".claude/skills/") -> list[dict[str, str]]:
    skills = []

    if not os.path.exists(skills_folder):
        return skills

    skills_list = os.listdir(skills_folder)
    for skill in skills_list:
        skill_file_path = f"{skills_folder}/{skill}/SKILL.md"
        with open(skill_file_path, "r") as f:
            content = f.read()

        match = re.match(r"\A---\s*\n(.*?)\n---", content, re.DOTALL)

        if not match:
            raise ValueError("No front matter found")

        front_matter = match.group(1)

        name = re.search(r"^name:\s*(.*)$", front_matter,
                         re.MULTILINE).group(1)
        description = re.search(
            r"^description:\s*(.*)$", front_matter, re.MULTILINE
        ).group(1)

        skill_text = content[match.end():].strip()

        skills.append(
            {"name": name, "description": description, "text": skill_text})

    return skills


def replace_values(templates: list[str], values: list[str]) -> list[str]:
    retr = []
    for template in templates:
        replaced = template.replace('$ARGUMENTS', ' '.join(values))

        replaced = re.sub(
            r'\$(\d+)',
            lambda m: str(values[int(m.group(1))]),
            replaced
        )
        retr.append(replaced)

    return retr


def render_skill(skill: dict[str, str], arguments: str) -> str:
    text = skill["text"]
    
    if arguments:
        text = text.replace("$ARGUMENTS", arguments)

    prompt = (
        f"Skill: {skill['name']} (located at .claude/skills/{skill['name']})\n"
        "Always adjust paths for scripts relative to that folder.\n\n"
        f"{text}"
    )

    return prompt


def handle_skill(tool_call: ChatCompletionMessageToolCall, skills: list[dict[str, str]]) -> str:
    func_args: dict[str, Any] = json.loads(tool_call.function.arguments)
    name: str = func_args["name"].lstrip("/")
    arguments: str = func_args.get("args", "")

    for skill in skills:
        if skill["name"] == name:
            return render_skill(skill, arguments)

    available = ", ".join(s["name"] for s in skills)
    return f"Skills '{name}' not found. Available skills: {available}"