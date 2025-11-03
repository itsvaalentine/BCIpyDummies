 
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