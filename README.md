 
# 🧠 BCIPYDUMMIES

**Librería para actuar como middleware entre un EEG Emotiv (from Emotiv) para comunicarse con otros dispositivos.**

_For dummies 4 real_

---

## 🚀 Instalación

```
pip install -e .
```
🧩 Uso básico
```
python -m bcipydummies.cli --source mock --map lift:SPACE
```
📦 Estructura del proyecto
engine.py: motor principal que interpreta las señales EEG.

sources.py: módulo para conectar o simular fuentes EEG (como Emotiv).

publishers.py: envía comandos a otros dispositivos (teclado, consola, red, etc.).

cli.py: interfaz de línea de comandos.

🧰 Requisitos
Python 3.9+

Dependencias en pyproject.toml

🧾 Licencia

Estructura

```
BCIPYDUMMIES/
│
├── __init__.py
├── cortex/
│   ├── __init__.py
│   ├── websocket_client.py     ← conexión y autenticación con Emotiv Cortex API
│   └── session_manager.py      ← manejo de token, sesión y subscripciones
│
├── control/
│   ├── __init__.py
│   ├── window_control.py       ← enviar teclas a la ventana (win32gui, win32con)
│   ├── action_mapper.py        ← lógica de interpretación (left→A, lift→SPACE, etc.)
│
├── core/
│   ├── __init__.py
│   ├── emotiv_controller.py    ← clase principal que usa los módulos anteriores
│
└── cli/
    ├── __init__.py
    └── main.py                 ← interfaz CLI tipo “nbx emotiv --window Mario”
```
