import json
from unittest.mock import patch

import httpx
import tools.github_tools as gt


def test_create_project_columns_success():
    mock_response = {
        "data": {
            "createProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "field_123",
                    "name": "Stage",
                    "options": [
                        {"id": "opt_1", "name": "Backlog"},
                        {"id": "opt_2", "name": "Ready"},
                    ],
                }
            }
        }
    }
    with patch("tools.github_tools._graphql", return_value=mock_response):
        result = gt.create_project_columns(
            "PVT_123", ["Backlog", "Ready", "In Progress", "Review", "Done"]
        )

    assert result["success"] is True
    assert result["field_id"] == "field_123"
    assert result["field_name"] == "Stage"
    assert result["columns"] == ["Backlog", "Ready", "In Progress", "Review", "Done"]


def test_create_project_columns_passes_correct_mutation():
    captured = {}

    def fake_graphql(query, variables):
        captured["query"] = query
        captured["variables"] = variables
        return {
            "data": {
                "createProjectV2Field": {
                    "projectV2Field": {
                        "__typename": "ProjectV2SingleSelectField",
                        "id": "f_1",
                        "name": "Stage",
                        "options": [],
                    }
                }
            }
        }

    with patch("tools.github_tools._graphql", side_effect=fake_graphql):
        gt.create_project_columns("PVT_abc", ["Todo", "Done"])

    assert captured["variables"]["projectId"] == "PVT_abc"
    assert captured["variables"]["name"] == "Stage"
    assert captured["variables"]["singleSelectOptions"] == [
        {"name": "Todo", "color": "GRAY", "description": "Todo"},
        {"name": "Done", "color": "BLUE", "description": "Done"},
    ]
    assert "$singleSelectOptions: [ProjectV2SingleSelectFieldOptionInput!]" in captured["query"]
    assert "singleSelectOptions: $singleSelectOptions" in captured["query"]
    assert "dataType: SINGLE_SELECT" in captured["query"]
    assert "... on ProjectV2SingleSelectField" in captured["query"]
    assert "projectV2Field {" in captured["query"]


def test_create_project_columns_with_graphql_error():
    mock_response = {"errors": [{"message": "Project not found"}]}
    with patch("tools.github_tools._graphql", return_value=mock_response):
        result = gt.create_project_columns("PVT_invalid", ["Backlog"])

    assert result["success"] is False
    assert result["error"] == "Project not found"


def test_create_project_columns_with_http_error():
    request = httpx.Request("POST", "https://api.github.com/graphql")
    response = httpx.Response(401, request=request, text='{"message": "Bad credentials"}')
    with patch("tools.github_tools._graphql", side_effect=httpx.HTTPStatusError(
        "401 Unauthorized", request=request, response=response
    )):
        result = gt.create_project_columns("PVT_123", ["Backlog"])

    assert result["success"] is False
    assert "GitHub API error: 401" in result["error"]


def test_create_project_columns_with_generic_exception():
    with patch("tools.github_tools._graphql", side_effect=ValueError("something broke")):
        result = gt.create_project_columns("PVT_123", ["Backlog"])

    assert result["success"] is False
    assert result["error"] == "something broke"


def test_create_project_columns_empty_columns():
    mock_response = {
        "data": {
            "createProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "f_1",
                    "name": "Stage",
                    "options": [],
                }
            }
        }
    }
    with patch("tools.github_tools._graphql", return_value=mock_response):
        result = gt.create_project_columns("PVT_123", [])

    assert result["success"] is True
    assert result["columns"] == []


def test_create_project_columns_color_cycling():
    captured = {}
    def fake_graphql(query, variables):
        captured["options"] = variables["singleSelectOptions"]
        return {
            "data": {
                "createProjectV2Field": {
                    "projectV2Field": {
                        "__typename": "ProjectV2SingleSelectField",
                        "id": "f_1",
                        "name": "Stage",
                        "options": [],
                    }
                }
            }
        }

    with patch("tools.github_tools._graphql", side_effect=fake_graphql):
        gt.create_project_columns("PVT_123", ["A", "B", "C", "D", "E", "F", "G", "H", "I"])

    assert len(captured["options"]) == 9
    assert captured["options"][0] == {"name": "A", "color": "GRAY", "description": "A"}
    assert captured["options"][7] == {"name": "H", "color": "PURPLE", "description": "H"}
    assert captured["options"][8] == {"name": "I", "color": "GRAY", "description": "I"}


def test_create_project_columns_single_column():
    mock_response = {
        "data": {
            "createProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "f_1",
                    "name": "Stage",
                    "options": [{"id": "opt_1", "name": "Backlog"}],
                }
            }
        }
    }
    with patch("tools.github_tools._graphql", return_value=mock_response):
        result = gt.create_project_columns("PVT_123", ["Backlog"])

    assert result["success"] is True
    assert result["columns"] == ["Backlog"]


def test_create_milestone_success():
    mock_resp = _fake_response(201, {"number": 42})
    with (patch("tools.github_tools._repo_owner", return_value="o"),
          patch("tools.github_tools._repo_name", return_value="r"),
          patch("tools.github_tools._rest", return_value=mock_resp)):
        result = gt.create_milestone("Sprint 7", "2025-05-25", "desc")

    assert result["success"] is True
    assert result["number"] == 42
    assert result["title"] == "Sprint 7"


def test_create_milestone_iso_date_format():
    captured = {}
    def fake_rest(method, path, data):
        captured["data"] = data
        return _fake_response(201, {"number": 1})
    with (patch("tools.github_tools._repo_owner", return_value="o"),
          patch("tools.github_tools._repo_name", return_value="r"),
          patch("tools.github_tools._rest", side_effect=fake_rest)):
        gt.create_milestone("Sprint", "2025-05-25", "desc")

    assert captured["data"]["due_on"] == "2025-05-25T23:59:59Z"


def test_create_milestone_already_exists():
    mock_resp = _fake_response(422, {"errors": [{"message": "name already exists"}]})
    with (patch("tools.github_tools._repo_owner", return_value="o"),
          patch("tools.github_tools._repo_name", return_value="r"),
          patch("tools.github_tools._rest", return_value=mock_resp)):
        result = gt.create_milestone("Sprint 7")

    assert result["success"] is True
    assert result["already_existed"] is True


def test_create_milestone_validation_error():
    mock_resp = _fake_response(
        422, {"errors": [{"message": "due_on is invalid"}]}
    )
    with (patch("tools.github_tools._repo_owner", return_value="o"),
          patch("tools.github_tools._repo_name", return_value="r"),
          patch("tools.github_tools._rest", return_value=mock_resp)):
        result = gt.create_milestone("Sprint 7", "bad-date")

    assert result["success"] is False
    assert "due_on is invalid" in result["error"]


def _fake_response(status_code, json_body):
    resp = httpx.Response(status_code)
    resp._content = json.dumps(json_body).encode()
    return resp
