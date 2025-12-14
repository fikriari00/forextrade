import os
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==================================================
# ENV VARIABLES (WAJIB ADA DI RAILWAY)
# ==================================================
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]

SOURCE_A = int(os.environ["SOURCE_A"])   # Channel crypto
SOURCE_B = int(os.environ["SOURCE_B"])   # Channel XAU

# ==================================================
# TELETHON CLIENT
# ==================================================
client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

latest_signal = {}

# ==================================================
# SYMBOL MAP
# ==================================================
PAIR_MAP = {
    "ADA": "ADAUSD",
    "SOL": "SOLUSD",
    "LINK": "LINKUSD",
    "LTC": "LTCUSD",
    "XRP": "XRPUSD"
}

# ==================================================
# PARSER CRYPTO (FORMAT A)
# ==================================================
def parse_crypto(text: str):
    try:
        pair = re.search(r"Pair:\s*([A-Z]+)/USDT", text)
        side = re.search(r"Position:.*(Short|Long)", text, re.I)
        entry = re.search(r"Entry Price:\s*([\d.]+)", text)
        tp = re.search(r"Take Profit:\s*([\d.]+)", text)
        sl = re.search(r"Stop Loss:\s*([\d.]+)", text)

        if not all([pair, side, entry, tp, sl]):
            return None

        base = pair.group(1)
        if base not in PAIR_MAP:
            return None

        return {
            "id": f"{PAIR_MAP[base]}_{side.group(1).lower()}_{entry.group(1)}",
            "symbol": PAIR_MAP[base],
            "side": side.group(1).lower(),
            "entry_price": float(entry.group(1)),
            "stop_loss": float(sl.group(1)),
            "take_profit": [float(tp.group(1))],
            "execute": True,
            "source": "crypto"
        }
    except:
        return None

# ==================================================
# PARSER XAU (FORMAT B)
# ==================================================
def parse_xau(text: str):
    try:
        lines = text.lower().splitlines()

        first = lines[0].split("@")
        symbol = first[0].upper()
        side = first[1].split()[0]
        entry = float(first[2])

        sl = float(lines[1].split("@")[1])

        tps = []
        for l in lines:
            if l.startswith("tp"):
                tps.append(float(l.split("@")[1]))

        return {
            "id": f"{symbol}_{side}_{entry}",
            "symbol": symbol,
            "side": side,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tps,
            "execute": True,
            "source": "xau"
        }
    except:
        return None

# ==================================================
# TELEGRAM LISTENER
# ==================================================
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

# ==================================================
# FASTAPI LIFESPAN (ANTI STUCK)
# ==================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.connect()
    print("✅ Telegram connected")
    yield
    await client.disconnect()

app = FastAPI(lifespan=lifespan)

# ==================================================
# API ENDPOINT
# ==================================================
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/signal/latest")
def get_signal():
    return latest_signal or {}

# ==================================================
# START SERVER (WAJIB UNTUK RAILWAY)
# ==================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
