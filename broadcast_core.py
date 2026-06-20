"""
Shared broadcast logic used by both the broadcast.py script and the
/broadcast admin command in handlers.py.

Respects Telegram's broadcast limits
(https://core.telegram.org/bots/faq#broadcasting): ~30 messages/second to
different users — we throttle under that and honour retry_after on a 429.
"""

import asyncio
import logging

import httpx
from telegram import Bot
from telegram.error import Forbidden, RetryAfter, TelegramError

from config import BOT_SECRET, DJANGO_CONTACTS_URL, DJANGO_MARK_BLOCKED_URL

logger = logging.getLogger("broadcast")

# Stay safely under Telegram's ~30 msg/s bulk cap for different users.
MESSAGES_PER_SECOND = 25
SEND_DELAY_SECONDS = 1.0 / MESSAGES_PER_SECOND


def _is_blocked(exc: Exception) -> bool:
    """True if the error means the user has blocked / deleted the bot."""
    return isinstance(exc, Forbidden)


async def fetch_contacts() -> list[dict]:
    """Fetch the broadcast list (non-blocked contacts with a chat_id) from Django."""
    headers = {"X-Bot-Secret": BOT_SECRET}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(DJANGO_CONTACTS_URL, headers=headers)
        resp.raise_for_status()
        return resp.json().get("contacts", [])


async def mark_blocked(telegram_ids: list[int]) -> None:
    """Tell Django which users blocked the bot, so later broadcasts skip them."""
    if not telegram_ids:
        return
    headers = {"X-Bot-Secret": BOT_SECRET}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                DJANGO_MARK_BLOCKED_URL,
                json={"telegram_ids": telegram_ids},
                headers=headers,
            )
    except httpx.RequestError as exc:
        logger.warning("Could not report blocked users to Django: %s", exc)


async def _send_one(bot: Bot, chat_id: int, text: str, parse_mode: str | None) -> None:
    """Send a single message, retrying once if Telegram returns a 429."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except RetryAfter as exc:
        logger.info("Rate limited; sleeping %ss", exc.retry_after)
        await asyncio.sleep(exc.retry_after + 1)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


async def run_broadcast(
    bot: Bot,
    text: str,
    parse_mode: str | None = None,
    contacts: list[dict] | None = None,
) -> dict:
    """
    Send `text` to every contact, throttled. Returns counts dict
    {'sent', 'failed', 'blocked', 'total'}.

    The caller supplies an initialised Bot (the script makes its own; the
    /broadcast command passes context.bot) and manages its lifecycle. If
    `contacts` is None it is fetched.
    """
    if contacts is None:
        contacts = await fetch_contacts()

    sent = failed = 0
    blocked: list[int] = []
    for contact in contacts:
        chat_id = contact.get("chat_id")
        if not chat_id:
            continue
        try:
            await _send_one(bot, chat_id, text, parse_mode)
            sent += 1
        except Exception as exc:  # one bad recipient must not stop the whole run
            failed += 1
            if _is_blocked(exc):
                blocked.append(contact["telegram_id"])
            elif not isinstance(exc, TelegramError):
                logger.warning("Unexpected error for %s: %s", chat_id, exc)
        await asyncio.sleep(SEND_DELAY_SECONDS)

    await mark_blocked(blocked)
    return {"sent": sent, "failed": failed, "blocked": len(blocked), "total": len(contacts)}
