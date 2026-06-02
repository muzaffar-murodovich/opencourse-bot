import logging

import httpx

from config import BOT_SECRET, DJANGO_API_URL, DJANGO_ISSUE_CODE_URL

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
    Send auth confirmation to Django backend (bot-link flow).

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


async def issue_code(
    telegram_id: int,
    first_name: str,
    last_name: str,
    username: str,
    photo_url: str,
) -> tuple[int, str | None]:
    """
    Ask Django to mint a 6-digit login code for this Telegram user.

    Django pre-confirms a token tied to the user; the user then types the
    returned code on the website to sign in.

    Returns (status_code, short_code):
      - (200, code) on success.
      - (403, None) when the bot secret is rejected (logged as an error).
      - (other, None) on Django error.
      - (0, None) on network/unexpected error.
    """
    payload = {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "photo_url": photo_url,
    }
    headers = {"X-Bot-Secret": BOT_SECRET}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                DJANGO_ISSUE_CODE_URL, json=payload, headers=headers
            )
            logger.debug(
                "Django issue-code response: %s %s",
                response.status_code,
                response.text,
            )
            if response.status_code == 200:
                return 200, response.json().get("short_code")
            if response.status_code == 403:
                logger.error("Bot secret rejected by issue-code endpoint")
            return response.status_code, None
    except httpx.RequestError as exc:
        logger.error("Network error while contacting Django: %s", exc)
        return 0, None
    except Exception as exc:
        logger.error("Unexpected error in issue_code: %s", exc)
        return 0, None
