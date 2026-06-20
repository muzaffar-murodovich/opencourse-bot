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

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS, BOT_TOKEN, DEBUG
from handlers import (
    BC_AWAIT_MESSAGE,
    BC_CONFIRM,
    broadcast_cancel,
    broadcast_confirm,
    broadcast_receive,
    broadcast_start,
    fallback,
    help_command,
    login_command,
    start,
)

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Ochiq Kurs bot (debug=%s)", DEBUG)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /broadcast — admin only. The User filter on the entry point means a
    # non-admin's /broadcast simply doesn't start the conversation. With an
    # empty ADMIN_IDS the filter matches nobody, so broadcast stays disabled.
    admin_filter = filters.User(user_id=ADMIN_IDS)
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start, filters=admin_filter)],
        states={
            BC_AWAIT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, broadcast_receive),
            ],
            BC_CONFIRM: [
                CallbackQueryHandler(broadcast_confirm, pattern="^bc_confirm$"),
                CallbackQueryHandler(broadcast_cancel, pattern="^bc_cancel$"),
            ],
        },
        fallbacks=[CommandHandler("bekor", broadcast_cancel)],
    )

    # Register the conversation before the catch-all fallback so it gets first
    # dibs on the admin's messages while a broadcast is being composed.
    app.add_handler(broadcast_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    logger.info("Polling started. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
