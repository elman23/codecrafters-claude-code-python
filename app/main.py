import argparse
import json
import os
from typing import Any

import app.constants as const
from app.utils import handle_bash, handle_read, handle_write, scan_skills, render_skill

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")

BASE_URL: str = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)


class ChatClient(OpenAI):
    def __init__(self, api_key: str, base_url: str) -> None:
        super().__init__(api_key=api_key, base_url=base_url)

    def call_api(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[ChatCompletionToolParam],
    ) -> ChatCompletionMessage:
        chat = self.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=tools,
        )

        if not chat.choices:
            raise RuntimeError("no choices in response")

        return chat.choices[0].message


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if API_KEY is None:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = ChatClient(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    skills = scan_skills(".claude/skills")
    formatted = ""

    prompt = args.p
    prompt_words = prompt.split()

    arguments = " ".join(
        x for x in prompt_words if not x.startswith("/")
    )
    skill_names = [
        x.lstrip("/")
        for x in prompt_words
        if x.startswith("/")
    ]
    selected_skills = [
        s for s in skills if s["name"] in skill_names
    ]

    new_prompt = ""

    for skill in selected_skills:
        new_prompt += "\n" + render_skill(skill, arguments)

    if arguments:
        new_prompt += f"\n\nArguments: {arguments}"

    if not new_prompt:
        new_prompt = prompt

    for skill in skills:
        formatted += f"- {skill['name']}: {skill['description']}\n"

    system_prompt = f"You have access to the following skills:\n\n{formatted}\n"
    system_prompt += "If a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns."

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": new_prompt,
        },
    ]

    tools: list[ChatCompletionToolParam] = [
        const.READ_FUNCTION,
        const.WRITE_FUNCTION,
        const.BASH_FUNCTION,
    ]

    if not prompt.startswith("/"):
        tools.append(const.SKILL_FUNCTION)

    response = run_agent_loop(client, messages, tools, skills)
    print(response)


def execute_skill_call(
    client: ChatClient,
    tool_call: Any,
    skills: list[Any],
    tools: list[ChatCompletionToolParam],
) -> str:
    args_json = json.loads(tool_call.function.arguments or "{}")
    skill_name = args_json.get("command") or args_json.get(
        "skill") or args_json.get("name")

    matched_skill = next((s for s in skills if s["name"] == skill_name), None)

    if not matched_skill:
        return f"Error: Skill '{skill_name}' not found"

    # Check if skill requires isolated subagent context
    if matched_skill.get("context") == "fork":
        subagent_prompt: list[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": matched_skill["text"],
            }
        ]
        # Run isolated subagent loop without parent message history
        return run_agent_loop(client, subagent_prompt, tools, skills)

    return matched_skill["text"]


def run_agent_loop(
    client: ChatClient,
    messages: list[ChatCompletionMessageParam],
    tools: list[ChatCompletionToolParam],
    skills: list[Any],
) -> str:
    while True:
        response: ChatCompletionMessage = client.call_api(
            messages=messages,
            tools=tools,
        )

        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                func_name: str = tool_call.function.name

                content = None
                if "read" in func_name.lower():
                    content = handle_read(tool_call, messages)
                elif "write" in func_name.lower():
                    content = handle_write(tool_call, messages)
                elif "bash" in func_name.lower():
                    content = handle_bash(tool_call, messages)
                elif "skill" in func_name.lower():
                    content = execute_skill_call(
                        client, tool_call, skills, tools)
                else:
                    content = f"Error: Unknown tool '{func_name}'"

                if content is None:
                    content = ""

                if not isinstance(content, str):
                    content = str(content)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content,
                    }
                )

        else:
            return response.content or ""


if __name__ == "__main__":
    main()
