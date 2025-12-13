import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from parser import parse_signal
from signal_store import save_signal, get_signal

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
SOURCE_CHAT_ID = int(os.getenv("SOURCE_CHAT_ID"))

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)

@client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def handler(event):
    signal = parse_signal(event.raw_text)
    if signal and save_signal(signal):
        print("✅ Signal saved:", signal["id"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🤖 Connecting to Telegram...")
    await client.start()
    print("✅ Telegram connected")

    task = asyncio.create_task(client.run_until_disconnected())
    yield

    print("🛑 Shutting down Telegram client")
    client.disconnect()
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/signal/latest")
def latest_signal():
    return get_signal()
