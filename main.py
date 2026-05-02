import os
import sys

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = "config/agent_config.yaml"


def load_config(path):
    if not os.path.exists(path):
        print(f"[Error] Config file not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    try:
        config = load_config(CONFIG_PATH)

        print("=" * 50)
        print("  Implementation Onboarding Agent")
        print("=" * 50)
        print()
        print("Welcome! I'll help you set up a GitHub Project for your team.")
        print()

        user_name = input("What's your name? ").strip()
        repo_owner = input("GitHub repository owner (username or org): ").strip()
        repo_name = input("GitHub repository name: ").strip()

        if not all([user_name, repo_owner, repo_name]):
            print("[Error] All fields are required.")
            sys.exit(1)

        os.environ["GITHUB_REPO_OWNER"] = repo_owner
        os.environ["GITHUB_REPO_NAME"] = repo_name

        from tools.github_tools import authenticate_github
        authenticate_github()

        from agent.loop import run_agent
        run_agent(config, repo_owner, repo_name, user_name)

        print()
        print("=" * 50)
        print("  Onboarding complete. Thank you!")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n\nSession cancelled by user. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
