from bcipydummies.engine import ThresholdEngine

def test_engine_activation():
    engine = ThresholdEngine(on_confidence=0.8)
    events = [
        {"ts": 1, "signal": "lift", "score": 0.2},
        {"ts": 2, "signal": "lift", "score": 0.8},
        {"ts": 3, "signal": "lift", "score": 0.9},
    ]
    for e in events:
        engine.accept_event(e)
    assert "lift" in engine.mu
