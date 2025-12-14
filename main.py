
import os
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ======================================================
# ENV
# ======================================================
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]

SOURCE_A = int(os.environ["SOURCE_A"])  # Crypto
SOURCE_B = int(os.environ["SOURCE_B"])  # XAUUSD

# ======================================================
# TELEGRAM CLIENT
# ======================================================
client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

latest_signal = {}

# ======================================================
# SYMBOL MAP
# ======================================================
ALLOWED_BASE = ["ADA", "SOL", "LINK", "LTC", "XRP", "DOGE"]

def map_symbol(pair: str):
    pair = pair.upper().strip()
    if pair.endswith("/USDT"):
        base = pair.replace("/USDT", "")
        if base in ALLOWED_BASE:
            return base + "USD"
    return None

# ======================================================
# PARSER CRYPTO
# ======================================================
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

# ======================================================
# PARSER XAUUSD
# ======================================================
def parse_xau(text: str):
    try:
        lines = text.lower().splitlines()
        first = lines[0].split()

        symbol = first[0].upper()      # XAUUSD
        side = first[1]               # sell / buy
        entry = float(first[-1].split("@")[1])

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

# ======================================================
# TELEGRAM LISTENER
# ======================================================
@client.on(events.NewMessage)
async def handler(event):
    global latest_signal

    if event.chat_id == SOURCE_A:
        signal = parse_crypto(event.raw_text)
    elif event.chat_id == SOURCE_B:
        signal = parse_xau(event.raw_text)
    else:
        return

    if signal:
        latest_signal = signal
        print("✅ SIGNAL SAVED:", signal)

# ======================================================
# FASTAPI LIFESPAN (BENAR)
# ======================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.start()
    yield
    await client.disconnect()

app = FastAPI(lifespan=lifespan)

# ======================================================
# API
# ======================================================
@app.get("/signal/latest")
def get_signal():
    return latest_signal or {}

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
