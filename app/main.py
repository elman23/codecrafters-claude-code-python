import argparse
import os
import sys
import json
import subprocess

import app.constants as const

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL",
                     default="https://openrouter.ai/api/v1")


class ChatClient(OpenAI):
    def __init__(self, api_key, base_url):
        super().__init__(api_key=api_key, base_url=base_url)

    def call_api(self, messages):
        chat = self.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=[
                const.READ_FUNCTION,
                const.WRITE_FUNCTION,
                const.BASH_FUNCTION
            ],
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        return chat.choices[0].message


def handle_read(tool_call, messages):
    func_args = json.loads(tool_call.function.arguments)
    file_name = func_args['file_path']

    with open(file_name, "r") as file:
        content = file.read()

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": content
        })


def handle_write(tool_call, messages):
    func_args = json.loads(tool_call.function.arguments)
    file_path = func_args['file_path']
    file_content = func_args['content']

    with open(file_path, "w") as file:
        file.write(file_content)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": file_content
        })


def handle_bash(tool_call, messages):
    func_args = json.loads(tool_call.function.arguments)
    command = func_args['command'].split()
    result = subprocess.run(
        command, capture_output=True, text=True)
    content = result.stdout
    if result.stderr:
        content = result.stderr
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": content
    })


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    messages = [{"role": "user", "content": args.p}]
    client = ChatClient(api_key=API_KEY, base_url=BASE_URL)
    while True:
        response = client.call_api(messages=messages)
        messages.append(response)
        if response is not None:
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    if "read" in func_name.lower():
                        handle_read(tool_call, messages)
                    if "write" in func_name.lower():
                        handle_write(tool_call, messages)
                    if "bash" in func_name.lower():
                        handle_bash(tool_call, messages)

            else:
                print(response.content)
                break
        else:
            print(response.content)
            break


if __name__ == "__main__":
    main()
