from tools.github_tools import (
    create_github_project,
    create_milestone,
    create_project_columns,
    create_repository_labels,
    get_repository_info,
)

TOOL_MAP = {
    "get_repository_info": get_repository_info,
    "create_github_project": create_github_project,
    "create_project_columns": create_project_columns,
    "create_repository_labels": create_repository_labels,
    "create_milestone": create_milestone,
}


def execute_tool(name, arguments):
    func = TOOL_MAP.get(name)
    if func is None:
        return {"success": False, "error": f"Unknown tool: '{name}'"}

    try:
        result = func(**arguments)
        return result
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for '{name}': {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing '{name}': {str(e)}",
        }
