import argparse
import os
import sys
import json

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
                {
                    "type": "function",
                    "function": {
                            "name": "Read",
                            "description": "Read and return the contents of a file",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "The path to the file to read"
                                    }
                                },
                                "required": ["file_path"]
                            }
                    }
                }
            ],
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        return chat.choices[0].message


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
                    func = tool_call.function
                    func_name = func.name
                    if "read" in func_name.lower():
                        func_args = json.loads(func.arguments)
                        file_name = func_args['file_path']

                        with open(file_name, "r") as file:
                            content = file.read()

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": content
                            })
            else:
                print(response.content)
                break
        else:
            print(response.content)
            break


if __name__ == "__main__":
    main()
