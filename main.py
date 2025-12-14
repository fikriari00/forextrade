import os
import re
import asyncio
from fastapi import FastAPI
from telethon import TelegramClient, events
from dotenv import load_dotenv

load_dotenv()

# ================= ENV =================
API_ID   = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION  = "railway_session"

SOURCE_A = int(os.getenv("SOURCE_A"))  # Crypto channel
SOURCE_B = int(os.getenv("SOURCE_B"))  # XAUUSD channel

# ================= APP =================
app = FastAPI()
latest_signal = {}

# ================= TELEGRAM =================
client = TelegramClient(SESSION, API_ID, API_HASH)

# ================= SYMBOL MAP =================
ALLOWED_BASE = ["ADA", "SOL", "LINK", "LTC", "XRP", "DOGE"]

def map_symbol(pair: str):
    pair = pair.upper().strip()
    if "/USDT" in pair:
        base = pair.replace("/USDT", "")
        if base in ALLOWED_BASE:
            return base + "USD"
    return None

# ================= PARSER A =================
def parse_crypto(text: str):
    pair = re.search(r"Pair:\s*([A-Z/]+)", text)
    side = re.search(r"Position:.*(Short|Long)", text, re.I)
    entry = re.search(r"Entry Price:\s*([\d.]+)", text)
    tp = re.search(r"Take Profit:\s*([\d.]+)", text)
    sl = re.search(r"Stop Loss:\s*([\d.]+)", text)

    if not all([pair, side, entry, tp, sl]):
        return None

    symbol = map_symbol(pair.group(1))
    if not symbol:
        return None

    return {
        "id": f"{symbol}_{side.group(1).lower()}_{entry.group(1)}",
        "symbol": symbol,
        "side": side.group(1).lower(),
        "entry_type": "market",
        "entry_price": float(entry.group(1)),
        "stop_loss": float(sl.group(1)),
        "take_profit": [float(tp.group(1))],
        "execute": True,
        "source": "crypto"
    }

# ================= PARSER B =================
def parse_xau(text: str):
    lines = text.lower().splitlines()

    try:
        first = lines[0].split("@")
        symbol = first[0].upper()
        side   = first[1].split()[0]
        entry  = float(first[2])

        sl = float(lines[1].split("@")[1])

        tps = []
        for l in lines:
            if l.startswith("tp"):
                tps.append(float(l.split("@")[1]))

        return {
            "id": f"{symbol}_{side}_{entry}",
            "symbol": symbol,
            "side": side,
            "entry_type": "market",
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tps,
            "execute": True,
            "source": "xau"
        }
    except:
        return None

# ================= TELEGRAM LISTENER =================
@client.on(events.NewMessage)
async def handler(event):
    global latest_signal

    chat_id = event.chat_id
    text = event.raw_text

    signal = None

    if chat_id == SOURCE_A:
        signal = parse_crypto(text)
    elif chat_id == SOURCE_B:
        signal = parse_xau(text)

    if signal:
        latest_signal = signal
        print("✅ SIGNAL SAVED:", signal)

# ================= API =================
@app.get("/signal/latest")
def get_signal():
    return latest_signal or {}

# ================= START =================
@app.on_event("startup")
async def startup():
    asyncio.create_task(client.start())
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
