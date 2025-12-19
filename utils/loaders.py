import requests
import json
import os

from utils.logger import get_app_logger

logger = get_app_logger(__name__)


def load_module_data():
    OWNER = "FehrAdvice-Partners-AG"
    REPO = "beatrix-api"
    BRANCH = "feat/schema"
    TOKEN = os.getenv("GITHUB_TOKEN")
    MODULE_PATHS = [
        "awx/awx.json",
        "context/context.json",
        "idn/idn.json",
        "int/int.json",
        "inu/inu.json",
        "jny/jny.json",
        "knu/knu.json",
        "meta/meta.json",
        "seg/seg.json",
        "wax/wax.json",
        "wtx/wtx.json",
    ]
    modules = {}
    for path in MODULE_PATHS:
        data = _read_github_json(OWNER, REPO, BRANCH, path, TOKEN)
        if data:
            modules[path.split("/")[0].upper()] = data
            modules[path.split("/")[0].upper()]["module"][
                "I_t"
            ] = _initialize_integrity()
            modules[path.split("/")[0].upper()]["module"][
                "I_prev"
            ] = _initialize_integrity()

        else:
            logger.error(f"Failed to read module data from {path}")
            return None
    return modules


def _read_github_json(owner, repo, branch, file_path, token):
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


def _initialize_integrity():
    """
    Initialize the integrity of the system.

    Args:
        None
    Returns:
        I0: The initial integrity of the system
    """
    # TODO: need to get intial integrity from STD 9232 v2.3
    # S = structure, M = semantics, C = context, O = operational

    defaults = dict(S=1.0, M=0.85, C=0.5, O=0.25)
    weights = dict(S=0.25, M=0.25, C=0.25, O=0.25)
    I0 = sum(defaults[k] * weights[k] for k in defaults)
    return I0
