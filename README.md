# Ochiq Kurs — Telegram Authentication Bot

Foydalanuvchilarni `ochiqkurs.uz` saytiga Telegram orqali kiritadigan bot.
`python-telegram-bot` ustida, **polling** rejimida ishlaydi.

## Kirish oqimlari

Botda ikkita kirish usuli bor:

1. **`/start <token>`** — sayt Telegramni deep-link orqali ochadi
   (foydalanuvchi qurilmasida Telegram bo'lishi shart). Bot
   `/api/auth/confirm/` endpoint'ini chaqirib sessiyani tasdiqlaydi.
2. **`/login`** — foydalanuvchi **boshqa qurilmadan** (masalan, kompyuter
   brauzerida) kirayotganda Telegramdan kod oladi. Bot
   `/api/auth/issue-code/` endpoint'iga foydalanuvchining Telegram
   identifikatorini yuboradi, javobda 6 raqamli kod oladi va uni
   foydalanuvchiga jo'natadi (masalan, `123 456`). Foydalanuvchi
   kodni saytdagi kirish sahifasiga kiritib tizimga kiradi. Kod 10 daqiqa
   amal qiladi va bir martagina ishlatish mumkin.

## Sozlash

`.env` faylini `.env.example` asosida yarating:

| O'zgaruvchi | Tavsif |
|-------------|--------|
| `BOT_TOKEN` | BotFather'dan olingan bot token |
| `BOT_SECRET` | Django bilan baham ko'rilgan maxfiy kalit (`X-Bot-Secret`) |
| `DJANGO_API_URL` | Auth tasdiqlash endpoint (`/api/auth/confirm/`) |
| `DJANGO_ISSUE_CODE_URL` | Kod chiqarish endpoint (`/api/auth/issue-code/`) |
| `DJANGO_BOT_START_URL` | `/start` telemetriya endpoint (`/api/telemetry/bot-start/`) |
| `DJANGO_CONTACTS_URL` | Broadcast ro'yxati endpoint (`/api/telemetry/contacts/`) |
| `DJANGO_MARK_BLOCKED_URL` | Bloklaganlarni belgilash endpoint (`/api/telemetry/mark-blocked/`) |
| `DEBUG` | `True` bo'lsa batafsil log |

## BotFather command list

Botning buyruq menyusini sozlash uchun BotFather'da `/setcommands` yuboring va
quyidagini joylashtiring:

```
start - Tizimga kirish (sayt orqali)
login - Saytga kirish uchun kod olish
help - Yordam
```

Bu bir martalik qo'lda sozlash bosqichi — kodga taalluqli emas.

## Ishga tushirish

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python bot.py
```

## Testlar va lint

```bash
venv/bin/pip install ruff pytest
ruff check .
pytest -q
```

Bular CI'da (har push va PR'da) avtomatik ishlaydi — pastga qarang.

## Broadcast (e'lon yuborish)

`/start` bosgan barcha foydalanuvchilarga (TelegramContact ro'yxati) bir martalik
xabar yuborish uchun **serverda qo'lda** ishlatiladigan skript — CI deploy
qismi emas, ataylab alohida (e'lon hammaga ketadi va qaytarib bo'lmaydi).

```bash
cd ~/opencourse-bot
# Avval nechta odamga ketishini ko'ring (hech narsa yuborilmaydi):
venv/bin/python broadcast.py --dry-run "Yangi kurs chiqdi! ochiqkurs.uz"
# Haqiqiy yuborish:
venv/bin/python broadcast.py "Yangi kurs chiqdi! ochiqkurs.uz"
# HTML formatlash bilan:
venv/bin/python broadcast.py --html "<b>Yangilik!</b> ochiqkurs.uz"
```

Skript Telegram cheklovlariga amal qiladi (~25 xabar/sek, `429` bo'lsa
`retry_after`ni kutadi), botni bloklagan foydalanuvchilarni Django'da
`blocked=True` qilib belgilaydi (keyingi broadcast'lar ularni o'tkazib yuboradi),
va oxirida `sent / failed / blocked` hisobotini chiqaradi. Skript polling
servisidan mustaqil ishlaydi — bot ishlab turganda ham xavfsiz.

## Deployment

Polling rejimida, systemd unit orqali ishlaydi (`telegram-bot-ochiqkurs`).
To'liq systemd unit namunasi `bot.py` faylining boshidagi izohda keltirilgan.

### CI/CD (GitHub Actions)

`.github/workflows/deploy.yml` ikki bosqichdan iborat:

1. **test** (har push va PR'da) — `ruff` lint, smoke import va `pytest`.
2. **deploy** (faqat `master` ga push'da, `test` muvaffaqiyatli o'tsagina) —
   serverga SSH orqali kiradi (`~/opencourse-bot`), `git reset --hard
   origin/master` qiladi, `requirements.txt` ni o'rnatadi,
   `telegram-bot-ochiqkurs` unitini qayta ishga tushiradi va botning `active`
   ekanini tekshiradi (polling rejimida HTTP yo'qligi uchun `systemctl
   is-active` orqali — crash-on-boot'ni ushlaydi).

Repo'da quyidagi **Actions secrets** sozlangan bo'lishi shart:

| Secret | Tavsif |
|--------|--------|
| `SERVER_IP` | Server IP manzili |
| `SERVER_USER` | SSH foydalanuvchisi (`deploy`) |
| `SSH_PRIVATE_KEY` | Serverga kirish uchun SSH maxfiy kaliti |

Deploy `deploy` foydalanuvchisining `NOPASSWD` sudo ruxsatiga tayanadi:
`systemctl restart/status telegram-bot-ochiqkurs`.
