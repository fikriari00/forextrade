LATEST_SIGNAL = {}
USED_IDS = set()

def save_signal(signal):
    global LATEST_SIGNAL
    if signal["id"] in USED_IDS:
        return False
    USED_IDS.add(signal["id"])
    LATEST_SIGNAL = signal
    return True

def get_signal():
    return LATEST_SIGNAL
