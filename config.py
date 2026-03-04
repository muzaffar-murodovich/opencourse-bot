from decouple import config

BOT_TOKEN: str = config("BOT_TOKEN")
DJANGO_API_URL: str = config("DJANGO_API_URL", default="https://ochiqkurs.uz/api/auth/confirm/")
BOT_SECRET: str = config("BOT_SECRET")
DEBUG: bool = config("DEBUG", default=False, cast=bool)
