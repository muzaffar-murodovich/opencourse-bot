import logging

import httpx

from config import BOT_SECRET, DJANGO_API_URL

logger = logging.getLogger(__name__)


async def confirm_auth(
    token: str,
    telegram_id: int,
    first_name: str,
    last_name: str,
    username: str,
    photo_url: str,
) -> int:
    """
    Send auth confirmation to Django backend.

    Returns the HTTP status code, or 0 on network/unexpected error.
    """
    payload = {
        "token": token,
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "photo_url": photo_url,
    }
    headers = {"X-Bot-Secret": BOT_SECRET}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(DJANGO_API_URL, json=payload, headers=headers)
            logger.debug("Django response: %s %s", response.status_code, response.text)
            return response.status_code
    except httpx.RequestError as exc:
        logger.error("Network error while contacting Django: %s", exc)
        return 0
    except Exception as exc:
        logger.error("Unexpected error in confirm_auth: %s", exc)
        return 0
