# 🧠 Arquitectura Completa de BCIpyDummies

Esta guía te ayudará a entender la estructura del proyecto, cómo se comunica cada parte y qué hace cada función para que puedas utilizar y probar esta librería.

## 📋 Índice

1. [Visión General](#visión-general)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Datos](#flujo-de-datos)
5. [Cómo se Comunican los Componentes](#cómo-se-comunican-los-componentes)
6. [Guía de Uso y Pruebas](#guía-de-uso-y-pruebas)
7. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## Visión General

BCIpyDummies es un **middleware** que actúa como traductor entre los dispositivos EEG Emotiv y las aplicaciones de Windows. La librería captura comandos mentales del headset Emotiv y los traduce en pulsaciones de teclado.

### Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BCIPipeline (Orquestador)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐    ┌──────────────────┐    ┌────────────────────────┐   │
│  │    SOURCES     │───▶│   PROCESSORS     │───▶│     PUBLISHERS         │   │
│  │  (Entrada)     │    │  (Procesamiento) │    │     (Salida)           │   │
│  └────────────────┘    └──────────────────┘    └────────────────────────┘   │
│                                                                              │
│  • EmotivSource       • ThresholdProcessor    • KeyboardPublisher           │
│  • MockSource         • DebounceProcessor     • ConsolePublisher            │
│                       • CommandMapper                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Estructura del Proyecto

```
bcipydummies/
├── __init__.py              # Punto de entrada, exporta todas las clases públicas
├── __main__.py              # Permite ejecutar: python -m bcipydummies
├── emotiv_controller.py     # Controlador legacy (versión antigua, simple)
│
├── core/                    # Núcleo del sistema
│   ├── __init__.py
│   ├── config.py            # Configuración (ThresholdConfig, KeyboardConfig, etc.)
│   ├── engine.py            # BCIPipeline - Orquestador principal
│   ├── events.py            # Tipos de eventos (MentalCommandEvent, etc.)
│   ├── exceptions.py        # Excepciones personalizadas
│   └── factory.py           # Funciones factory para crear componentes
│
├── sources/                 # Fuentes de datos EEG
│   ├── __init__.py
│   ├── base.py              # Protocolo/interfaz EEGSource
│   ├── mock.py              # Fuente simulada para pruebas
│   └── emotiv/              # Implementación para Emotiv
│       ├── __init__.py
│       ├── cortex_client.py # Cliente WebSocket para Cortex API
│       └── source.py        # EmotivSource
│
├── processors/              # Procesadores de eventos
│   ├── __init__.py
│   ├── base.py              # Interfaz Processor
│   ├── threshold.py         # Filtro por umbral de potencia
│   ├── debounce.py          # Evita comandos repetidos rápidos
│   └── mapper.py            # Mapea comandos a acciones
│
├── publishers/              # Publicadores de salida
│   ├── __init__.py
│   ├── base.py              # Interfaz Publisher
│   ├── console.py           # Imprime en consola (debugging)
│   └── keyboard/            # Simulación de teclado
│       ├── __init__.py
│       ├── base.py          # KeyboardPublisher base
│       └── windows.py       # Implementación Windows
│
└── cli/                     # Interfaz de línea de comandos
    ├── __init__.py
    ├── main.py              # Punto de entrada CLI
    └── commands/            # Comandos disponibles
```

---

## Componentes Principales

### 1. 🔌 Sources (Fuentes de Datos)

Las **fuentes** son responsables de capturar datos EEG y convertirlos en eventos.

#### `EEGSource` (Protocolo Base)
```python
# Ubicación: bcipydummies/sources/base.py

class EEGSource(Protocol):
    """Interfaz que todas las fuentes deben implementar."""
    
    @property
    def source_id(self) -> str:
        """Identificador único de la fuente."""
        
    @property
    def is_connected(self) -> bool:
        """True si está conectada y transmitiendo."""
        
    def connect(self) -> None:
        """Establece conexión con el dispositivo EEG."""
        
    def disconnect(self) -> None:
        """Desconecta del dispositivo EEG."""
        
    def subscribe(self, callback: EventCallback) -> None:
        """Registra un callback para recibir eventos."""
        
    def unsubscribe(self, callback: EventCallback) -> None:
        """Elimina un callback registrado."""
```

#### `EmotivSource` (Implementación Emotiv)
```python
# Ubicación: bcipydummies/sources/emotiv/source.py

class EmotivSource(BaseEEGSource):
    """
    Fuente EEG para dispositivos Emotiv via Cortex API.
    
    Streams disponibles (sin licencia):
    - "com": Comandos mentales (push, pull, left, right, lift, etc.)
    - "fac": Expresiones faciales (blink, smile, frown, wink, etc.)
    - "met": Métricas de rendimiento (atención, estrés, relajación)
    - "pow": Bandas de potencia (theta, alpha, beta, gamma)
    - "dev": Info del dispositivo (batería, calidad de señal)
    - "sys": Eventos del sistema
    
    Flujo de conexión:
    1. Conecta vía WebSocket a wss://localhost:6868
    2. Solicita acceso (muestra popup en Cortex si no está aprobado)
    3. Autentica con client_id y client_secret
    4. Busca headsets disponibles
    5. Crea sesión con el headset
    6. Se suscribe a los streams configurados
    
    Ejemplo con múltiples streams:
        source = EmotivSource(
            credentials=credentials,
            streams=["com", "fac", "met"]  # Comandos, facial, métricas
        )
    """
```

#### `MockSource` (Para Pruebas)
```python
# Ubicación: bcipydummies/sources/mock.py

class MockSource(BaseEEGSource):
    """
    Fuente simulada para desarrollo y pruebas.
    
    Dos modos de operación:
    - Aleatorio: genera comandos aleatorios periódicamente
    - Scripted: reproduce una secuencia predefinida de eventos
    """
```

### 2. ⚙️ Processors (Procesadores)

Los **procesadores** transforman y filtran eventos en una cadena secuencial.

#### `Processor` (Interfaz Base)
```python
# Ubicación: bcipydummies/processors/base.py

class Processor(ABC):
    """
    Interfaz base para procesadores.
    
    Cada procesador recibe un evento y puede:
    - Pasarlo sin cambios
    - Transformarlo
    - Filtrarlo (retorna None)
    """
    
    @abstractmethod
    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        """Procesa un evento. Retorna None para filtrar."""
        
    @abstractmethod
    def reset(self) -> None:
        """Reinicia el estado interno del procesador."""
```

#### `ThresholdProcessor` (Filtro por Umbral)
```python
# Ubicación: bcipydummies/processors/threshold.py

class ThresholdProcessor(Processor):
    """
    Filtra eventos por debajo del umbral de potencia configurado.
    
    Ejemplo:
        processor = ThresholdProcessor(thresholds={"left": 0.8})
        # Solo pasan eventos 'left' con potencia >= 80%
    """
```

#### `DebounceProcessor` (Anti-rebote)
```python
# Ubicación: bcipydummies/processors/debounce.py

class DebounceProcessor(Processor):
    """
    Evita comandos repetidos en un período de tiempo (cooldown).
    
    Ejemplo:
        processor = DebounceProcessor(cooldown=0.3)
        # Ignora el mismo comando si llega antes de 300ms
    """
```

#### `CommandMapper` (Mapeo de Comandos)
```python
# Ubicación: bcipydummies/processors/mapper.py

class CommandMapper(Processor):
    """
    Mapea comandos mentales a acciones (teclas).
    
    Ejemplo:
        mapper = CommandMapper(mapping={
            "left": "A",
            "right": "D",
            "lift": "SPACE"
        })
    """
```

### 3. 📤 Publishers (Publicadores)

Los **publicadores** reciben eventos procesados y ejecutan acciones.

#### `Publisher` (Interfaz Base)
```python
# Ubicación: bcipydummies/publishers/base.py

class Publisher(ABC):
    """
    Interfaz base para publicadores.
    
    Ciclo de vida:
    1. start() - Inicializa recursos
    2. publish(event) - Procesa eventos
    3. stop() - Libera recursos
    """
    
    @abstractmethod
    def publish(self, event: EEGEvent) -> None:
        """Publica un evento EEG."""
        
    @abstractmethod
    def start(self) -> None:
        """Inicializa el publicador."""
        
    @abstractmethod
    def stop(self) -> None:
        """Detiene el publicador."""
        
    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """True si está listo para recibir eventos."""
```

#### `ConsolePublisher` (Salida a Consola)
```python
# Ubicación: bcipydummies/publishers/console.py

class ConsolePublisher(Publisher):
    """
    Imprime eventos en la consola.
    Útil para debugging y desarrollo.
    """
```

#### `WindowsKeyboardPublisher` (Teclado Windows)
```python
# Ubicación: bcipydummies/publishers/keyboard/windows.py

class WindowsKeyboardPublisher:
    """
    Simula pulsaciones de teclado en Windows.
    
    Usa la API win32 para enviar eventos de teclado
    a una ventana específica.
    """
```

### 4. 🎛️ BCIPipeline (Orquestador)

```python
# Ubicación: bcipydummies/core/engine.py

class BCIPipeline:
    """
    Orquestador central que conecta Source -> Processors -> Publishers.
    
    Características:
    - Thread-safe mediante locks
    - Maneja ciclo de vida de componentes
    - Estadísticas de eventos procesados
    - Soporta context manager (with)
    """
```

### 5. 📊 Events (Eventos)

```python
# Ubicación: bcipydummies/core/events.py

class MentalCommand(Enum):
    """
    Comandos mentales soportados:
    NEUTRAL, PUSH, PULL, LIFT, DROP,
    LEFT, RIGHT, ROTATE_LEFT, ROTATE_RIGHT, DISAPPEAR
    """

class FacialExpression(Enum):
    """
    Expresiones faciales soportadas:
    NEUTRAL, BLINK, WINK_LEFT, WINK_RIGHT, SURPRISE, FROWN,
    SMILE, CLENCH, LAUGH, SMIRK_LEFT, SMIRK_RIGHT,
    LOOK_LEFT, LOOK_RIGHT, LOOK_UP, LOOK_DOWN
    """

class EmotivStream(Enum):
    """
    Streams de datos disponibles:
    COM (comandos), FAC (facial), MET (métricas), 
    POW (potencia), DEV (dispositivo), SYS (sistema)
    """

@dataclass(frozen=True)
class MentalCommandEvent(EEGEvent):
    """
    Evento de comando mental.
    
    Atributos:
    - timestamp: Momento del evento
    - source_id: ID de la fuente
    - command: Tipo de comando (MentalCommand)
    - power: Potencia/confianza (0.0 - 1.0)
    - action: Acción mapeada (opcional)
    """

@dataclass(frozen=True)
class FacialExpressionEvent(EEGEvent):
    """
    Evento de expresión facial.
    
    Atributos:
    - timestamp: Momento del evento
    - source_id: ID de la fuente
    - expression: Tipo de expresión (FacialExpression)
    - power: Potencia/confianza (0.0 - 1.0)
    """

@dataclass(frozen=True)
class PerformanceMetricsEvent(EEGEvent):
    """
    Evento de métricas de rendimiento.
    
    Atributos:
    - focus: Nivel de foco/atención (0.0 - 1.0)
    - engagement: Nivel de compromiso (0.0 - 1.0)
    - excitement: Nivel de excitación (0.0 - 1.0)
    - long_excitement: Excitación a largo plazo (0.0 - 1.0)
    - stress: Nivel de estrés (0.0 - 1.0)
    - relaxation: Nivel de relajación (0.0 - 1.0)
    - interest: Nivel de interés (0.0 - 1.0)
    """

@dataclass(frozen=True)
class DeviceInfoEvent(EEGEvent):
    """
    Evento de información del dispositivo.
    
    Atributos:
    - battery_level: Nivel de batería (0-100%)
    - signal_quality: Calidad de señal (0.0 - 1.0)
    - contact_quality: Calidad por canal (dict)
    """
```

---

## Flujo de Datos

### Diagrama de Flujo Completo

```
┌──────────────────┐
│  Headset Emotiv  │ (Hardware EEG)
└────────┬─────────┘
         │ Bluetooth/USB
         ▼
┌──────────────────┐
│ Emotiv Cortex App│ (Software Emotiv)
└────────┬─────────┘
         │ WebSocket (wss://localhost:6868)
         ▼
┌──────────────────────────────────────────────────────────────┐
│                        BCIPipeline                            │
│  ┌─────────────┐                                              │
│  │EmotivSource │                                              │
│  │             │                                              │
│  │ CortexClient├──┐  ┌─────────────────────────────────────┐ │
│  └─────────────┘  │  │         PROCESSOR CHAIN             │ │
│                   │  │                                     │ │
│                   ▼  │  ┌──────────┐  ┌──────────┐        │ │
│  MentalCommandEvent │  │Threshold │──▶│Debounce │──┐     │ │
│      {                │  │Processor │  │Processor │  │     │ │
│        command: LEFT, │  └──────────┘  └──────────┘  │     │ │
│        power: 0.85    │                              │     │ │
│      }                │  ┌──────────┐                │     │ │
│                   ────┼─▶│Command   │◀───────────────┘     │ │
│                       │  │Mapper    │                      │ │
│                       │  └────┬─────┘                      │ │
│                       └───────┼────────────────────────────┘ │
│                               │                              │
│                               ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    PUBLISHERS (Fan-out)                  ││
│  │  ┌─────────────────┐    ┌─────────────────────────────┐ ││
│  │  │ConsolePublisher │    │WindowsKeyboardPublisher    │ ││
│  │  │                 │    │                             │ ││
│  │  │ print(event)    │    │ PostMessage(WM_KEYDOWN)    │ ││
│  │  └─────────────────┘    └─────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Aplicación Target│ (Juego, Notepad, etc.)
                    └──────────────────┘
```

### Flujo de Autenticación Emotiv

```
┌──────────────┐                    ┌──────────────┐
│   Cliente    │                    │ Cortex API   │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │──── 1. authorize() ──────────────▶│
       │      {clientId, clientSecret}     │
       │◀─── cortexToken ─────────────────│
       │                                   │
       │──── 2. queryHeadsets() ─────────▶│
       │◀─── lista de headsets ───────────│
       │                                   │
       │──── 3. createSession() ─────────▶│
       │      {headsetId}                  │
       │◀─── sessionId ───────────────────│
       │                                   │
       │──── 4. subscribe() ─────────────▶│
       │      {streams: ["com"]}           │
       │◀─── datos de streaming ──────────│
       │                                   │
```

---

## Cómo se Comunican los Componentes

### 1. Patrón Observer (Source → Pipeline)

La fuente emite eventos a través de callbacks registrados:

```python
# El Pipeline se suscribe a la fuente
source.subscribe(callback=self._on_event)

# Cuando llega un evento, la fuente lo emite
def _emit(self, event: EEGEvent) -> None:
    for callback in self._subscribers:
        callback(event)
```

### 2. Patrón Chain of Responsibility (Processors)

Los procesadores se ejecutan en secuencia:

```python
# En BCIPipeline._on_event():
current_event = event
for processor in self._processors:
    if current_event is None:
        break  # Evento filtrado
    current_event = processor.process(current_event)
```

### 3. Patrón Fan-out (Pipeline → Publishers)

El evento procesado se envía a todos los publishers:

```python
# En BCIPipeline._on_event():
for publisher in self._publishers:
    if publisher.is_ready:
        publisher.publish(current_event)
```

---

## Guía de Uso y Pruebas

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/itsvaalentine/BCIpyDummies.git
cd BCIpyDummies

# Instalar en modo desarrollo
pip install -e .

# Instalar dependencias de desarrollo (para tests)
pip install -e ".[dev]"
```

### Configuración de Credenciales

```bash
# Variables de entorno (recomendado)
export EMOTIV_CLIENT_ID="tu_client_id"
export EMOTIV_CLIENT_SECRET="tu_client_secret"
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests específicos
pytest tests/test_core.py -v
pytest tests/test_processors.py -v
pytest tests/test_sources.py -v
pytest tests/test_publishers.py -v
```

---

## Ejemplos Prácticos

### Ejemplo 1: Uso Básico con MockSource (Sin Hardware)

```python
"""
Este ejemplo funciona sin hardware Emotiv.
Perfecto para probar la librería.
"""
import time
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher
from bcipydummies.core.events import MentalCommand

# Crear fuente simulada que genera eventos aleatorios
source = MockSource(
    source_id="test-source",
    random_interval=1.0,  # Un evento cada segundo
    random_commands=[
        MentalCommand.LEFT,
        MentalCommand.RIGHT,
        MentalCommand.PUSH,
        MentalCommand.NEUTRAL,
    ]
)

# Crear publicador de consola
console = ConsolePublisher(prefix="[BCI]")

# Crear y ejecutar el pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[console]
)

# Usar como context manager
with pipeline:
    print("Pipeline iniciado. Presiona Ctrl+C para detener.")
    try:
        time.sleep(10)  # Ejecutar por 10 segundos
    except KeyboardInterrupt:
        pass

print("Pipeline detenido.")
print(f"Estadísticas: {pipeline.statistics}")
```

### Ejemplo 2: Pipeline Completo con Procesadores

```python
"""
Ejemplo con cadena de procesadores.
"""
from bcipydummies import (
    BCIPipeline,
    MockSource,
    ConsolePublisher,
    ThresholdProcessor,
    DebounceProcessor,
    CommandMapper
)

# Fuente simulada
source = MockSource()

# Cadena de procesadores
processors = [
    # 1. Filtrar por umbral de potencia
    ThresholdProcessor(
        thresholds={
            "left": 0.7,   # Solo left con 70%+ potencia
            "right": 0.6,  # Solo right con 60%+ potencia
        },
        default_threshold=0.5
    ),
    
    # 2. Evitar comandos repetidos
    DebounceProcessor(cooldown=0.3),  # 300ms entre comandos
    
    # 3. Mapear comandos a teclas
    CommandMapper(
        mapping={
            "left": "A",
            "right": "D",
            "push": "W",
            "lift": "SPACE"
        }
    )
]

# Publicadores
publishers = [ConsolePublisher(prefix="[EVENTO]")]

# Crear pipeline
pipeline = BCIPipeline(
    source=source,
    processors=processors,
    publishers=publishers
)

# Ejecutar
with pipeline:
    import time
    time.sleep(30)
```

### Ejemplo 3: Secuencia de Eventos Scripted

```python
"""
Ejemplo con secuencia predefinida de eventos.
Útil para pruebas reproducibles.
"""
from bcipydummies.sources.mock import MockSource, ScriptedEvent, create_test_script
from bcipydummies.core.events import MentalCommand
from bcipydummies import BCIPipeline, ConsolePublisher

# Crear script de eventos
script = create_test_script(
    commands=["neutral", "left", "left", "right", "push", "neutral"],
    interval=0.5,  # 500ms entre eventos
    power=0.85
)

# Fuente con script
source = MockSource(script=script, loop_script=False)

# Pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time.sleep(5)  # Esperar que termine el script
```

### Ejemplo 4: Crear un Publicador Personalizado

```python
"""
Ejemplo de cómo crear tu propio publicador.
"""
from bcipydummies.publishers.base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent

class MiPublicador(Publisher):
    """Publicador personalizado que cuenta eventos por comando."""
    
    def __init__(self):
        self._is_ready = False
        self.contadores = {}
    
    def start(self) -> None:
        self._is_ready = True
        self.contadores = {}
        print("MiPublicador iniciado!")
    
    def stop(self) -> None:
        self._is_ready = False
        print(f"MiPublicador detenido. Contadores: {self.contadores}")
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event: EEGEvent) -> None:
        if isinstance(event, MentalCommandEvent):
            cmd = event.command.name
            self.contadores[cmd] = self.contadores.get(cmd, 0) + 1
            print(f"Comando {cmd} detectado ({self.contadores[cmd]} veces)")


# Usar el publicador personalizado
from bcipydummies import BCIPipeline, MockSource

source = MockSource()
mi_pub = MiPublicador()

with BCIPipeline(source=source, publishers=[mi_pub]):
    import time
    time.sleep(10)
```

### Ejemplo 5: Crear un Procesador Personalizado

```python
"""
Ejemplo de procesador personalizado que filtra comandos NEUTRAL.
"""
from bcipydummies.processors.base import Processor
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand
from typing import Optional

class FiltrarNeutral(Processor):
    """Filtra todos los eventos NEUTRAL."""
    
    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        if isinstance(event, MentalCommandEvent):
            if event.command == MentalCommand.NEUTRAL:
                return None  # Filtrar
        return event  # Pasar el resto
    
    def reset(self) -> None:
        pass  # No tiene estado


# Usar el procesador
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher

pipeline = BCIPipeline(
    source=MockSource(),
    processors=[FiltrarNeutral()],
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time.sleep(10)
```

### Ejemplo 6: Uso con Factory (Configuración Simplificada)

```python
"""
Uso de funciones factory para crear pipelines desde configuración.
"""
from bcipydummies import create_pipeline, Config, ThresholdConfig, KeyboardConfig, EmotivConfig

# Crear configuración
config = Config(
    emotiv=EmotivConfig(
        client_id="tu_client_id",
        client_secret="tu_client_secret"
    ),
    thresholds=ThresholdConfig(
        default=0.5,
        left=0.8,
        right=0.6
    ),
    keyboard=KeyboardConfig(
        left="a",
        right="d",
        lift="space"
    ),
    target_window="Notepad"
)

# Crear pipeline con factory
# Usa "simulated" en lugar de "emotiv" para pruebas sin hardware
pipeline = create_pipeline(config, source_type="simulated")

with pipeline:
    input("Presiona Enter para detener...")
```

### Ejemplo 7: Control de Ventana Real (Windows)

```python
"""
Ejemplo real controlando una ventana de Windows.
NOTA: Requiere Windows y la aplicación target abierta.
"""
from bcipydummies import BCIPipeline, MockSource, ThresholdProcessor, CommandMapper
from bcipydummies.publishers.keyboard.windows import WindowsKeyboardPublisher
from bcipydummies.core.events import MentalCommand

# Listar ventanas disponibles
print("Ventanas disponibles:")
for window in WindowsKeyboardPublisher.list_windows()[:20]:
    print(f"  - {window}")

# Configurar
target_window = "Notepad"  # Cambia esto por tu ventana

# Fuente simulada para pruebas
source = MockSource()

# Procesadores
processors = [
    ThresholdProcessor(thresholds={"left": 0.7, "right": 0.7}),
    CommandMapper(mapping={
        "left": "A",
        "right": "D", 
        "push": "W",
        "lift": "SPACE"
    })
]

# Publisher de teclado
keyboard = WindowsKeyboardPublisher(
    window_name=target_window,
    command_mapping={
        MentalCommand.LEFT: "A",
        MentalCommand.RIGHT: "D",
        MentalCommand.PUSH: "W",
        MentalCommand.LIFT: "SPACE"
    }
)

# Pipeline
pipeline = BCIPipeline(
    source=source,
    processors=processors,
    publishers=[keyboard]
)

try:
    with pipeline:
        print(f"Controlando '{target_window}'...")
        print("Presiona Ctrl+C para detener.")
        import time
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("\nDetenido.")
```

### Ejemplo 8: Uso con Hardware Real Emotiv (Mostrar Datos)

```python
"""
Ejemplo de uso con hardware REAL Emotiv.
Muestra los comandos mentales recibidos del dispositivo en tiempo real.

REQUISITOS:
- Emotiv Cortex app ejecutándose
- Headset Emotiv conectado y configurado
- Comandos mentales entrenados en EmotivBCI
- Credenciales de desarrollador (client_id, client_secret)
"""
import os
import time
from datetime import datetime

from bcipydummies import BCIPipeline, ConsolePublisher
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies.core.events import MentalCommandEvent, ConnectionEvent, EEGEvent
from bcipydummies.publishers.base import Publisher


class MonitorPublisher(Publisher):
    """
    Publisher personalizado para mostrar información detallada
    de los comandos recibidos del hardware Emotiv.
    """
    
    def __init__(self):
        self._is_ready = False
        self.total_eventos = 0
        self.comandos_por_tipo = {}
        self.ultimo_comando = None
        self.hora_inicio = None
    
    def start(self) -> None:
        self._is_ready = True
        self.hora_inicio = datetime.now()
        print("=" * 60)
        print("🧠 MONITOR DE COMANDOS EMOTIV - INICIADO")
        print("=" * 60)
        print(f"⏰ Inicio: {self.hora_inicio.strftime('%H:%M:%S')}")
        print("-" * 60)
    
    def stop(self) -> None:
        self._is_ready = False
        duracion = datetime.now() - self.hora_inicio if self.hora_inicio else None
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE SESIÓN")
        print("=" * 60)
        print(f"⏱️  Duración: {duracion}")
        print(f"📈 Total eventos: {self.total_eventos}")
        print("\n📋 Comandos por tipo:")
        for cmd, count in sorted(self.comandos_por_tipo.items()):
            porcentaje = (count / self.total_eventos * 100) if self.total_eventos > 0 else 0
            print(f"   • {cmd}: {count} ({porcentaje:.1f}%)")
        print("=" * 60)
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event: EEGEvent) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if isinstance(event, ConnectionEvent):
            estado = "✅ CONECTADO" if event.connected else "❌ DESCONECTADO"
            print(f"[{timestamp}] {estado}: {event.message or ''}")
            
        elif isinstance(event, MentalCommandEvent):
            self.total_eventos += 1
            cmd_name = event.command.name
            self.comandos_por_tipo[cmd_name] = self.comandos_por_tipo.get(cmd_name, 0) + 1
            
            # Barra de potencia visual
            potencia_porcentaje = event.power * 100
            barras = int(potencia_porcentaje / 5)  # 20 barras máximo
            barra_visual = "█" * barras + "░" * (20 - barras)
            
            # Emoji según el comando
            emojis = {
                "NEUTRAL": "😐",
                "PUSH": "👊",
                "PULL": "🤚",
                "LIFT": "⬆️",
                "DROP": "⬇️",
                "LEFT": "⬅️",
                "RIGHT": "➡️",
                "ROTATE_LEFT": "↪️",
                "ROTATE_RIGHT": "↩️",
                "DISAPPEAR": "👻"
            }
            emoji = emojis.get(cmd_name, "🧠")
            
            print(f"[{timestamp}] {emoji} {cmd_name:12} [{barra_visual}] {potencia_porcentaje:5.1f}%")
            
            # Guardar último comando no-neutral
            if cmd_name != "NEUTRAL":
                self.ultimo_comando = (cmd_name, event.power)


def main():
    """
    Función principal para conectar con hardware Emotiv real.
    """
    print("\n🔧 Configurando conexión con Emotiv...")
    
    # Obtener credenciales de variables de entorno
    client_id = os.environ.get("EMOTIV_CLIENT_ID")
    client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERROR: Configura las variables de entorno:")
        print("   export EMOTIV_CLIENT_ID='tu_client_id'")
        print("   export EMOTIV_CLIENT_SECRET='tu_client_secret'")
        return
    
    # Crear credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Crear fuente Emotiv (hardware real)
    source = EmotivSource(credentials=credentials)
    
    # Crear monitor para visualizar datos
    monitor = MonitorPublisher()
    
    # También añadir ConsolePublisher para ver eventos raw
    console = ConsolePublisher(prefix="[RAW]")
    
    # Crear pipeline
    pipeline = BCIPipeline(
        source=source,
        publishers=[monitor]  # Solo monitor para vista limpia
        # publishers=[monitor, console]  # Descomentar para ver también raw
    )
    
    print("\n🎧 Conectando con headset Emotiv...")
    print("   (Asegúrate de que Emotiv Cortex esté ejecutándose)")
    print("\n⌨️  Presiona Ctrl+C para detener\n")
    
    try:
        with pipeline:
            # Mantener ejecutando hasta Ctrl+C
            while True:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo...")


if __name__ == "__main__":
    main()
```

**Salida esperada del ejemplo:**

```
🔧 Configurando conexión con Emotiv...

🎧 Conectando con headset Emotiv...
   (Asegúrate de que Emotiv Cortex esté ejecutándose)

⌨️  Presiona Ctrl+C para detener

============================================================
🧠 MONITOR DE COMANDOS EMOTIV - INICIADO
============================================================
⏰ Inicio: 14:30:45
------------------------------------------------------------
[14:30:46.123] ✅ CONECTADO: Connected to EPOC-X12345
[14:30:46.234] 😐 NEUTRAL      [████████████████░░░░] 82.5%
[14:30:46.456] 😐 NEUTRAL      [███████████████░░░░░] 78.3%
[14:30:46.678] ⬅️ LEFT         [████████████████████] 95.2%
[14:30:46.890] ⬅️ LEFT         [██████████████████░░] 88.1%
[14:30:47.123] 😐 NEUTRAL      [████████████░░░░░░░░] 62.0%
[14:30:47.345] ➡️ RIGHT        [████████████████░░░░] 79.5%
[14:30:47.567] 👊 PUSH         [███████████████████░] 91.3%
...

🛑 Deteniendo...

============================================================
📊 RESUMEN DE SESIÓN
============================================================
⏱️  Duración: 0:02:15.234567
📈 Total eventos: 847

📋 Comandos por tipo:
   • LEFT: 45 (5.3%)
   • NEUTRAL: 756 (89.3%)
   • PUSH: 12 (1.4%)
   • RIGHT: 34 (4.0%)
============================================================
```

### Ejemplo 9: Captura Completa - Todos los Streams de Emotiv

```python
"""
Ejemplo COMPLETO para capturar TODOS los datos disponibles de Emotiv
sin necesidad de licencia:

- Comandos mentales (com)
- Expresiones faciales (fac)
- Métricas de rendimiento (met)
- Bandas de potencia (pow)
- Info del dispositivo (dev)

Este ejemplo permite al usuario elegir qué streams capturar.
"""
import os
import time
from datetime import datetime
from typing import Dict, List

from bcipydummies import BCIPipeline, ConsolePublisher
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies.core.events import (
    MentalCommandEvent,
    FacialExpressionEvent,
    PerformanceMetricsEvent,
    PowerBandEvent,
    DeviceInfoEvent,
    ConnectionEvent,
    EEGEvent,
)
from bcipydummies.publishers.base import Publisher


class MultiStreamMonitor(Publisher):
    """
    Monitor que captura y muestra todos los tipos de eventos de Emotiv.
    """
    
    def __init__(self, show_power_bands: bool = False):
        self._is_ready = False
        self.show_power_bands = show_power_bands
        
        # Contadores por tipo de evento
        self.stats = {
            "mental_commands": 0,
            "facial_expressions": 0,
            "performance_metrics": 0,
            "power_bands": 0,
            "device_info": 0,
        }
        
        # Último valor de cada métrica
        self.last_metrics: Dict[str, float] = {}
        self.last_battery: int = 0
    
    def start(self) -> None:
        self._is_ready = True
        print("=" * 70)
        print("🧠 MONITOR MULTI-STREAM DE EMOTIV - INICIADO")
        print("=" * 70)
        print(f"⏰ Inicio: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 70)
        print("📡 Streams activos: COM (mental), FAC (facial), MET (métricas)")
        print("-" * 70)
    
    def stop(self) -> None:
        self._is_ready = False
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE SESIÓN")
        print("=" * 70)
        print(f"🧠 Comandos mentales capturados: {self.stats['mental_commands']}")
        print(f"😀 Expresiones faciales capturadas: {self.stats['facial_expressions']}")
        print(f"📈 Actualizaciones de métricas: {self.stats['performance_metrics']}")
        print(f"🔋 Último nivel de batería: {self.last_battery}%")
        print("=" * 70)
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event: EEGEvent) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if isinstance(event, ConnectionEvent):
            estado = "✅ CONECTADO" if event.connected else "❌ DESCONECTADO"
            print(f"\n[{timestamp}] {estado}: {event.message or ''}\n")
            
        elif isinstance(event, MentalCommandEvent):
            self.stats["mental_commands"] += 1
            cmd = event.command.name
            power = event.power * 100
            
            # Barra visual de potencia
            bar = "█" * int(power / 5) + "░" * (20 - int(power / 5))
            
            emojis = {
                "NEUTRAL": "😐", "PUSH": "👊", "PULL": "🤚",
                "LIFT": "⬆️", "DROP": "⬇️", "LEFT": "⬅️",
                "RIGHT": "➡️", "ROTATE_LEFT": "↪️", "ROTATE_RIGHT": "↩️",
            }
            emoji = emojis.get(cmd, "🧠")
            
            print(f"[{timestamp}] 🧠 MENTAL   | {emoji} {cmd:12} [{bar}] {power:5.1f}%")
            
        elif isinstance(event, FacialExpressionEvent):
            self.stats["facial_expressions"] += 1
            expr = event.expression.name
            power = event.power * 100
            
            # Barra visual
            bar = "█" * int(power / 5) + "░" * (20 - int(power / 5))
            
            emojis = {
                "NEUTRAL": "😐", "BLINK": "😑", "WINK_LEFT": "😉",
                "WINK_RIGHT": "😜", "SURPRISE": "😲", "FROWN": "😠",
                "SMILE": "😊", "CLENCH": "😬", "LAUGH": "😄",
                "LOOK_LEFT": "👀⬅️", "LOOK_RIGHT": "👀➡️",
                "LOOK_UP": "👀⬆️", "LOOK_DOWN": "👀⬇️",
            }
            emoji = emojis.get(expr, "😀")
            
            print(f"[{timestamp}] 😀 FACIAL   | {emoji} {expr:12} [{bar}] {power:5.1f}%")
            
        elif isinstance(event, PerformanceMetricsEvent):
            self.stats["performance_metrics"] += 1
            
            # Mostrar métricas si cambiaron significativamente
            metrics_str = []
            if event.focus:
                metrics_str.append(f"Foco: {event.focus:.0%}")
            if event.engagement:
                metrics_str.append(f"Compromiso: {event.engagement:.0%}")
            if event.stress:
                metrics_str.append(f"Estrés: {event.stress:.0%}")
            if event.relaxation:
                metrics_str.append(f"Relajación: {event.relaxation:.0%}")
            
            if metrics_str:
                print(f"[{timestamp}] 📈 METRICS | {' | '.join(metrics_str)}")
            
        elif isinstance(event, DeviceInfoEvent):
            self.stats["device_info"] += 1
            if event.battery_level:
                self.last_battery = event.battery_level
                print(f"[{timestamp}] 🔋 DEVICE  | Batería: {event.battery_level}%")
            
        elif isinstance(event, PowerBandEvent):
            self.stats["power_bands"] += 1
            if self.show_power_bands:
                print(f"[{timestamp}] 📊 POWER   | {event.channel}: "
                      f"θ={event.theta:.2f} α={event.alpha:.2f} "
                      f"β={event.low_beta:.2f}/{event.high_beta:.2f} γ={event.gamma:.2f}")


def main():
    """
    Función principal para capturar todos los streams de Emotiv.
    """
    print("\n🔧 CONFIGURACIÓN DE CAPTURA MULTI-STREAM")
    print("=" * 50)
    
    # Verificar credenciales
    client_id = os.environ.get("EMOTIV_CLIENT_ID")
    client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERROR: Configura las variables de entorno:")
        print("   export EMOTIV_CLIENT_ID='tu_client_id'")
        print("   export EMOTIV_CLIENT_SECRET='tu_client_secret'")
        print("\n   Obtén tus credenciales en: https://www.emotiv.com/developer/")
        return
    
    # Permitir al usuario elegir los streams
    print("\n📡 STREAMS DISPONIBLES (sin licencia):")
    print("   [1] com - Comandos mentales (push, left, right, etc.)")
    print("   [2] fac - Expresiones faciales (smile, blink, wink, etc.)")
    print("   [3] met - Métricas de rendimiento (atención, estrés)")
    print("   [4] pow - Bandas de potencia (alpha, beta, theta)")
    print("   [5] dev - Info del dispositivo (batería, señal)")
    print("   [6] TODOS los streams")
    
    choice = input("\n¿Qué streams quieres capturar? [1-6, default=6]: ").strip() or "6"
    
    stream_options = {
        "1": ["com"],
        "2": ["fac"],
        "3": ["met"],
        "4": ["pow"],
        "5": ["dev"],
        "6": ["com", "fac", "met", "pow", "dev"],
    }
    
    streams = stream_options.get(choice, ["com", "fac", "met"])
    
    print(f"\n✅ Streams seleccionados: {streams}")
    
    # Crear credenciales y source
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    source = EmotivSource(
        credentials=credentials,
        streams=streams  # ¡Múltiples streams!
    )
    
    # Monitor personalizado
    show_pow = "pow" in streams
    monitor = MultiStreamMonitor(show_power_bands=show_pow)
    
    pipeline = BCIPipeline(
        source=source,
        publishers=[monitor]
    )
    
    print("\n🎧 Conectando con Emotiv Cortex...")
    print("   (Si es la primera vez, acepta el permiso en la app Cortex)")
    print("\n⌨️  Presiona Ctrl+C para detener\n")
    
    try:
        with pipeline:
            while True:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo captura...")


if __name__ == "__main__":
    main()
```

**Salida esperada con todos los streams:**

```
🔧 CONFIGURACIÓN DE CAPTURA MULTI-STREAM
==================================================

📡 STREAMS DISPONIBLES (sin licencia):
   [1] com - Comandos mentales (push, left, right, etc.)
   [2] fac - Expresiones faciales (smile, blink, wink, etc.)
   [3] met - Métricas de rendimiento (atención, estrés)
   [4] pow - Bandas de potencia (alpha, beta, theta)
   [5] dev - Info del dispositivo (batería, señal)
   [6] TODOS los streams

¿Qué streams quieres capturar? [1-6, default=6]: 6

✅ Streams seleccionados: ['com', 'fac', 'met', 'pow', 'dev']

🎧 Conectando con Emotiv Cortex...

======================================================================
🧠 MONITOR MULTI-STREAM DE EMOTIV - INICIADO
======================================================================
⏰ Inicio: 14:30:45
----------------------------------------------------------------------
📡 Streams activos: COM (mental), FAC (facial), MET (métricas)
----------------------------------------------------------------------

[14:30:46.123] ✅ CONECTADO: Connected to EPOC-X12345

[14:30:46.234] 🔋 DEVICE  | Batería: 85%
[14:30:46.345] 📈 METRICS | Foco: 45% | Compromiso: 62% | Relajación: 38%
[14:30:46.456] 🧠 MENTAL   | 😐 NEUTRAL      [████████████████░░░░] 82.5%
[14:30:46.567] 😀 FACIAL   | 😐 NEUTRAL      [████████████████████] 100.0%
[14:30:46.789] 😀 FACIAL   | 😑 BLINK        [████████████████████] 100.0%
[14:30:47.012] 🧠 MENTAL   | ⬅️ LEFT         [████████████████████] 95.2%
[14:30:47.234] 😀 FACIAL   | 😊 SMILE        [████████████░░░░░░░░] 65.3%
[14:30:47.456] 📈 METRICS | Foco: 78% | Compromiso: 71% | Estrés: 25%
[14:30:47.678] 😀 FACIAL   | 😉 WINK_LEFT    [████████████████████] 100.0%
...

🛑 Deteniendo captura...

======================================================================
📊 RESUMEN DE SESIÓN
======================================================================
🧠 Comandos mentales capturados: 156
😀 Expresiones faciales capturadas: 423
📈 Actualizaciones de métricas: 89
🔋 Último nivel de batería: 84%
======================================================================
```

### Ejemplo 10: Uso del CLI

```bash
# Ver ayuda
python -m bcipydummies --help

# Listar ventanas disponibles
python -m bcipydummies list-windows

# Ejecutar con fuente mock
python -m bcipydummies run --source mock --verbose

# Ejecutar con ventana específica
python -m bcipydummies run --source mock --window "Notepad" --verbose
```

---

## Resumen de Funciones Principales

### BCIPipeline

| Método | Descripción |
|--------|-------------|
| `start()` | Inicia el pipeline: conecta source, inicia publishers |
| `stop()` | Detiene el pipeline: desconecta source, detiene publishers |
| `add_processor(p)` | Añade un procesador a la cadena |
| `add_publisher(p)` | Añade un publicador |
| `remove_processor(p)` | Elimina un procesador |
| `remove_publisher(p)` | Elimina un publicador |
| `statistics` | Retorna diccionario con eventos recibidos/procesados/descartados |

### EEGSource

| Método | Descripción |
|--------|-------------|
| `connect()` | Conecta con el dispositivo EEG |
| `disconnect()` | Desconecta del dispositivo |
| `subscribe(callback)` | Registra función para recibir eventos |
| `unsubscribe(callback)` | Elimina función registrada |
| `is_connected` | True si está conectado |
| `source_id` | Identificador único de la fuente |

### Processor

| Método | Descripción |
|--------|-------------|
| `process(event)` | Procesa evento; retorna evento o None para filtrar |
| `reset()` | Reinicia estado interno |

### Publisher

| Método | Descripción |
|--------|-------------|
| `start()` | Inicializa recursos |
| `stop()` | Libera recursos |
| `publish(event)` | Publica un evento |
| `is_ready` | True si está listo |

---

## Troubleshooting

### Errores Comunes

**"Window not found"**
- El nombre de la ventana debe coincidir exactamente
- Usa `WindowsKeyboardPublisher.list_windows()` para ver nombres exactos

**"No headsets found"**
- Asegúrate de que Emotiv Cortex esté ejecutándose
- Verifica que el headset esté conectado en Cortex

**"Authentication failed"**
- Verifica tus credenciales (client_id, client_secret)
- Obtén credenciales en: https://www.emotiv.com/developer/

**Eventos no llegan al publisher**
- Revisa los umbrales (thresholds) - pueden estar filtrando todo
- Usa `ConsolePublisher` para debugging

---

## Contacto y Soporte

- **Issues**: https://github.com/itsvaalentine/BCIpyDummies/issues
- **Documentación**: https://github.com/itsvaalentine/BCIpyDummies/docs

---

*Documentación generada para BCIpyDummies v0.2.0*
