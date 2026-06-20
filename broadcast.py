"""
Ochiq Kurs — broadcast script (run manually on the server, NOT via CI).

Sends a one-off message to everyone who has pressed /start on the bot
(the TelegramContact list, fetched from Django). Deliberately a standalone
script rather than a bot command: a broadcast reaches everyone and can't be
undone, so it should take a conscious `python broadcast.py ...` invocation,
ideally previewed with --dry-run first.

Respects Telegram's limits (https://core.telegram.org/bots/faq#broadcasting):
~30 messages/second to different users — we throttle under that, and on a 429
we honour the server's retry_after. Users who have blocked the bot are reported
back to Django (mark-blocked) so future broadcasts skip them.

Usage (on the server, from ~/opencourse-bot):
    venv/bin/python broadcast.py --dry-run "Xabar matni"
    venv/bin/python broadcast.py "Xabar matni"
    venv/bin/python broadcast.py --html "<b>Qalin</b> matn"
"""

import argparse
import asyncio
import logging
import sys

import httpx
from telegram import Bot
from telegram.error import Forbidden, RetryAfter, TelegramError

from config import (
    BOT_SECRET,
    BOT_TOKEN,
    DJANGO_CONTACTS_URL,
    DJANGO_MARK_BLOCKED_URL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("broadcast")

# Stay safely under Telegram's ~30 msg/s bulk cap for different users.
MESSAGES_PER_SECOND = 25
SEND_DELAY_SECONDS = 1.0 / MESSAGES_PER_SECOND


def _is_blocked(exc: Exception) -> bool:
    """True if the error means the user has blocked / deleted the bot."""
    return isinstance(exc, Forbidden)


async def _fetch_contacts() -> list[dict]:
    headers = {"X-Bot-Secret": BOT_SECRET}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(DJANGO_CONTACTS_URL, headers=headers)
        resp.raise_for_status()
        return resp.json().get("contacts", [])


async def _mark_blocked(telegram_ids: list[int]) -> None:
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


async def broadcast(text: str, dry_run: bool, parse_mode: str | None) -> None:
    contacts = await _fetch_contacts()
    logger.info("%d recipient(s)", len(contacts))
    if dry_run:
        logger.info("DRY RUN — no messages sent. Preview:\n%s", text)
        return

    bot = Bot(BOT_TOKEN)
    sent = failed = 0
    blocked: list[int] = []
    async with bot:
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

    await _mark_blocked(blocked)
    logger.info("Done: sent=%d failed=%d blocked=%d", sent, failed, len(blocked))


def main() -> None:
    parser = argparse.ArgumentParser(description="Broadcast a message to all bot contacts.")
    parser.add_argument("message", help="The message text to send.")
    parser.add_argument("--dry-run", action="store_true", help="Show recipient count only.")
    parser.add_argument("--html", action="store_true", help="Render the message as HTML.")
    args = parser.parse_args()

    if not args.message.strip():
        sys.exit("Refusing to broadcast an empty message.")

    parse_mode = "HTML" if args.html else None
    asyncio.run(broadcast(args.message, args.dry_run, parse_mode))


if __name__ == "__main__":
    main()
