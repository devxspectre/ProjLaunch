# Implementation Onboarding Agent — Spec Sheet
### A complete guide for building an AI agent that automates enterprise software onboarding
**Target Model:** Qwen3-32b via Groq (free tier)  
**Target Platform:** GitHub Projects API (free, no credit card)  
**Difficulty:** Beginner-friendly | **Estimated Build Time:** 10–14 days

---

## Table of Contents
1. [What We Are Building](#1-what-we-are-building)
2. [How an AI Agent Works — First Principles](#2-how-an-ai-agent-works--first-principles)
3. [Tech Stack](#3-tech-stack)
4. [Project Folder Structure](#4-project-folder-structure)
5. [File-by-File Specification](#5-file-by-file-specification)
6. [The Agent Loop — Explained](#6-the-agent-loop--explained)
7. [Tools Specification](#7-tools-specification)
8. [Data Flow — End to End](#8-data-flow--end-to-end)
9. [Discovery Interview Design](#9-discovery-interview-design)
10. [Environment & Setup Guide](#10-environment--setup-guide)
11. [What "Done" Looks Like](#11-what-done-looks-like)
12. [How to Frame This for the Interviewer](#12-how-to-frame-this-for-the-interviewer)

---

## 1. What We Are Building

### The Product
An **Implementation Onboarding Agent** — a conversational CLI tool that:

1. Interviews a user about their software team (size, workflow, methodology, preferences)
2. Reasons about those answers to make configuration decisions
3. Executes those decisions by making real API calls to GitHub Projects
4. Produces a written summary of everything it did and why

### Why This Maps to Lab0.ai
Lab0.ai's core product compresses enterprise software implementation (ERP, ITSM, identity platforms) from months of consulting work into an automated, self-serve agent experience. What consultants do — ask questions, map answers to decisions, configure systems — is exactly what this agent does. You are building a scaled-down version of their core loop.

### What the User Experience Looks Like

```
Agent: Hello! I'm going to set up a GitHub Project for your team.
       Let's start with a few questions.
       
       How many people are on your engineering team?

User:  We're a team of 5 developers.

Agent: Got it. Do you work in sprints (Scrum) or do you prefer
       a continuous flow (Kanban)?

User:  We do 2-week sprints.

...

Agent: Great. Based on your answers, here's what I'm going to configure:
       - Sprint board with 5 columns
       - WIP limits set to 2 per developer
       - Labels for: bug, feature, tech-debt
       - Milestone for your first sprint
       
       Shall I proceed? (yes/no)

User:  yes

Agent: ✓ Created project "Team Sprint Board"
       ✓ Created 5 columns: Backlog, Ready, In Progress, Review, Done
       ✓ Created 8 labels
       ✓ Created Milestone: Sprint 1
       
       Setup complete. Summary saved to output/summary.md
```

---

## 2. How an AI Agent Works — First Principles

### The Core Insight
A regular LLM responds to a message and stops. An AI agent responds, takes an action in the real world, observes the result, and then decides what to do next. It keeps going until the goal is achieved.

### The Three Building Blocks

**1. Tools**
A tool is simply a function that the LLM is allowed to call. You describe what the function does in plain English. The LLM reads your description and decides whether to call it, and with what arguments. You execute the function, capture the result, and feed it back to the LLM.

The LLM never executes the tool directly. It asks you to run it. You run it. You tell it what happened. This distinction is critical.

**2. Memory**
Memory in an agent is just the message history — a growing list of every message, tool call, and tool result that has happened so far. Every time you call the LLM, you send the entire history. The LLM has no persistent state of its own — the list you maintain IS the memory.

**3. The Loop**
The agent loop is:
```
while task is not complete:
    ask LLM what to do next (send full message history)
    if LLM calls a tool:
        run the tool
        add result to message history
    if LLM gives a final response:
        break the loop
        show the user the final response
```

This is the entirety of how agents work. Everything else — frameworks, orchestration systems, multi-agent patterns — is an abstraction built on top of this loop.

### Why Qwen3-32b for This Project
Qwen3-32b is a reasoning model. This means it "thinks" before responding — it runs an internal chain of thought before deciding what tool to call or what to say. For a discovery agent that needs to map answers to configurations, a reasoning model is ideal because it can handle multi-step logic like: "the user said 5 people AND Scrum → therefore WIP limit should be 2 → therefore I should call the tool with this specific argument."

---

## 3. Tech Stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.10+ | Strongest ecosystem for AI, clean syntax |
| LLM Provider | Groq | Free tier, supports Qwen3-32b, fast |
| LLM Model | qwen3-32b | Free on Groq, reasoning capability |
| Action Target | GitHub Projects API (GraphQL) | Free, widely known, good docs |
| HTTP Client | `httpx` | Modern, async-capable Python HTTP library |
| Env Management | `python-dotenv` | Load API keys from .env file |
| Config Files | YAML | Human-readable, easy to edit without code changes |
| Output | Markdown file | Clean, readable, shareable summary |
| CLI Interface | Plain `input()` / `print()` | No extra dependencies needed |

### Why Not Use a Framework (LangChain, etc.)
Frameworks are fine once you understand what they abstract. For this project, writing the loop yourself is intentional — it forces you to understand exactly how tool calling works. When the CTO asks "how does this work?", you can explain every line rather than saying "LangChain handles it."

---

## 4. Project Folder Structure

```
implementation-agent/
│
├── .env                          # API keys (never committed to git)
├── .env.example                  # Template showing what keys are needed
├── .gitignore                    # Excludes .env, __pycache__, output/
├── requirements.txt              # All Python dependencies
├── README.md                     # How to set up and run the project
│
├── main.py                       # Entry point — starts the agent
│
├── agent/
│   ├── __init__.py               # Makes agent/ a Python package
│   ├── loop.py                   # The core agent loop
│   ├── llm.py                    # All communication with the Groq API
│   └── memory.py                 # Manages message history
│
├── tools/
│   ├── __init__.py               # Makes tools/ a Python package
│   ├── registry.py               # Master list of all available tools
│   ├── github_tools.py           # Functions that call GitHub API
│   └── executor.py               # Receives tool call from LLM, runs it
│
├── prompts/
│   ├── system_prompt.txt         # The agent's identity and instructions
│   └── summary_prompt.txt        # Prompt used to generate the final summary
│
├── config/
│   ├── agent_config.yaml         # Model name, max turns, temperature etc.
│   └── interview_config.yaml     # The discovery questions and logic
│
└── output/
    └── .gitkeep                  # Empty folder tracked by git, summaries saved here
```

---

## 5. File-by-File Specification

---

### `main.py`
**Role:** The entry point. The only file a user needs to run.

**Responsibilities:**
- Load environment variables from `.env`
- Load configuration from `config/agent_config.yaml`
- Print a welcome message to the user
- Ask for the user's name and GitHub repository name
- Pass those inputs to the agent loop
- Handle graceful shutdown (Ctrl+C without stack traces)
- Print final status when complete

**Does NOT do:**
- Any LLM logic
- Any API calls
- Any tool execution
- Any prompt building

**Mental model:** Think of this as the `main()` function of a C program — it just bootstraps everything and hands off.

---

### `agent/loop.py`
**Role:** The brain of the operation. Implements the core ReAct loop.

**Responsibilities:**
- Accept the initial user context (team info provided at start)
- Maintain a turn counter to prevent infinite loops
- On each iteration: send current message history to the LLM
- Check if the LLM response contains a tool call
- If yes: pass the tool call to `executor.py`, get the result, add to memory
- If no: the LLM is giving a final text response — end the loop
- After the loop ends: trigger summary generation
- Save the summary to `output/`

**Key behavior — the stopping condition:**
The loop stops when either:
1. The LLM produces a plain text response with no tool call (it considers itself done)
2. The turn counter exceeds the maximum defined in config (safety limit)

**Does NOT do:**
- Know anything about Groq or HTTP
- Know anything about GitHub
- Parse tool arguments directly (delegates to executor)

**Mental model:** This is the conductor of an orchestra. It doesn't play any instrument, but it coordinates who plays when.

---

### `agent/llm.py`
**Role:** The only file that talks to Groq. All LLM communication lives here.

**Responsibilities:**
- Load the Groq API key from environment
- Build the correct request body for the Groq `/chat/completions` endpoint
- Attach the tools list (received as a parameter) to the request
- Send the request using `httpx`
- Parse the response and return a structured object that `loop.py` can understand
- Handle API errors (rate limits, timeouts) with retries and clear error messages

**Returns to the caller:** A simple object/dict with two fields:
- `response_type`: either `"tool_call"` or `"message"`
- `content`: either the tool call details OR the text message

**Does NOT do:**
- Decide which tools to attach (that comes from registry.py)
- Interpret what the tool call means (that's executor.py)
- Store any history (that's memory.py)

**Mental model:** This is a thin HTTP wrapper. Its only job is "send this payload to Groq, return what comes back in a clean format."

---

### `agent/memory.py`
**Role:** Manages the message history that constitutes the agent's memory.

**Responsibilities:**
- Store messages as a list of dicts in the format the Groq API expects
- Provide methods to add: user messages, assistant messages, tool call messages, tool result messages
- Provide a method to retrieve the full history for sending to the LLM
- Load the system prompt from `prompts/system_prompt.txt` and prepend it to history on initialization

**The four message types it handles:**
1. `system` — the agent's identity and instructions (added once at start)
2. `user` — what the human typed
3. `assistant` — what the LLM said (including tool call requests)
4. `tool` — the result of a tool execution

**Does NOT do:**
- Any LLM calls
- Any persistence (messages only live in RAM during one session)
- Any summarization or compression

**Mental model:** Think of this as a typed list with helper methods. It is the memory. Nothing more.

---

### `tools/registry.py`
**Role:** The master list of all tools the LLM is allowed to use.

**Responsibilities:**
- Define each tool as a structured description that the Groq API can understand
- For each tool, specify: name, description, and the parameters it accepts (with types and descriptions)
- Export a single list called `TOOLS` that `llm.py` attaches to every request

**This is critical to understand:** The tool descriptions are not just documentation — they are instructions to the LLM. The clearer and more specific your descriptions, the better the LLM will know when and how to call each tool. A vague description leads to wrong arguments.

**Example of what a good tool description contains:**
- What the tool does in one sentence
- When the LLM should use it (and when NOT to)
- Every parameter explained precisely
- What the tool returns

**Does NOT do:**
- Execute any tools
- Import from `github_tools.py` directly

---

### `tools/github_tools.py`
**Role:** All functions that make real GitHub API calls.

**Responsibilities:**
- Load the GitHub token and target repo from environment variables
- Implement each GitHub action as a separate, clearly named function:
  - Create a GitHub Project
  - Create columns/fields within the project
  - Create labels on the repository
  - Create a milestone
  - Get existing project/repo info (for validation)
- Return results as simple dicts (success/failure + relevant IDs)
- Handle GitHub API errors gracefully and return error messages rather than crashing

**GitHub API notes for the implementer:**
- GitHub Projects v2 uses GraphQL, not REST. This means you POST queries as strings to `https://api.github.com/graphql`
- The GitHub personal access token needs: `project`, `repo` scopes
- All responses are nested JSON — the implementer will need to navigate the response carefully

**Does NOT do:**
- Decide when to call these functions (that's the LLM's job via executor)
- Format output for display (just return raw data)

---

### `tools/executor.py`
**Role:** The bridge between what the LLM asks for and what actually runs.

**Responsibilities:**
- Receive a tool call object from `loop.py` (contains: tool name + arguments as a dict)
- Look up which Python function corresponds to that tool name
- Call the function with the provided arguments
- Return the result as a string (LLMs expect tool results as text)
- Handle unknown tool names gracefully (return an error string, don't crash)

**The mapping it maintains:**
A simple dictionary that maps tool name strings to Python function references. For example: `"create_github_project"` → `github_tools.create_project`

**Does NOT do:**
- Import every tool at the top level (only import what's in the map)
- Validate arguments (trust the LLM has provided them correctly per the registry spec)
- Know anything about the LLM or Groq

**Mental model:** This is a switchboard operator. Someone says "connect me to create_github_project" — it looks up the number and dials it.

---

### `prompts/system_prompt.txt`
**Role:** Defines the agent's identity, behavior, and constraints.

**What it should contain:**
1. **Identity** — "You are an implementation specialist agent for software teams."
2. **Goal** — "Your job is to gather information about a team through conversation and then configure a GitHub Project for them."
3. **Behavior rules:**
   - Always confirm the full configuration plan with the user before executing any tools
   - Ask one or two questions at a time — do not overwhelm the user
   - If the user says something ambiguous, ask for clarification before proceeding
   - Never make assumptions about team size, workflow, or preferences — always ask
4. **Tool usage rules:**
   - Only call tools after the user has confirmed the plan
   - Always call tools in order: create project first, then columns, then labels, then milestones
5. **Tone** — Professional but friendly. Concise questions. No jargon.

**Why this matters:** The system prompt is the most impactful thing you can change to improve agent behavior. 80% of agent quality problems are prompt problems, not code problems.

---

### `prompts/summary_prompt.txt`
**Role:** A one-time prompt used at the end to generate the written summary.

**What it should instruct the LLM to produce:**
- A brief description of the team that was onboarded
- A list of every action taken and why it was taken
- The reasoning behind key decisions (e.g., "WIP limit was set to 2 because the team size is 5 and they use Scrum")
- Next recommended steps for the team
- Output format: clean Markdown with headings

**How it is used:** After the main loop ends, `loop.py` makes one final LLM call with the full conversation history plus this prompt appended, asking for the summary.

---

### `config/agent_config.yaml`
**Role:** All tunable settings in one place. No code changes needed to adjust behavior.

**What it contains:**
- `model`: the model name string Groq expects (e.g., `qwen-qwq-32b`)
- `max_turns`: maximum loop iterations before force-stopping (safety; recommended: 20)
- `temperature`: how creative vs deterministic the LLM is (0.6 is a good starting point for reasoning models)
- `max_tokens`: max length of each LLM response
- `groq_api_base_url`: the Groq endpoint URL (makes it easy to switch providers)

**Why YAML and not hardcoded constants:** A junior developer or tester should be able to change the model or the turn limit without touching Python. Config belongs in config files.

---

### `config/interview_config.yaml`
**Role:** Documents the intended discovery flow. Not used programmatically — it is a reference for writing the system prompt.

**What it contains:**
A structured definition of:
- The questions the agent should ask (in rough order)
- What each answer implies for configuration
- Decision logic in plain English

**Example structure in the YAML:**
```
questions:
  - id: team_size
    ask: "How many people are on your engineering team?"
    implications:
      1-3: "Small team — single WIP limit of 1, minimal columns"
      4-8: "Medium team — WIP limit of 2, standard 5-column board"
      9+:  "Large team — WIP limit of 3, add a triage column"

  - id: methodology
    ask: "Do you work in sprints or continuous flow?"
    implications:
      sprints: "Enable milestone per sprint, add Sprint column"
      continuous: "No milestones, add priority labels instead"
```

**Why this file exists:** It forces you to think through the decision logic before coding. When writing the system prompt, you translate this YAML into instructions for the LLM.

---

### `.env`
**Role:** Stores all secrets. Never committed to git.

**Contains:**
- `GROQ_API_KEY` — from console.groq.com
- `GITHUB_TOKEN` — personal access token from GitHub settings
- `GITHUB_REPO_OWNER` — your GitHub username
- `GITHUB_REPO_NAME` — the repo to configure

---

### `.env.example`
**Role:** A committed template showing which keys are required, with placeholder values.

**Purpose:** Anyone cloning the repo knows exactly what to fill in without reading the code.

---

### `requirements.txt`
**Role:** Pin all dependencies so the project works identically on any machine.

**Dependencies to include:**
- `httpx` — HTTP client for API calls
- `python-dotenv` — load .env files
- `pyyaml` — read YAML config files
- `rich` (optional but recommended) — makes CLI output much more readable with colors and formatting

---

## 6. The Agent Loop — Explained

The following describes what happens step by step when a user runs the agent. No code — just the logical sequence.

```
START
  │
  ▼
Load config, load .env, print welcome message
  │
  ▼
Ask user: "What's your GitHub repo name?"
Add that as the first user message to memory
  │
  ▼
┌─────────────────────────────────────────────────┐
│                  AGENT LOOP                      │
│                                                  │
│  1. Send full message history + tools to Groq    │
│                                                  │
│  2. Get response back                            │
│       │                                          │
│       ├── Is it a TOOL CALL?                     │
│       │       │                                  │
│       │       ▼                                  │
│       │   executor.py runs the tool              │
│       │   Result added to memory as tool result  │
│       │   → Go back to step 1                    │
│       │                                          │
│       └── Is it a TEXT MESSAGE?                  │
│               │                                  │
│               ▼                                  │
│           Print message to user                  │
│           Wait for user to type reply            │
│           Add reply to memory                    │
│           → Go back to step 1                    │
│                                                  │
│  (loop exits when LLM produces final response    │
│   with no tool call and no question)             │
└─────────────────────────────────────────────────┘
  │
  ▼
Generate summary (one final LLM call with summary prompt)
  │
  ▼
Save summary to output/summary_TIMESTAMP.md
  │
  ▼
Print "Setup complete. Summary saved to output/"
END
```

---

## 7. Tools Specification

These are the five tools the agent has access to. Each is a description of what the function does and what arguments it needs.

---

### Tool 1: `create_github_project`
**What it does:** Creates a new GitHub Projects v2 board linked to a repository.

**Arguments:**
- `project_name` (string) — the display name of the project
- `project_description` (string) — a brief description

**Returns:** The new project's ID (needed for subsequent tools) or an error message.

**When the LLM should call this:** Only once, as the very first action, after user confirmation.

---

### Tool 2: `create_project_columns`
**What it does:** Creates the status columns (workflow stages) on the project board.

**Arguments:**
- `project_id` (string) — the ID returned by `create_github_project`
- `columns` (list of strings) — the ordered list of column names to create

**Returns:** Confirmation that columns were created, or an error.

**When the LLM should call this:** Immediately after the project is created.

---

### Tool 3: `create_repository_labels`
**What it does:** Creates colored labels on the GitHub repository for categorizing issues.

**Arguments:**
- `labels` (list of objects) — each object has `name` (string) and `color` (hex string without #)

**Returns:** A list of labels that were successfully created.

**When the LLM should call this:** After columns are created.

---

### Tool 4: `create_milestone`
**What it does:** Creates a milestone on the repository (used to group issues by sprint).

**Arguments:**
- `title` (string) — name of the milestone (e.g., "Sprint 1")
- `due_date` (string, optional) — ISO 8601 date string (e.g., "2025-06-01")
- `description` (string, optional) — brief description

**Returns:** The milestone number, or an error.

**When the LLM should call this:** Only if the user indicated they work in sprints.

---

### Tool 5: `get_repository_info`
**What it does:** Fetches basic information about the target repository to validate it exists and is accessible.

**Arguments:**
- None (uses repo info from environment variables)

**Returns:** Repo name, owner, visibility, and whether Projects are enabled.

**When the LLM should call this:** At the very start, before asking questions, to confirm the repo is valid. If the repo doesn't exist or the token lacks permissions, the agent should tell the user immediately rather than asking 10 questions and then failing.

---

## 8. Data Flow — End to End

This describes how data moves through the system from the user's first input to the final saved file.

```
User types repo name
        │
        ▼
main.py captures input
        │
        ▼
loop.py adds it to memory.py as a user message
        │
        ▼
loop.py calls llm.py with (message history, tools from registry.py)
        │
        ▼
llm.py sends POST request to Groq API
        │
        ▼
Groq returns response (tool call OR text)
        │
        ├─── TOOL CALL path ─────────────────────────────────────────┐
        │                                                             │
        │   loop.py passes tool name + args to executor.py           │
        │   executor.py maps name → function in github_tools.py      │
        │   github_tools.py calls GitHub API via httpx               │
        │   GitHub returns result                                     │
        │   github_tools.py returns clean dict                       │
        │   executor.py converts to string                           │
        │   loop.py adds to memory.py as tool result message         │
        │   → loops back to llm.py call                              │
        │                                                             │
        └─── TEXT MESSAGE path ──────────────────────────────────────┘
                                                                      │
            loop.py prints message to terminal                        │
            User reads and types reply                                │
            loop.py adds reply to memory.py as user message          │
            → loops back to llm.py call                              │
                                                                      │
        (after loop ends)
        │
        ▼
loop.py calls llm.py one more time with summary_prompt.txt appended
        │
        ▼
LLM generates markdown summary
        │
        ▼
loop.py writes summary to output/summary_TIMESTAMP.md
        │
        ▼
main.py prints completion message to user
```

---

## 9. Discovery Interview Design

This section defines the questions the agent should ask and the decisions each answer drives. Use this to write the system prompt.

### Phase 1 — Validation (before any questions)
The agent silently calls `get_repository_info` to confirm the repo exists.
- If it fails: agent tells the user and asks to confirm the repo name before proceeding.
- If it succeeds: agent begins the interview.

### Phase 2 — Team Discovery

| Question | Purpose | Drives |
|---|---|---|
| How many people on your team? | Scale columns and WIP limits | Column count, WIP limit value |
| Do you work in sprints or continuous flow? | Workflow type | Whether to create milestones |
| If sprints: how long are your sprints? | Sprint duration | Milestone due date calculation |
| What types of work does your team do? (bugs, features, tech debt, etc.) | Label set | Which labels to create |
| Does your team do code reviews before merging? | Process step | Whether to add a "Review" column |
| What would you like to name this project board? | Naming | project_name argument |

### Phase 3 — Confirmation (before any API calls)
After gathering all answers, the agent must present a **complete plan** in plain language and ask for a yes/no confirmation before calling any tools. This is not optional — it is defined in the system prompt as required behavior.

### Phase 4 — Execution
Only after user confirmation does the agent begin calling tools, in this fixed order:
1. `create_github_project`
2. `create_project_columns`
3. `create_repository_labels`
4. `create_milestone` (only if sprints)

### Phase 5 — Summary Generation
After all tools complete, the agent generates and saves the summary.

---

## 10. Environment & Setup Guide

### Prerequisites
- Python 3.10 or newer installed
- A GitHub account with a test repository created (can be empty)
- A Groq account (free, no credit card) at console.groq.com

### Groq Setup
1. Sign up at console.groq.com
2. Navigate to API Keys → Create API Key
3. Copy the key into `.env` as `GROQ_API_KEY`
4. The model name string to use: check Groq's model list for the exact Qwen3-32b identifier (it changes — verify on their docs page at the time of building)

### GitHub Token Setup
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate a new token with scopes: `repo` (full) and `project`
3. Copy into `.env` as `GITHUB_TOKEN`

### Running the Project
```bash
# 1. Clone / create the project folder
# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy .env.example to .env and fill in your keys
cp .env.example .env

# 5. Run
python main.py
```

---

## 11. What "Done" Looks Like

The project is complete when all of the following are true:

### Functional Checklist
- [ ] Running `python main.py` starts a conversation in the terminal
- [ ] The agent asks relevant discovery questions (not all at once)
- [ ] The agent presents a configuration plan before taking any action
- [ ] After user confirms, the agent creates a real project on GitHub
- [ ] Columns, labels, and milestones appear correctly in the GitHub UI
- [ ] A summary markdown file is saved in `output/`
- [ ] Ctrl+C exits cleanly without a stack trace

### Quality Checklist
- [ ] The agent does not ask redundant questions
- [ ] If a GitHub API call fails, the agent reports it clearly and does not crash
- [ ] The agent handles "no" at the confirmation step gracefully (asks what to change)
- [ ] The summary explains the reasoning behind each decision, not just what was done

### Code Quality Checklist
- [ ] No API keys appear anywhere except `.env`
- [ ] `.env` is in `.gitignore`
- [ ] Each file does only what its spec says — no cross-cutting responsibilities
- [ ] The loop in `loop.py` has a maximum turn limit and respects it

---

## 12. How to Frame This for the Interviewer

When presenting this project to the CTO of Lab0.ai, do not lead with the code. Lead with the thinking.

**Opening statement to use:**

> "I studied your product and saw that the core problem is replacing a consultant's workflow with an agent. A consultant asks questions, maps answers to decisions, and executes configurations. I built a minimal version of that loop from scratch — no frameworks — so I could understand every component. This agent interviews a team, reasons about their answers using Qwen3-32b, and configures a real GitHub Project through live API calls."

**Points to emphasize:**

1. **You built the loop yourself.** You can explain exactly what happens at every step: message history, tool call format, executor dispatch, result injection. No black boxes.

2. **The reasoning model choice was deliberate.** Qwen3-32b reasons before acting. For mapping multi-variable inputs (team size AND methodology AND review process) to configuration decisions, a reasoning model is more reliable than a standard one. You chose it because of the problem, not because of convenience.

3. **The confirmation step is a design decision, not a nicety.** Enterprise software implementation agents need human-in-the-loop checkpoints before taking irreversible actions. This is exactly what Lab0.ai describes as "AI with guardrails." You built that in on purpose.

4. **The folder structure separates concerns intentionally.** The LLM communication layer, the tool execution layer, and the memory layer are all separate. Ask them to look at any file — each one does exactly one thing.

5. **This scales.** The same architecture — swap GitHub for SAP or ServiceNow, expand the tool registry, deepen the interview logic — is how you'd build the real product. The skeleton is the same.

---

*Spec version 1.0 — Built for Lab0.ai CTO interview preparation*