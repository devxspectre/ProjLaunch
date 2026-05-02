# Implementation Onboarding Agent

A conversational CLI agent that interviews software teams about their workflow and automatically configures a GitHub Project board based on their answers.

Built for Lab0.ai — demonstrates how enterprise software implementation (ERP, ITSM, identity platforms) can be compressed from months of consulting into an automated, self-serve agent experience.

## How It Works

1. **Discovery Interview** — The agent asks about team size, workflow methodology, work types, and preferences one or two questions at a time.
2. **Configuration Plan** — Based on your answers, the agent reasons about the optimal board structure (columns, WIP limits, labels, milestones) and presents a plan for confirmation.
3. **Execution** — After you approve, the agent makes real API calls to GitHub Projects v2 to create the board, columns, labels, and milestones.
4. **Summary** — A Markdown report is saved to `output/` explaining every action and the reasoning behind it.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.10+ | Strong ecosystem for AI, clean syntax |
| LLM | Qwen3-32b via Groq (free tier) | Reasoning model, handles multi-step config logic |
| Action Target | GitHub Projects API (GraphQL) | Free, widely known |
| HTTP | `httpx` | Modern async-capable Python HTTP |
| Config | YAML | Human-readable, no code changes needed |

## Project Structure

```
├── main.py                  # Entry point
├── agent/
│   ├── loop.py              # Core ReAct agent loop
│   ├── llm.py               # Groq API communication
│   └── memory.py            # Message history management
├── tools/
│   ├── registry.py          # Tool definitions for the LLM
│   ├── github_tools.py      # GitHub API functions
│   └── executor.py          # Tool call dispatcher
├── prompts/
│   ├── system_prompt.txt    # Agent identity and behavior
│   └── summary_prompt.txt   # Summary generation instructions
├── config/
│   ├── agent_config.yaml    # Model, turns, temperature
│   └── interview_config.yaml# Discovery question definitions
└── output/                  # Generated summaries
```

## Prerequisites

- Python 3.10 or newer
- A GitHub account with a test repository
- A [Groq](https://console.groq.com) account (free, no credit card)

## Setup

1. **Clone and enter the project**

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your keys:
   - `GROQ_API_KEY` — from [console.groq.com](https://console.groq.com) (API Keys → Create API Key)
   - `GITHUB_TOKEN` — from GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic) with `repo` and `project` scopes
   - `GITHUB_REPO_OWNER` — your GitHub username
   - `GITHUB_REPO_NAME` — the repository to configure

4. **Run the agent**
   ```bash
   python main.py
   ```

## What the Agent Does

The agent discovers your team's needs through conversation and translates them into a working GitHub Project:

| Question | Drives |
|---|---|
| Team size | Column count, WIP limits |
| Sprint vs continuous flow | Whether to create milestones |
| Sprint duration | Milestone due dates |
| Work types (bugs, features, etc.) | Label set |
| Code review process | Review column on board |
| Project board name | Project title |

A reasoning model (Qwen3-32b) handles the multi-variable mapping: it considers all your answers together to make coherent configuration decisions.

## Architecture

This agent implements the ReAct (Reasoning + Acting) loop from first principles — no frameworks:

```
Loop:
  1. Send full conversation history + tool descriptions to the LLM
  2. LLM responds with either:
     a) A tool call → execute the function, add result to history, repeat
     b) A text message → print to user, wait for input, add reply, repeat
  3. Loop exits when LLM signals completion with [DONE]
```

Each component has a single responsibility:
- **loop.py** orchestrates (conductor, doesn't play any instrument)
- **llm.py** talks to Groq (thin HTTP wrapper)
- **memory.py** stores message history (typed list with helpers)
- **registry.py** describes tools (instructions for the LLM)
- **github_tools.py** calls GitHub (each function = one API action)
- **executor.py** dispatches tool calls (switchboard operator)

## "Done" Checklist

- [x] CLI conversation with discovery questions
- [x] Configuration plan presented before any API calls
- [x] Real GitHub Project created on confirmation
- [x] Columns, labels, and milestones created via API
- [x] Summary Markdown saved to `output/`
- [x] Ctrl+C exits cleanly
- [x] GitHub API errors handled gracefully
- [x] No API keys in code (only `.env`)
- [x] `.env` is in `.gitignore`
- [x] Maximum turn limit prevents infinite loops
- [x] Human-in-the-loop confirmation step
