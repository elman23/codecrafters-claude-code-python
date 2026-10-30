import argparse
import os
from typing import Any

import app.constants as const
from app.utils import handle_bash, handle_read, handle_write, scan_skills, replace_values, render_skill, handle_skill

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

    prompt = args.p

    if API_KEY is None:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    skills = scan_skills(".claude/skills")
    formatted = ""

    new_prompt = prompt

    if prompt.startswith("/"):
        prompt_words = prompt.split()

        skill_names = [
            x.lstrip("/")
            for x in prompt_words
            if x.startswith("/")
        ]

        arguments = " ".join(
            x for x in prompt_words if not x.startswith("/")
        )

        selected_skills = [
            s for s in skills if s["name"] in skill_names
        ]

        new_prompt = ""
        for skill in selected_skills:
            new_prompt += "\n" + render_skill(skill, arguments)

        if arguments:
            new_prompt += f"\n\nArguments: {arguments}"

    for skill in skills:
        formatted += f"- {skill['name']}: {skill['description']}\n"

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": f"You have access to the following skills:\n\n{formatted}",
        },
        {
            "role": "user",
            "content": new_prompt,
        },
    ]

    client = ChatClient(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    tools: list[ChatCompletionToolParam] = [
        const.READ_FUNCTION,
        const.WRITE_FUNCTION,
        const.BASH_FUNCTION,
    ]

    if not prompt.startswith("/"):
        tools.append(const.SKILL_FUNCTION)

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
                    content = handle_skill(tool_call, skills)
                else:
                    content = f"Unknown tool: {func_name}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content,
                    }
                )

        else:
            print(response.content)
            break


if __name__ == "__main__":
    main()
