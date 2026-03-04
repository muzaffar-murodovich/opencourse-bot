import logging

from telegram import Update
from telegram.ext import ContextTypes

from api import confirm_auth
from config import BOT_TOKEN

logger = logging.getLogger(__name__)

MSG_NO_TOKEN = (
    "Salom! Ochiq Kurs platformasiga xush kelibsiz. "
    "Kirish uchun ochiqkurs.uz saytiga o'ting."
)
MSG_SUCCESS = "✅ Tizimga muvaffaqiyatli kirdingiz. Saytga qaytingiz mumkin."
MSG_INVALID = (
    "❌ Havola yaroqsiz yoki muddati o'tgan. "
    "Saytdan qaytadan urinib ko'ring."
)
MSG_ERROR = "⚠️ Xatolik yuz berdi. Bir ozdan keyin qaytadan urinib ko'ring."
MSG_OTHER = (
    "Kirish uchun ochiqkurs.uz saytiga o'ting "
    "Telegram orqali tasdiqlash tugmasini bosing."
)


async def _get_photo_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return the first profile photo URL, or empty string if unavailable."""
    try:
        user = update.effective_user
        photos = await user.get_profile_photos(limit=1)
        if not photos.photos:
            return ""
        file_id = photos.photos[0][-1].file_id  # highest resolution
        file = await context.bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    except Exception as exc:
        logger.warning("Could not fetch profile photo: %s", exc)
        return ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start [token]."""
    try:
        args = context.args
        if not args:
            await update.message.reply_text(MSG_NO_TOKEN)
            return

        token = args[0]
        user = update.effective_user

        photo_url = await _get_photo_url(update, context)

        status = await confirm_auth(
            token=token,
            telegram_id=user.id,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            username=user.username or "",
            photo_url=photo_url,
        )

        if status == 200:
            await update.message.reply_text(MSG_SUCCESS)
        elif status == 400:
            await update.message.reply_text(MSG_INVALID)
        else:
            await update.message.reply_text(MSG_ERROR)

    except Exception as exc:
        logger.error("Unhandled error in /start handler: %s", exc)
        await update.message.reply_text(MSG_ERROR)


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any non-command message."""
    try:
        await update.message.reply_text(MSG_OTHER)
    except Exception as exc:
        logger.error("Unhandled error in fallback handler: %s", exc)
