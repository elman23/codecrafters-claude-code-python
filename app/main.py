import argparse
import os
from typing import Any

import app.constants as const
from app.utils import handle_bash, handle_read, handle_write

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
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
    ) -> ChatCompletionMessage:
        chat = self.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=[
                const.READ_FUNCTION,
                const.WRITE_FUNCTION,
                const.BASH_FUNCTION,
            ],
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

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "user",
            "content": args.p,
        }
    ]

    client = ChatClient(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    while True:
        response: ChatCompletionMessage = client.call_api(
            messages=messages
        )

        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                func_name: str = tool_call.function.name

                content = None
                if "read" in func_name.lower():
                    content = handle_read(tool_call, messages)

                if "write" in func_name.lower():
                    content = handle_write(tool_call, messages)

                if "bash" in func_name.lower():
                    content = handle_bash(tool_call, messages)

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
