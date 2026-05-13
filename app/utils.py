import json
import subprocess


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
