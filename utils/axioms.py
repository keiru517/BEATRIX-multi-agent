import os
import re
import ast

from dotenv import load_dotenv

from utils.http_client import HTTPClient

load_dotenv()

http_client = HTTPClient(
    base_url=os.getenv("FEH_ADVICE_API_URL"),
    timeout=10,
    auth_token=os.getenv("FEH_ADVICE_API_BEARER_TOKEN"),
)


def load_axioms(chapter_content_id: int):
    """Load axioms"""

    # TODO: need to update
    endpoint = "/api/openapi/endpoints/6931568f18f19/text"
    chapter_content_id = 10945
    response = http_client.get(
        endpoint, params={"chapter_content_id": chapter_content_id}
    )
    # Extract JSON from HTML-wrapped response
    cleaned_response = _extract_info(response["text"])
    return cleaned_response


# TODO: need to remove this after updating the API to return JSON
def _extract_info(text):
    # Remove invalid trailing commas and fix Python-style dicts
    cleaned = text.replace("\n", "").replace("\r", "")

    # Fix missing commas between blocks using regex (optional improvement)
    cleaned = re.sub(r"}\s*{", "}, {", cleaned)

    # Extract top-level metadata (version, total_axioms, etc.)
    meta_pattern = r"'version':\s*'([^']+)'|'module_id':\s*'([^']+)'|'module_title':\s*'([^']+)'|'total_axioms':\s*([0-9]+)"
    meta_matches = re.findall(meta_pattern, cleaned)

    metadata = {
        "module_id": None,
        "module_title": None,
        "version": None,
        "total_axioms": None,
    }

    # Fill metadata from regex groups
    for match in meta_matches:
        if match[0]:
            metadata["version"] = match[0]
        if match[1]:
            metadata["module_id"] = match[1]
        if match[2]:
            metadata["module_title"] = match[2]
        if match[3]:
            metadata["total_axioms"] = int(match[3])

    # Extract axioms (everything inside `'axioms': [ ... ]`)
    axioms_block = re.search(r"'axioms':\s*\[(.*)\]\s*", cleaned)
    axioms_list = []

    if axioms_block:
        block = axioms_block.group(1)
        # Split into individual dictionaries using pattern `{'execution_step'...}`
        axiom_entries = re.findall(r"\{[^{}]+\}", block)

        for ax in axiom_entries:
            try:
                # Convert string dict to Python dict
                axiom_data = ast.literal_eval(ax)
                axioms_list.append(axiom_data)
            except:
                pass  # skip malformed entries

    return {"version_info": metadata, "axioms": axioms_list}
