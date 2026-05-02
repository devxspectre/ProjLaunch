import os
from datetime import datetime

from agent.llm import call_llm
from agent.memory import Memory
from tools.executor import execute_tool
from tools.registry import TOOLS


def run_agent(config, repo_owner, repo_name, user_name):
    memory = Memory()
    turn_count = 0
    max_turns = config.get("max_turns", 20)
    model = config.get("model", "deepseek-chat")
    temperature = config.get("temperature", 0.6)
    max_tokens = config.get("max_tokens", 4000)
    api_base_url = config.get("api_base_url", "https://api.deepseek.com/v1")

    print(f"\nHello {user_name}! I'm your Implementation Onboarding Agent.")
    print("Let's set up a GitHub Project for your team.\n")

    memory.add_user(
        f"My name is {user_name}. "
        f"My GitHub repository is {repo_owner}/{repo_name}. "
        "I want to set up a project board for my team."
    )

    while turn_count < max_turns:
        turn_count += 1

        response = call_llm(
            messages=memory.get_history(),
            tools=TOOLS,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_base_url=api_base_url,
        )

        if response["response_type"] == "error":
            print(f"\n[Error] {response['content']}")
            break

        if response["response_type"] == "tool_call":
            tool_info = response["content"]
            print(f"\n[Calling tool: {tool_info['name']}]")
            print(f"  Arguments: {tool_info['arguments']}")

            memory.add_assistant_tool_call(
                tool_info["id"], tool_info["name"], tool_info["arguments"]
            )

            result = execute_tool(tool_info["name"], tool_info["arguments"])
            memory.add_tool_result(tool_info["id"], result)

            if not result.get("success"):
                print(f"  Result: Failed - {result.get('error', 'Unknown error')}")
            else:
                print(f"  Result: Success")

        else:
            text = response["content"]
            print(f"\n{text}")

            memory.add_assistant_message(text)

            if "[DONE]" in text:
                break

            user_input = input("\n> ").strip()
            memory.add_user(user_input)

    if turn_count >= max_turns:
        print(f"\n[Reached maximum turns ({max_turns}) — ending session]")

    _generate_summary(memory, config)


def _generate_summary(memory, config):
    summary_prompt_path = "prompts/summary_prompt.txt"
    if not os.path.exists(summary_prompt_path):
        print("[Warning] summary_prompt.txt not found — skipping summary")
        return

    with open(summary_prompt_path) as f:
        summary_prompt = f.read().strip()

    history = memory.get_history()
    summary_messages = history + [
        {"role": "user", "content": summary_prompt}
    ]

    model = config.get("model", "deepseek-chat")
    temperature = config.get("temperature", 0.6)
    max_tokens = config.get("max_tokens", 4000)
    api_base_url = config.get("api_base_url", "https://api.deepseek.com/v1")

    response = call_llm(
        messages=summary_messages,
        tools=None,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_base_url=api_base_url,
    )

    if response["response_type"] == "message":
        summary = response["content"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"summary_{timestamp}.md")
        with open(output_path, "w") as f:
            f.write(summary)
        print(f"\nSummary saved to {output_path}")
    elif response["response_type"] == "error":
        print(f"\n[Error generating summary] {response['content']}")
