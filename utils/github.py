import requests
import json


def read_github_json(owner, repo, branch, file_path, token):
    """
    Read a JSON file from a private GitHub repository.

    Args:
        owner: GitHub username or organization
        repo: Repository name
        branch: Branch name (e.g., 'main', 'feat/schema')
        file_path: Path to the file in the repo
        token: GitHub Personal Access Token

    Returns:
        dict: Parsed JSON data
    """
    # GitHub API URL for file contents
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"

    # Headers with authentication
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Add branch parameter
    params = {"ref": branch}

    try:
        # Make the request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Get the content (it's base64 encoded)
        import base64

        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")

        # Parse JSON
        json_data = json.loads(file_content)
        return json_data

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
