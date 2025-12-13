import os
from fastapi import FastAPI
from telethon import TelegramClient, events
from parser import parse_signal
from signal_store import save_signal, get_signal

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
SOURCE_CHAT_ID = int(os.getenv("SOURCE_CHAT_ID"))

app = FastAPI()
client = TelegramClient(SESSION, API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def handler(event):
    signal = parse_signal(event.raw_text)
    if signal:
        if save_signal(signal):
            print("✅ Signal saved:", signal)
        else:
            print("⚠️ Duplicate signal ignored")

@app.on_event("startup")
async def start_bot():
    await client.start()
    print("🤖 Telegram connected")

@app.get("/signal/latest")
def latest_signal():
    return get_signal()
