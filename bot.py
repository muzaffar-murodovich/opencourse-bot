"""
Ochiq Kurs Telegram Authentication Bot
=======================================

Deployment notes:
  - Run mode      : polling (not webhook)
  - Systemd unit  : telegram-bot-ochiqkurs
  - Working dir   : /home/deploy/opencourse-bot/
  - Python venv   : /home/deploy/opencourse-bot/venv/

Systemd service example (/etc/systemd/system/telegram-bot-ochiqkurs.service):
  [Unit]
  Description=Ochiq Kurs Telegram Bot
  After=network.target

  [Service]
  User=deploy
  WorkingDirectory=/home/deploy/opencourse-bot
  ExecStart=/home/deploy/opencourse-bot/venv/bin/python bot.py
  Restart=always
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
"""

import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, DEBUG
from handlers import fallback, help_command, login_command, start

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Ochiq Kurs bot (debug=%s)", DEBUG)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    logger.info("Polling started. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
