from decouple import config

BOT_TOKEN: str = config("BOT_TOKEN")
DJANGO_API_URL: str = config("DJANGO_API_URL", default="https://ochiqkurs.uz/api/auth/confirm/")
DJANGO_ISSUE_CODE_URL: str = config(
    "DJANGO_ISSUE_CODE_URL",
    default="https://ochiqkurs.uz/api/auth/issue-code/",
)
BOT_SECRET: str = config("BOT_SECRET")
DEBUG: bool = config("DEBUG", default=False, cast=bool)
