"""
Ochiq Kurs — broadcast script (server-side fallback to the /broadcast command).

The primary way to broadcast is the in-Telegram admin command /broadcast (see
handlers.py). This script does the same thing from the server's shell — handy
for very long messages or automation. The shared sending logic lives in
broadcast_core.py.

Usage (on the server, from ~/opencourse-bot):
    venv/bin/python broadcast.py --dry-run "Xabar matni"
    venv/bin/python broadcast.py "Xabar matni"
    venv/bin/python broadcast.py --html "<b>Qalin</b> matn"
    venv/bin/python broadcast.py --file xabar.txt          # avoids shell quoting
"""

import argparse
import asyncio
import logging
import sys

from telegram import Bot

from broadcast_core import fetch_contacts, run_broadcast
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("broadcast")


async def _main(text: str, dry_run: bool, parse_mode: str | None) -> None:
    if dry_run:
        contacts = await fetch_contacts()
        logger.info("%d recipient(s) — DRY RUN, nothing sent. Preview:\n%s", len(contacts), text)
        return

    bot = Bot(BOT_TOKEN)
    async with bot:
        result = await run_broadcast(bot, text, parse_mode)
    logger.info(
        "Done: sent=%d failed=%d blocked=%d",
        result["sent"], result["failed"], result["blocked"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Broadcast a message to all bot contacts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("message", nargs="?", help="The message text to send.")
    group.add_argument("--file", help="Read the message text from a file (avoids shell quoting).")
    parser.add_argument("--dry-run", action="store_true", help="Show recipient count only.")
    parser.add_argument("--html", action="store_true", help="Render the message as HTML.")
    args = parser.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else args.message
    if not text or not text.strip():
        sys.exit("Refusing to broadcast an empty message.")

    parse_mode = "HTML" if args.html else None
    asyncio.run(_main(text, args.dry_run, parse_mode))


if __name__ == "__main__":
    main()
