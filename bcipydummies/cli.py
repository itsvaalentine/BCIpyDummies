import argparse
from bcipydummies.sources import mock_source
from bcipydummies.engine import ThresholdEngine
from bcipydummies.publishers import send_to_keyboard

def main():
    parser = argparse.ArgumentParser(description="BCIPYDUMMIES CLI")
    parser.add_argument("--source", default="mock", help="Fuente de datos (mock o real)")
    parser.add_argument("--map", default="lift:SPACE", help="Mapeo de señales a teclas")
    parser.add_argument("--confidence", type=float, default=0.8, help="Umbral de confianza")
    args = parser.parse_args()

    print("🧠 Iniciando BCIPYDUMMIES...")
    print(f"📡 Fuente: {args.source}")
    print(f"🎚️ Umbral de confianza: {args.confidence}")
    print("🎮 Presiona Ctrl+C para salir\n")

    engine = ThresholdEngine(on_confidence=args.confidence)

    try:
        for event in mock_source():
            engine.accept_event(event)
            for signal in engine.mu:
                send_to_keyboard(signal)
    except KeyboardInterrupt:
        print("\n🧩 Finalizado.")
