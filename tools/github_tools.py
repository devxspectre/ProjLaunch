import os
import time
import sys
import webbrowser

import httpx

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


def _token():
    return os.environ.get("GITHUB_TOKEN")


def _repo_owner():
    return os.environ.get("GITHUB_REPO_OWNER")


def _repo_name():
    return os.environ.get("GITHUB_REPO_NAME")


def authenticate_github():
    token = _token()
    if token:
        return token

    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "[Error] No GitHub credentials found. Set GITHUB_TOKEN in .env "
            "or add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET for OAuth."
        )
        sys.exit(1)

    print("\nAuthenticating with GitHub...")
    resp = httpx.post(
        "https://github.com/login/device/code",
        json={"client_id": client_id, "scope": "repo project"},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"\n[Error] GitHub device code request failed: {resp.text}")
        sys.exit(1)
    device = resp.json()

    user_code = device["user_code"]
    device_code = device["device_code"]
    interval = device.get("interval", 5)
    verification_uri = device.get("verification_uri", "https://github.com/login/device")

    combined_url = f"{verification_uri}?user_code={user_code}"
    webbrowser.open(combined_url)
  
    print(f"\n  → Open: {combined_url}")
    print("  (Or manually enter the code below)")
    print(f"  → Code: {user_code}")
    print("\n  Waiting for authorization...")

    while True:
        time.sleep(interval)
        resp = httpx.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        if "access_token" in result:
            token = result["access_token"]
            os.environ["GITHUB_TOKEN"] = token
            verify = httpx.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if verify.status_code == 401:
                print(
                    "  ✗ Token received but is invalid (401). "
                    "Check that your GitHub App has 'repo' and 'project' scopes."
                )
                sys.exit(1)
            scopes = verify.headers.get("X-OAuth-Scopes", "none")
            print(f"  ✓ Authorized (scopes: {scopes})")
            return token
        elif result.get("error") == "authorization_pending":
            continue
        elif result.get("error") == "slow_down":
            interval += 5
            continue
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            print(f"\n[Error] GitHub OAuth failed: {error}")
            sys.exit(1)


def _graphql(query, variables=None):
    token = _token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"query": query}
    if variables:
        body["variables"] = variables
    resp = httpx.post(GITHUB_GRAPHQL, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _rest(method, path, data=None):
    token = _token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    url = f"{GITHUB_API}{path}"
    resp = httpx.request(method, url, headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    return resp


def get_repository_info(owner=None, repo=None):
    owner = owner or _repo_owner()
    repo = repo or _repo_name()
    if not all([_token(), owner, repo]):
        return {
            "success": False,
            "error": (
                "Missing GitHub configuration. Ensure GITHUB_TOKEN, "
                "GITHUB_REPO_OWNER, and GITHUB_REPO_NAME are set."
            ),
        }

    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        owner { login }
        isPrivate
        hasIssuesEnabled
      }
    }
    """
    try:
        data = _graphql(query, {"owner": owner, "name": repo})
        if "errors" in data:
            return {"success": False, "error": data["errors"][0]["message"]}
        repo_data = data["data"]["repository"]
        if repo_data is None:
            return {
                "success": False,
                "error": f"Repository {owner}/{repo} not found",
            }
        return {
            "success": True,
            "name": repo_data["name"],
            "owner": repo_data["owner"]["login"],
            "visibility": "private" if repo_data["isPrivate"] else "public",
            "has_issues": repo_data["hasIssuesEnabled"],
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": (
                f"GitHub API error: {e.response.status_code} - "
                f"{e.response.text[:200]}"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_github_project(project_name):
    if not _token():
        return {"success": False, "error": "GITHUB_TOKEN is not set"}

    try:
        viewer_query = "query { viewer { id } }"
        viewer_data = _graphql(viewer_query)
        if "errors" in viewer_data:
            return {"success": False, "error": viewer_data["errors"][0]["message"]}
        owner_id = viewer_data["data"]["viewer"]["id"]

        mutation = """
        mutation($ownerId: ID!, $title: String!) {
          createProjectV2(input: {
            ownerId: $ownerId
            title: $title
          }) {
            projectV2 {
              id
              number
              title
              url
            }
          }
        }
        """
        result = _graphql(
            mutation,
            {
                "ownerId": owner_id,
                "title": project_name,
            },
        )
        if "errors" in result:
            return {"success": False, "error": result["errors"][0]["message"]}
        project = result["data"]["createProjectV2"]["projectV2"]
        return {
            "success": True,
            "project_id": project["id"],
            "project_number": project["number"],
            "title": project["title"],
            "url": project["url"],
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": (
                f"GitHub API error: {e.response.status_code} - "
                f"{e.response.text[:200]}"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_project_columns(project_id, columns):
    COLORS = ["GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE"]
    options = [
        {"name": col, "color": COLORS[i % len(COLORS)], "description": col}
        for i, col in enumerate(columns)
    ]

    mutation = """
    mutation($projectId: ID!, $name: String!, $singleSelectOptions: [ProjectV2SingleSelectFieldOptionInput!]) {
      createProjectV2Field(
        input: {
          projectId: $projectId
          dataType: SINGLE_SELECT
          name: $name
          singleSelectOptions: $singleSelectOptions
        }
      ) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
    """
    try:
        result = _graphql(
            mutation,
            {"projectId": project_id, "name": "Stage", "singleSelectOptions": options},
        )
        if "errors" in result:
            err_msg = result["errors"][0]["message"]
            return {"success": False, "error": err_msg}
        field = result["data"]["createProjectV2Field"]["projectV2Field"]
        return {
            "success": True,
            "field_id": field["id"],
            "field_name": field["name"],
            "columns": columns,
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": (
                f"GitHub API error: {e.response.status_code} - "
                f"{e.response.text[:200]}"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_repository_labels(labels):
    owner = _repo_owner()
    repo = _repo_name()
    if not all([owner, repo]):
        return {
            "success": False,
            "error": "GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set",
        }

    created = []
    for label in labels:
        resp = _rest(
            "POST",
            f"/repos/{owner}/{repo}/labels",
            {"name": label["name"], "color": label["color"]},
        )
        if resp.status_code == 201:
            created.append(label["name"])
        elif resp.status_code == 422:
            created.append(f"{label['name']} (already exists)")
        else:
            return {
                "success": False,
                "error": (
                    f"Failed to create label '{label['name']}': "
                    f"{resp.text[:200]}"
                ),
            }

    return {"success": True, "created": created}


def create_milestone(title, due_date=None, description=None):
    owner = _repo_owner()
    repo = _repo_name()
    if not all([owner, repo]):
        return {
            "success": False,
            "error": "GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set",
        }

    data = {"title": title}
    if due_date:
        data["due_on"] = f"{due_date}T23:59:59Z"
    if description:
        data["description"] = description

    try:
        resp = _rest(
            "POST",
            f"/repos/{owner}/{repo}/milestones",
            data,
        )
        if resp.status_code == 201:
            return {
                "success": True,
                "number": resp.json()["number"],
                "title": title,
            }
        if resp.status_code == 422:
            error_body = resp.json()
            already_exists = any(
                err.get("message") == "name already exists"
                for err in error_body.get("errors", [])
            )
            if already_exists:
                return {"success": True, "title": title, "already_existed": True}
            api_errors = error_body.get("errors", [])
            details = "; ".join(
                e.get("message", str(e)) for e in api_errors
            ) or resp.text[:200]
            return {
                "success": False,
                "error": f"Milestone '{title}' invalid: {details}",
            }
        return {
            "success": False,
            "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
