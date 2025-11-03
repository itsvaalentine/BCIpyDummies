 
class ThresholdEngine:
    """
    Motor simple que activa señales cuando superan un umbral de confianza.
    """

    def __init__(self, on_confidence=0.8):
        self.on_confidence = on_confidence
        self.mu = {}  # historial de señales activadas

    def accept_event(self, event: dict):
        """
        Acepta un evento con formato:
        {"ts": timestamp, "signal": "nombre", "score": valor entre 0 y 1}
        """
        signal = event.get("signal")
        score = event.get("score", 0)
        if score >= self.on_confidence:
            self.mu[signal] = self.mu.get(signal, 0) + 1
            print(f"✅ Activación detectada: {signal} (score={score:.2f})")
        else:
            print(f"⚪ Ignorado: {signal} (score={score:.2f})")
