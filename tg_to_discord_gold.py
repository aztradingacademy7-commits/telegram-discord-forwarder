import os
import json
import asyncio
import requests
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Încarcă variabilele din .env
load_dotenv("gold.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT")
PERSIST_FILE = os.getenv("PERSIST_FILE", "gold_forwarded.json")

# Inițializează clientul Telegram
client = TelegramClient("gold_session", API_ID, API_HASH)

# Încarcă mesajele deja transmise
if os.path.exists(PERSIST_FILE):
    with open(PERSIST_FILE, "r") as f:
        sent_messages = json.load(f)
else:
    sent_messages = []


# ------------------------------------------------------------
# 🔥 FILTRU SPECIAL PENTRU SEMNALE GOLD / XAUUSD
# ------------------------------------------------------------
def is_gold_signal(text: str) -> bool:
    if not text:
        return False

    text_upper = text.upper()

    # Mesajul trebuie să înceapă cu BUY sau SELL
    if not (text_upper.startswith("BUY") or text_upper.startswith("SELL")):
        return False

    # Trebuie să conțină GOLD sau XAUUSD
    if "GOLD" not in text_upper and "XAUUSD" not in text_upper:
        return False

    # Trebuie să conțină TP-uri
    if "TP" not in text_upper:
        return False

    # Trebuie să conțină SL
    if "SL" not in text_upper:
        return False

    return True


# ------------------------------------------------------------
# 📡 HANDLER – ASCULTĂ MESAJELE ȘI LE FILTREAZĂ
# ------------------------------------------------------------
@client.on(events.NewMessage(chats=TELEGRAM_CHAT))
async def handler(event):
    msg_id = event.id

    if msg_id in sent_messages:
        return  # dacă a fost trimis deja, ignorăm

    text = event.message.message or ""

    # 🔎 APLICĂ FILTRUL GOLD
    if not is_gold_signal(text):
        print("⏭ Mesaj ignorat (nu este semnal GOLD).")
        return

    print(f"➡️ Semnal GOLD detectat: {text[:70]}...")

    # Trimite pe Discord
    await send_to_discord(text)

    # Salvează mesajul ca trimis
    sent_messages.append(msg_id)
    with open(PERSIST_FILE, "w") as f:
        json.dump(sent_messages, f)


# ------------------------------------------------------------
# 🚀 TRIMITEREA CĂTRE DISCORD
# ------------------------------------------------------------
async def send_to_discord(message_text):
    payload = {"content": message_text}

    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        if response.status_code in (200, 204):
            print("✅ Semnal GOLD trimis pe Discord.")
        else:
            print(f"⚠️ Eroare Discord ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Eroare de rețea: {e}")


# ------------------------------------------------------------
# 🔌 PORNIREA BOTULUI
# ------------------------------------------------------------
async def main():
    print("🔹 Conectare la Telegram...")
    await client.start()

    me = await client.get_me()
    print(f"✅ Conectat ca {me.username or me.first_name}")
    print(f"📡 Ascult semnalele din {TELEGRAM_CHAT}...")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
