import logging

from telegram import Update
from telegram.ext import ContextTypes

from api import confirm_auth, issue_code

logger = logging.getLogger(__name__)

MSG_START_NO_TOKEN = (
    "Salom! Ochiq Kurs platformasiga xush kelibsiz.\n\n"
    "Saytga kirish uchun /login buyrug'ini yuboring — "
    "men sizga 6 ta raqamli kod beraman. Kodni saytga kiriting."
)
MSG_SUCCESS = "✅ Tizimga muvaffaqiyatli kirdingiz. Saytga qaytishingiz mumkin."
MSG_INVALID = (
    "❌ Havola yaroqsiz yoki muddati o'tgan. "
    "Saytdan qaytadan urinib ko'ring."
)
MSG_ERROR = "⚠️ Xatolik yuz berdi. Bir ozdan keyin qaytadan urinib ko'ring."
MSG_OTHER = (
    "Saytga kirish uchun /login buyrug'ini yuboring — "
    "men sizga 6 ta raqamli kod beraman."
)


async def _get_photo_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return the first profile photo URL, or empty string if unavailable."""
    try:
        user = update.effective_user
        if not user:
            return ""
        photos = await user.get_profile_photos(limit=1)
        if not photos.photos:
            return ""
        file_id = photos.photos[0][-1].file_id  # highest resolution
        file = await context.bot.get_file(file_id)
        return file.file_path if file.file_path.startswith("http") else ""
    except Exception as exc:
        logger.warning("Could not fetch profile photo: %s", exc)
        return ""


async def _confirm_and_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE, token: str
) -> None:
    """Confirm a deep-link token with Django and reply based on the result."""
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


def _format_code(code: str) -> str:
    """Render `123456` as `123 456` for readability."""
    return f"{code[:3]} {code[3:]}" if len(code) == 6 else code


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start [token]. With a token, run the deep-link confirm flow."""
    try:
        args = context.args
        if not args:
            await update.message.reply_text(MSG_START_NO_TOKEN)
            return

        await _confirm_and_reply(update, context, args[0])

    except Exception as exc:
        logger.error("Unhandled error in /start handler: %s", exc)
        await update.message.reply_text(MSG_ERROR)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /login — issue a 6-digit login code for the user to type on the website."""
    try:
        user = update.effective_user
        photo_url = await _get_photo_url(update, context)
        status, code = await issue_code(
            telegram_id=user.id,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            username=user.username or "",
            photo_url=photo_url,
        )
        if status == 200 and code:
            pretty = _format_code(code)
            await update.message.reply_text(
                f"Sizning kirish kodingiz:\n\n<code>{pretty}</code>\n\n"
                "Bu kodni ochiqkurs.uz saytidagi kirish sahifasiga kiriting. "
                "Kod 10 daqiqa ichida amal qiladi.",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(MSG_ERROR)

    except Exception as exc:
        logger.error("Unhandled error in /login handler: %s", exc)
        await update.message.reply_text(MSG_ERROR)


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any non-command message."""
    try:
        if not update.message:
            return
        await update.message.reply_text(MSG_OTHER)
    except Exception as exc:
        logger.error("Unhandled error in fallback handler: %s", exc)
