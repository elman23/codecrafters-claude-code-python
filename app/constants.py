from openai.types.chat import ChatCompletionToolParam
from typing import Final


READ_FUNCTION: Final[ChatCompletionToolParam] = {
    "type": "function",
    "function": {
        "name": "Read",
        "description": "Read and return the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read",
                }
            },
            "required": ["file_path"],
        },
    },
}

WRITE_FUNCTION: Final[ChatCompletionToolParam] = {
    "type": "function",
    "function": {
        "name": "Write",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "required": ["file_path", "content"],
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "The path of the file to write to"
                    ),
                },
                "content": {
                    "type": "string",
                    "description": (
                        "The content to write to the file"
                    ),
                },
            },
        },
    },
}

BASH_FUNCTION: Final[ChatCompletionToolParam] = {
    "type": "function",
    "function": {
        "name": "Bash",
        "description": "Execute a shell command",
        "parameters": {
            "type": "object",
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute",
                }
            },
        },
    },
}

SKILL_FUNCTION: Final[ChatCompletionToolParam] = {
    "type": "function",
    "function": {
      "name": "Skill",
      "description": "Load a skill's instructions into the conversation",
      "parameters": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string", "description": "The name of the skill to use" },
          "args": { "type": "string", "description": "Optional arguments for the skill" }
        }
      }
    }
  }