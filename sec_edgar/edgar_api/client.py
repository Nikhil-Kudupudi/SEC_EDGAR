"""HTTP access to SEC EDGAR. Every SEC call goes through get_json()."""
import requests

from sec_edgar.config import settings
from sec_edgar.utils.logger import logger


def get_json(url: str) -> dict:
    logger.info(f"GET {url}")
    response = requests.get(url, headers={"User-Agent": settings.sec_user_agent}, timeout=30)
    response.raise_for_status()
    return response.json()
