import re
from datetime import datetime

def parse_signal(text: str):
    text = text.lower()

    # --- Pair ---
    pair_match = re.search(r'(xauusd|[a-z]{3,10}usdt)', text)
    if not pair_match:
        return None
    symbol = pair_match.group(1).upper()

    # --- Side ---
    side = "buy" if "buy" in text else "sell" if "sell" in text else None
    if not side:
        return None

    # --- Entry ---
    entry_price = None
    entry_type = "market"
    entry_match = re.search(r'@(\d+\.?\d*)', text)
    if entry_match:
        entry_price = float(entry_match.group(1))

    # --- Stop Loss ---
    sl_match = re.search(r'sl@(\d+\.?\d*)', text)
    if not sl_match:
        return None
    stop_loss = float(sl_match.group(1))

    # --- Take Profits ---
    tps = re.findall(r'tp\d*@?(\d+\.?\d*)', text)
    take_profit = [float(tp) for tp in tps]

    # --- Build JSON ---
    signal = {
        "id": f"{symbol}_{side}_{entry_price or 'mkt'}",
        "symbol": symbol,
        "side": side,
        "entry_type": entry_type,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "execute": True,
        "timestamp": datetime.now().isoformat(),
        "source": "telegram"
    }

    return signal
