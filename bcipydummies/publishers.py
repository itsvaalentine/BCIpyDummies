from pynput.keyboard import Controller, Key

keyboard = Controller()

def send_to_keyboard(signal: str):
    """
    Mapea nombres de señales a teclas del teclado.
    """
    mapping = {
        "lift": Key.space,
        "left": Key.left,
        "right": Key.right,
        "drop": "s"
    }
    key = mapping.get(signal)
    if key:
        keyboard.press(key)
        keyboard.release(key)
        print(f"🎮 Acción enviada: {signal} → {key}")
    else:
        print(f"⚠️ No hay mapeo para: {signal}")
