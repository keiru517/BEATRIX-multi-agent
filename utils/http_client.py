import requests
from typing import Dict, Any, Optional
from utils.logger import get_app_logger

logger = get_app_logger(__name__)


class HTTPClient:
    """Handles HTTP GET and POST requests for BEATRIX."""

    def __init__(self, base_url: str = "", timeout: int = 10):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"GET request failed: {e}")
            raise

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"POST request failed: {e}")
            raise
