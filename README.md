```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ____   ____ ___            ____                            _           ║
║  | __ ) / ___|_ _|_ __  _   |  _ \ _   _ _ __ ___  _ __ ___ (_) ___  ___ ║
║  |  _ \| |    | || '_ \| | | | | | | | | '_ ` _ \| '_ ` _ \| |/ _ \/ __| ║
║  | |_) | |___ | || |_) | |_| | |_| | |_| | | | | | | | | | | |  __/\__ \ ║
║  |____/ \____|___| .__/ \__, |____/ \__,_|_| |_| |_|_| |_| |_|\___||___/ ║
║                  |_|    |___/                                            ║
║                                                                          ║
║                       **For dummies 4 real**                             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

[![Python](https://img.shields.io/badge/Python-3.9+-blue. svg)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)

---

**Middleware to connect Emotiv EEG headsets with Windows applications through mental commands.**

BCIpyDummies acts as a translator between your brain and your computer. It captures mental commands from your Emotiv headset and converts them into keyboard inputs to control any Windows application.

---

## 🎯 Use Cases

- 🎮 Control video games with your mind
- 🖥️ Hands-free application control
- 🔬 BCI research and experimentation
- ♿ Accessibility solutions

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BCIPipeline (Orchestrator)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │    SOURCES     │───▶│   PROCESSORS     │───▶│     PUBLISHERS         │  │
│  │    (Input)     │    │  (Processing)    │    │      (Output)          │  │
│  └────────────────┘    └──────────────────┘    └────────────────────────┘  │
│                                                                             │
│  • EmotivSource        • ThresholdProcessor    • KeyboardPublisher         │
│  • MockSource          • DebounceProcessor     • ConsolePublisher          │
│                        • CommandMapper                                      │
│                                                                             │
└──────────���──────────────────────────────────────────────────────────────────┘
```

📖 **[View Full Architecture →](ARQUITECTURA_COMPLETA. md)**

---

## 📋 Requirements

| Requirement | Version |
|-------------|---------|
| Operating System | Windows 10/11 |
| Python | 3.9+ |
| Hardware | Emotiv EEG Headset (EPOC X, EPOC+, Insight, Flex) |
| Software | [Emotiv Cortex](https://www.emotiv.com/emotiv-cortex/) |

---

## 🧠 Step 0: Subject Preparation & Mental Command Training (REQUIRED)

> **⚠️ IMPORTANT:** Before using this library, you MUST prepare the subject and train their mental command profile in Emotiv BCI. This is essential to get the maximum potential from BCIpyDummies. 

### Subject Preparation

Before putting on the headset:

1. **Clean hair** - No hair products (gel, hairspray, etc.)
2. **Stay hydrated** - Drink water before the session
3. **Rest well** - Be adequately rested to ensure optimal signal quality
4. **Comfortable environment** - Minimize distractions and noise

These precautions help minimize artifacts and optimize EEG signal quality.

### Mental Command Training in Emotiv BCI

Open the Emotiv BCI app and follow these steps:

#### 1. 🔴 Train the NEUTRAL State First (MANDATORY)

> **⚠️ DO NOT SKIP THIS STEP.** Many users assume Neutral is automatic — it is NOT. You must explicitly train it. 

The **Neutral state** is your brain's "baseline" or "do nothing" state. Without it, the system cannot distinguish between intentional commands and random brain activity.

**How to train Neutral:**
1. Open Emotiv BCI → Mental Commands
2. Select **Neutral** as the command to train
3. During training: **relax, breathe normally, don't think about any movement**
4. Keep your mind calm and unfocused (like daydreaming or zoning out)
5. Complete **at least 8-10 training trials** of 8 seconds each

**Why Neutral is critical:**
- It serves as the reference point for ALL other commands
- Without a good Neutral baseline, the system will constantly trigger false positives
- A well-trained Neutral = fewer accidental commands during use

#### 2. Train Your Mental Commands

**Only after training Neutral**, proceed to train each command by **mentally visualizing** the intended action:

| Command | Visualization | Tips |
|---------|---------------|------|
| **Right** | Imagine pushing something to the right | Visualize your hand pushing a box right |
| **Left** | Imagine pushing something to the left | Visualize your hand pushing a box left |
| **Lift** | Imagine lifting something up | Visualize lifting a heavy object or jumping |

**Training Protocol:**
- Perform **10 trials per command**, each lasting **8 seconds**
- Take a **2-minute break** every 3 trials to avoid cognitive fatigue
- Maintain concentration and focus during each trial
- **Do NOT physically move** — only imagine the movement

#### 3. Recommended Training Order

```
1. Neutral (FIRST - ALWAYS)
2. Right
3. Left  
4. Lift
```

> **Note:** Always start with Neutral. The order of Right/Left/Lift can vary, but Neutral must be trained first.

#### 4. Verify Your Training

Before using BCIpyDummies:
- Check that each command achieves a reasonable potency score (>50%) in Emotiv BCI
- Test the commands in Emotiv's built-in visualization
- Practice switching between Neutral and active commands
- If accuracy is low, retrain the problematic command

**Pro tip:** Spend extra time on Neutral training. A strong Neutral baseline improves ALL other command recognition.

---

## 🚀 Quick Start

```bash
pip install bcipydummies
```

```python
from bcipydummies.emotiv_controller import EmotivController

# List available windows
windows = EmotivController.list_windows()
print(windows)

# Connect and control an application
controller = EmotivController("Your Target Window")
controller.connect()
```

---

## 📚 Documentation

### 🇪🇸 Español

| Document | Description |
|----------|-------------|
| 📖 **[ARQUITECTURA_COMPLETA.md](ARQUITECTURA_COMPLETA.md)** | Complete guide: structure, data flow, components and examples |

### 🇬🇧 English

| Section | Description |
|---------|-------------|
| 📥 [Installation](docs/en/getting-started/installation.md) | System requirements and setup |
| ⚡ [Quickstart](docs/en/getting-started/quickstart.md) | Get running in 5 minutes |
| 🎧 [Emotiv Setup](docs/en/hardware/emotiv-setup.md) | Hardware configuration guide |
| 📖 [API Reference](docs/en/api/emotiv-controller.md) | Class and method documentation |
| 🏛️ [System Design](docs/en/architecture/system-design.md) | Architecture overview |

---

## 📂 Project Structure

```
bcipydummies/
├── __init__.py              # Entry point
├── __main__.py              # CLI: python -m bcipydummies
├── emotiv_controller.py     # Legacy controller
│
├── core/                    # System core
│   ├── config.py            # Configuration
│   ├── engine.py            # BCIPipeline - Main orchestrator
│   ├── events. py            # Event types
│   ├── exceptions.py        # Custom exceptions
│   └── factory.py           # Factory functions
│
├── sources/                 # EEG data sources
├── processors/              # Signal processors
└── publishers/              # Output publishers
```

---

## ✨ Features

- ✅ WebSocket connection to Emotiv Cortex API
- ✅ Mental command processing (left, right, lift)
- ✅ Keyboard simulation for Windows applications
- ✅ Window enumeration utility
- ✅ Mock source for testing without hardware
- ✅ Modular and extensible architecture

---

## 📚 Documentation / Documentación

| English 🇬🇧 | Español 🇪🇸 |
|-------------|-------------|
| [Getting Started](docs/en/index.md) | [Primeros Pasos](docs/es/index.md) |
| [Installation](docs/en/getting-started/installation.md) | [Instalación](docs/es/getting-started/installation.md) |
| [Quickstart](docs/en/getting-started/quickstart.md) | [Inicio Rápido](docs/es/getting-started/quickstart.md) |
| [Hardware Setup](docs/en/hardware/emotiv-setup.md) | [Configuración Hardware](docs/es/hardware/emotiv-setup..md) |
| [API Reference](docs/en/api/emotiv-controller.md) | [Referencia API](docs/es/api/emotiv-controller.md) |
| [System Design](docs/en/architecture/system-design.md) | [Diseño del Sistema](docs/es/architecture/system-design.md) |
| [Deep Dive](docs/en/deep-dive/deep-dive.md) | [Vision General ](docs/es/vision-general.md) |
| [Examples](docs/en/examples/examples.md) | [Ejemplos](docs/es/ejemplos/ejemplos.md) |

## 👥 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/itsvaalentine">
        <img src="https://avatars.githubusercontent.com/u/96605134? v=4" width="100px;" alt="itsvaalentine"/>
        <br />
        <sub><b>@itsvaalentine</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Gaelite">
        <img src="https://avatars.githubusercontent.com/u/129134162? v=4" width="100px;" alt="Gaelite"/>
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

## 📬 Support

- 🐛 [GitHub Issues](https://github.com/itsvaalentine/BCIpyDummies/issues) - Report bugs
- 💬 [GitHub Discussions](https://github.com/itsvaalentine/BCIpyDummies/discussions) - Questions

---

```
                    Made with 🧠 by @itsvaalentine
```