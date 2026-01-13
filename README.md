```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ____   ____ ___            ____                            _           ║
║  | __ ) / ___|_ _|_ __  _   |  _ \ _   _ _ __ ___  _ __ ___ (_) ___  ___ ║
║  |  _ \| |    | || '_ \| | | | | | | | | '_ ` _ \| '_ ` _ \| |/ _ \/ __|║
║  | |_) | |___ | || |_) | |_| | |_| | |_| | | | | | | | | | | |  __/\__ \║
║  |____/ \____|___| .__/ \__, |____/ \__,_|_| |_| |_|_| |_| |_|\___||___/║
║                  |_|    |___/                                            ║
║                                                                          ║
║                       **For dummies 4 real**                             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)

---

**Middleware para conectar headsets EEG Emotiv con aplicaciones de Windows mediante comandos mentales.**

BCIpyDummies actúa como traductor entre tu cerebro y tu computadora.  Captura comandos mentales desde tu headset Emotiv y los convierte en pulsaciones de teclado para controlar cualquier aplicación de Windows.

---

## 🎯 Casos de Uso

- 🎮 Controla videojuegos con tu mente
- 🖥️ Control de aplicaciones manos libres
- 🔬 Investigación y experimentación BCI
- ♿ Soluciones de accesibilidad

---

## 🏗️ Arquitectura de Alto Nivel

```
┌───────────────────────────────���─────────────────────────────────────────────┐
│                          BCIPipeline (Orquestador)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │    SOURCES     │───▶│   PROCESSORS     │───▶│     PUBLISHERS         │  │
│  │   (Entrada)    │    │ (Procesamiento)  │    │      (Salida)          │  │
│  └────────────────┘    └──────────────────┘    └────────────────────────┘  │
│                                                                             │
│  • EmotivSource        • ThresholdProcessor    • KeyboardPublisher         │
│  • MockSource          • DebounceProcessor     • ConsolePublisher          │
│                        • CommandMapper                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

📖 **[Ver Arquitectura Completa →](ARQUITECTURA_COMPLETA.md)**

---

## 📋 Requisitos

| Requisito | Versión |
|-----------|---------|
| Sistema Operativo | Windows 10/11 |
| Python | 3.9+ |
| Hardware | Headset Emotiv EEG (EPOC X, EPOC+, Insight, Flex) |
| Software | [Emotiv Cortex](https://www.emotiv.com/emotiv-cortex/) |

---

## 🚀 Inicio Rápido

```bash
pip install bcipydummies
```

```python
from bcipydummies.emotiv_controller import EmotivController

# Listar ventanas disponibles
windows = EmotivController.list_windows()
print(windows)

# Conectar y controlar una aplicación
controller = EmotivController("Tu Ventana Objetivo")
controller.connect()
```

---

## 📚 Documentación

### 🇪🇸 Español

| Documento | Descripción |
|-----------|-------------|
| 📖 **[ARQUITECTURA_COMPLETA.md](ARQUITECTURA_COMPLETA.md)** | Guía completa:  estructura, flujo de datos, componentes y ejemplos |

### 🇬🇧 English

| Section | Description |
|---------|-------------|
| 📥 [Installation](docs/getting-started/installation.md) | System requirements and setup |
| ⚡ [Quickstart](docs/getting-started/quickstart.md) | Get running in 5 minutes |
| 🎧 [Emotiv Setup](docs/hardware/emotiv-setup.md) | Hardware configuration guide |
| 📖 [API Reference](docs/api/emotiv-controller.md) | Class and method documentation |
| 🏛️ [System Design](docs/architecture/system-design.md) | Architecture overview |

---

## 📂 Estructura del Proyecto

```
bcipydummies/
├── __init__.py              # Punto de entrada
├── __main__.py              # CLI:  python -m bcipydummies
├── emotiv_controller.py     # Controlador legacy
│
├── core/                    # Núcleo del sistema
│   ├── config.py            # Configuración
│   ├── engine.py            # BCIPipeline - Orquestador principal
│   ├── events.py            # Tipos de eventos
│   ├── exceptions.py        # Excepciones personalizadas
│   └── factory.py           # Funciones factory
│
├── sources/                 # Fuentes de datos EEG
├── processors/              # Procesadores de señal
└── publishers/              # Publicadores de salida
```

---

## ✨ Características

- ✅ Conexión WebSocket a Emotiv Cortex API
- ✅ Procesamiento de comandos mentales (left, right, lift)
- ✅ Simulación de teclado para aplicaciones Windows
- ✅ Utilidad de enumeración de ventanas
- ✅ Fuente mock para pruebas sin hardware
- ✅ Arquitectura modular y extensible

---
## 📚 Documentation / Documentación

| English 🇬🇧 | Español 🇪🇸 |
|-------------|-------------|
| [Getting Started](docs/en/getting-started/index.md) | [Primeros Pasos](docs/es/getting-started/index.md) |
| [Installation](docs/en/getting-started/installation.md) | [Instalación](docs/es/getting-started/installation.md) |
| [Quickstart](docs/en/getting-started/quickstart.md) | [Inicio Rápido](docs/es/getting-started/quickstart. md) |
| [Hardware Setup](docs/en/hardware/emotiv-setup.md) | [Configuración Hardware](docs/es/hardware/emotiv-setup. md) |
| [API Reference](docs/en/api/emotiv-controller.md) | [Referencia API](docs/es/api/emotiv-controller. md) |
| [System Design](docs/en/architecture/system-design.md) | [Diseño del Sistema](docs/es/architecture/system-design.md) |
| [Deep Dive](docs/en/deep-dive/deep-dive.md) | [Deep Dive](docs/es/deep-dive/deep-dive.md) |
| [Examples](docs/en/examples/examples.md) | [Ejemplos](docs/es/examples/examples. md) |  

## 👥 Colaboradores

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/itsvaalentine">
        <img src="https://avatars.githubusercontent.com/u/96605134?v=4" width="100px;" alt="itsvaalentine"/>
        <br />
        <sub><b>@itsvaalentine</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Gaelite">
        <img src="https://avatars.githubusercontent.com/u/129134162?v=4" width="100px;" alt="Gaelite"/>
        <br />
        <sub><b>@Gaelite</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/BernardoAguayoOrtega">
        <img src="https://avatars.githubusercontent.com/u/63122476?v=4" width="100px;" alt="BernardoAguayoOrtega"/>
        <br />
        <sub><b>@BernardoAguayoOrtega</b></sub>
      </a>
    </td>
  </tr>
</table>

---

## 📬 Soporte

- 🐛 [GitHub Issues](https://github.com/itsvaalentine/BCIpyDummies/issues) - Reportar bugs
- 💬 [GitHub Discussions](https://github.com/itsvaalentine/BCIpyDummies/discussions) - Preguntas

---

```
                    Hecho con 🧠 por @itsvaalentine
```