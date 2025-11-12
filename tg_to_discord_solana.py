import os
import json
import asyncio
import requests
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Încarcă variabilele din .env
load_dotenv("memecoin.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT")
FORWARD_FILTER = os.getenv("FORWARD_FILTER", "all")
PERSIST_FILE = os.getenv("PERSIST_FILE", "forwarded.json")

# Inițializează clientul Telegram
client = TelegramClient("session", API_ID, API_HASH)

# Încarcă mesajele deja transmise (ca să nu le retrimită)
if os.path.exists(PERSIST_FILE):
    with open(PERSIST_FILE, "r") as f:
        sent_messages = json.load(f)
else:
    sent_messages = []

async def send_to_discord(message_text):
    """Trimite mesajul către Discord prin webhook."""
    payload = {"content": message_text}
    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        if response.status_code == 204:
            print("✅ Mesaj trimis pe Discord.")
        else:
            print(f"⚠️ Eroare la trimitere ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Eroare de rețea: {e}")

@client.on(events.NewMessage(chats=TELEGRAM_CHAT))
async def handler(event):
    """Când apare un mesaj nou în canalul Telegram."""
    msg_id = event.id
    if msg_id in sent_messages:
        return  # deja trimis

    text = event.message.message or ""

    if FORWARD_FILTER == "text" and not text:
        return
    if FORWARD_FILTER == "media" and not event.message.media:
        return

    # Creează textul de trimis
    if text:
        to_send = text
    else:
        to_send = "[Media / fișier primit]"

    print(f"➡️ {to_send[:60]}...")
    await send_to_discord(to_send)

    # Salvează ID-ul mesajului trimis
    sent_messages.append(msg_id)
    with open(PERSIST_FILE, "w") as f:
        json.dump(sent_messages, f)

async def main():
    print("🔹 Conectare la Telegram...")
    await client.start()
    me = await client.get_me()
    print(f"✅ Conectat ca {me.username or me.first_name}")
    print(f"📡 Ascult mesajele din {TELEGRAM_CHAT}...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
