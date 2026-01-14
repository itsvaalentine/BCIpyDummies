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
┌─────────────────────────────────────────────────────────────────────────────┐
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

📖 **[Ver Arquitectura Completa →](ARQUITECTURA_COMPLETA. md)**

---

## 📋 Requisitos

| Requisito | Versión |
|-----------|---------|
| Sistema Operativo | Windows 10/11 |
| Python | 3.9+ |
| Hardware | Headset Emotiv EEG (EPOC X, EPOC+, Insight, Flex) |
| Software | [Emotiv Cortex](https://www.emotiv.com/emotiv-cortex/) |

---

## 🧠 Paso 0: Preparación del Sujeto y Entrenamiento de Comandos Mentales (OBLIGATORIO)

> **⚠️ IMPORTANTE:** Antes de usar esta librería, DEBES preparar al sujeto y entrenar su perfil de comandos mentales en Emotiv BCI.  Esto es esencial para obtener el máximo potencial de BCIpyDummies.

### Preparación del Sujeto

Antes de colocar el headset: 

1. **Cabello limpio** - Sin productos (gel, spray, etc.)
2. **Buena hidratación** - Beber agua antes de la sesión
3. **Descanso adecuado** - Estar bien descansado para óptima calidad de señal
4. **Ambiente cómodo** - Minimizar distracciones y ruido

Estas precauciones ayudan a minimizar artefactos y optimizar la calidad de la señal EEG.

### Entrenamiento de Comandos Mentales en Emotiv BCI

Abre la aplicación Emotiv BCI y sigue estos pasos:

#### 1. 🔴 Entrena el Estado NEUTRAL Primero (OBLIGATORIO)

> **⚠️ NO SALTES ESTE PASO. ** Muchos usuarios asumen que Neutral es automático — NO lo es.  Debes entrenarlo explícitamente.

El **estado Neutral** es la "línea base" o estado de "no hacer nada" de tu cerebro. Sin él, el sistema no puede distinguir entre comandos intencionales y actividad cerebral aleatoria.

**Cómo entrenar Neutral:**
1. Abre Emotiv BCI → Mental Commands
2. Selecciona **Neutral** como el comando a entrenar
3. Durante el entrenamiento:  **relájate, respira normalmente, no pienses en ningún movimiento**
4. Mantén tu mente calmada y desenfocada (como soñar despierto)
5. Completa **al menos 8-10 sesiones de entrenamiento** de 8 segundos cada una

**Por qué Neutral es crítico:**
- Sirve como punto de referencia para TODOS los demás comandos
- Sin una buena línea base Neutral, el sistema constantemente disparará falsos positivos
- Un Neutral bien entrenado = menos comandos accidentales durante el uso

#### 2. Entrena tus Comandos Mentales

**Solo después de entrenar Neutral**, procede a entrenar cada comando **visualizando mentalmente** la acción deseada:

| Comando | Visualización | Tips |
|---------|---------------|------|
| **Right** | Imagina empujar algo hacia la derecha | Visualiza tu mano empujando una caja a la derecha |
| **Left** | Imagina empujar algo hacia la izquierda | Visualiza tu mano empujando una caja a la izquierda |
| **Lift** | Imagina levantar algo | Visualiza levantar un objeto pesado o saltar |

**Protocolo de Entrenamiento:**
- Realiza **10 sesiones por comando**, cada una de **8 segundos**
- Toma un **descanso de 2 minutos** cada 3 sesiones para evitar fatiga cognitiva
- Mantén concentración y enfoque durante cada sesión
- **NO te muevas físicamente** — solo imagina el movimiento

#### 3. Orden de Entrenamiento Recomendado

```
1. Neutral (PRIMERO - SIEMPRE)
2. Right
3. Left
4. Lift
```

> **Nota:** Siempre comienza con Neutral.  El orden de Right/Left/Lift puede variar, pero Neutral debe entrenarse primero.

#### 4. Verifica tu Entrenamiento

Antes de usar BCIpyDummies:
- Verifica que cada comando alcance una puntuación de potencia razonable (>50%) en Emotiv BCI
- Prueba los comandos en la visualización integrada de Emotiv
- Practica alternar entre Neutral y comandos activos
- Si la precisión es baja, re-entrena el comando problemático

**Pro tip:** Dedica tiempo extra al entrenamiento de Neutral.  Una línea base Neutral fuerte mejora el reconocimiento de TODOS los demás comandos.

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
| 📖 **[ARQUITECTURA_COMPLETA.md](ARQUITECTURA_COMPLETA. md)** | Guía completa:  estructura, flujo de datos, componentes y ejemplos |

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
| [Installation](docs/en/getting-started/installation.md) | [Instalación](docs/es/getting-started/installation. md) |
| [Quickstart](docs/en/getting-started/quickstart.md) | [Inicio Rápido](docs/es/getting-started/quickstart. md) |
| [Hardware Setup](docs/en/hardware/emotiv-setup.md) | [Configuración Hardware](docs/es/hardware/emotiv-setup. md) |
| [API Reference](docs/en/api/emotiv-controller.md) | [Referencia API](docs/es/api/emotiv-controller. md) |
| [System Design](docs/en/architecture/system-design.md) | [Diseño del Sistema](docs/es/architecture/system-design.md) |
| [Deep Dive](docs/en/deep-dive/deep-dive.md) | [Deep Dive](docs/es/deep-dive/deep-dive.md) |
| [Examples](docs/en/examples/examples.md) | [Ejemplos](docs/es/examples/examples.md) |

## 👥 Colaboradores

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

## 📬 Soporte

- 🐛 [GitHub Issues](https://github.com/itsvaalentine/BCIpyDummies/issues) - Reportar bugs
- 💬 [GitHub Discussions](https://github.com/itsvaalentine/BCIpyDummies/discussions) - Preguntas

---

```
                    Hecho con 🧠 por @itsvaalentine
```