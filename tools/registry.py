TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_repository_info",
            "description": (
                "Fetches repository info to validate it exists and is accessible. "
                "Call this first, before asking the user any questions, "
                "to confirm the repo is valid."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "GitHub owner (user or org). Defaults to env var.",
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name. Defaults to env var.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_project",
            "description": (
                "Creates a new GitHub Projects v2 board. "
                "Only call this after the user has confirmed the configuration plan. "
                "This must be the first tool called during execution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The display name for the project board",
                    },
                },
                "required": ["project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project_columns",
            "description": (
                "Creates a single-select 'Stage' field on the project board "
                "with the given column names as options. "
                "Call immediately after create_github_project, "
                "passing the project_id it returned."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID returned by create_github_project",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Ordered list of column/stage names "
                            "(e.g. ['Backlog', 'In Progress', 'Review', 'Done'])"
                        ),
                    },
                },
                "required": ["project_id", "columns"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_repository_labels",
            "description": (
                "Creates labels on the repository for categorizing issues. "
                "Call after columns are created."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Label display name (e.g. 'bug')",
                                },
                                "color": {
                                    "type": "string",
                                    "description": (
                                        "Hex color code without the # "
                                        "(e.g. 'ff0000' for red)"
                                    ),
                                },
                            },
                            "required": ["name", "color"],
                        },
                        "description": "List of label objects to create",
                    }
                },
                "required": ["labels"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_milestone",
            "description": (
                "Creates a milestone on the repository. "
                "Only call this if the user indicated they work in sprints."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Milestone name (e.g. 'Sprint 1')",
                    },
                    "due_date": {
                        "type": "string",
                        "description": (
                            "ISO 8601 due date (optional, e.g. '2025-06-01')"
                        ),
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the milestone",
                    },
                },
                "required": ["title"],
            },
        },
    },
]
