from decouple import config

BOT_TOKEN: str = config("BOT_TOKEN")
DJANGO_API_URL: str = config("DJANGO_API_URL", default="https://ochiqkurs.uz/api/auth/confirm/")
DJANGO_ISSUE_CODE_URL: str = config(
    "DJANGO_ISSUE_CODE_URL",
    default="https://ochiqkurs.uz/api/auth/issue-code/",
)
DJANGO_BOT_START_URL: str = config(
    "DJANGO_BOT_START_URL",
    default="https://ochiqkurs.uz/api/telemetry/bot-start/",
)
BOT_SECRET: str = config("BOT_SECRET")
DEBUG: bool = config("DEBUG", default=False, cast=bool)
