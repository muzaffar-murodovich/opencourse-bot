import os

# config.py reads BOT_TOKEN / BOT_SECRET with no default and raises if missing,
# so set dummy values before any module that imports config gets loaded.
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("BOT_SECRET", "test-secret")
