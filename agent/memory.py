import json
import os


class Memory:
    def __init__(self, system_prompt_path="prompts/system_prompt.txt"):
        self.messages = []
        self._load_system_prompt(system_prompt_path)

    def _load_system_prompt(self, path):
        if os.path.exists(path):
            with open(path) as f:
                content = f.read().strip()
            if content:
                self.messages.append({"role": "system", "content": content})

    def add_user(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})

    def add_assistant_tool_call(self, tool_call_id, name, arguments):
        self.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments)
                }
            }]
        })

    def add_tool_result(self, tool_call_id, content):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": str(content)
        })

    def get_history(self):
        return self.messages

    def clear(self):
        self.messages.clear()
