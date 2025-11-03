import random
import time

def mock_source(signals=("lift", "drop", "left", "right")):
    """
    Genera señales aleatorias (simulación de EEG).
    """
    while True:
        time.sleep(1)
        signal = random.choice(signals)
        score = random.random()
        yield {"ts": time.time(), "signal": signal, "score": score}
