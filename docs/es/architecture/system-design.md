# Arquitectura del Sistema

Este documento describe la arquitectura de BCIpyDummies y su evolución planificada.

## Arquitectura Actual (v0.1.0)

### Vista General

BCIpyDummies actualmente sigue un diseño monolítico con toda la funcionalidad en una sola clase:

```
┌─────────────────────────────────────────────────────────────┐
│                     EmotivController                         │
├─────────────────────────────────────────────────────────────┤
│  • Comunicación WebSocket                                    │
│  • Protocolo Emotiv Cortex (auth, session, subscribe)       │
│  • Procesamiento de comandos mentales                        │
│  • Gestión de ventanas                                       │
│  • Simulación de teclado                                     │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
Headset Emotiv
      │
      ▼
App Emotiv Cortex (wss://127.0.0.1:6868)
      │
      ▼ WebSocket
┌─────────────────────┐
│  EmotivController   │
│  ┌───────────────┐  │
│  │ _on_message() │  │  Recibir comando mental
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │_process_cmd() │  │  Aplicar umbral de potencia
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │  _control()   │  │  Mapear comando a tecla
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │ _press_key()  │  │  Simular pulsación de tecla
│  └───────────────┘  │
└─────────┬───────────┘
          │
          ▼ API Win32
   Ventana Objetivo
```

### Flujo de Autenticación

La API Cortex usa un flujo de autenticación secuencial:

```
┌──────────────┐          ┌──────────────┐
│   Cliente    │          │    Cortex    │
└──────┬───────┘          └──────┬───────┘
       │                         │
       │──── authorize ─────────▶│
       │     (id=1)              │
       │◀─── cortexToken ────────│
       │                         │
       │──── queryHeadsets ─────▶│
       │     (id=2)              │
       │◀─── lista headsets ─────│
       │                         │
       │──── createSession ─────▶│
       │     (id=3)              │
       │◀─── session id ─────────│
       │                         │
       │──── subscribe ─────────▶│
       │     (id=4, "com")       │
       │◀─── datos streaming ────│
       │                         │
```

### Limitaciones Actuales

1. **Acoplamiento Fuerte**: No se puede intercambiar fuente EEG o método de salida
2. **Solo Windows**: Dependencia dura de `win32gui`
3. **Sin Configuración**: Umbrales y mapeos de teclas hardcodeados
4. **Manejo de Errores Limitado**:  Errores registrados pero no propagados
5. **Procesamiento de Hilo Único**:  Puede causar acumulación de mensajes

---

## Arquitectura Planificada (v0.2.0+)

### Principios de Diseño

- **Separación de Responsabilidades**:  Cada componente tiene una única responsabilidad
- **Inversión de Dependencias**: Depender de abstracciones, no de concreciones
- **Abierto/Cerrado**: Extender vía nuevas implementaciones, no modificación
- **Testabilidad**: Todos los componentes pueden ser mockeados para pruebas unitarias

### Vista General de Componentes

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           BCIPipeline                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐  │
│  │   Sources   │───▶│ Processors  │───▶│      Publishers             │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────────┘  │
│                                                                          │
│  • EmotivSource      • ThresholdProc    • KeyboardPublisher             │
│  • MockSource        • DebounceProc     • ConsolePublisher              │
│  • FileSource        • MapperProc       • WebSocketPublisher            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Interfaces Core

**EEGSource** (Adaptador de Entrada):
```python
class EEGSource(ABC):
    def connect(self) -> None
    def disconnect(self) -> None
    def subscribe(callback: Callable[[EEGEvent], None]) -> None
    def is_connected -> bool
```

**Processor** (Transformar/Filtrar):
```python
class Processor(ABC):
    def process(event: EEGEvent) -> Optional[EEGEvent]
    def reset() -> None
```

**Publisher** (Adaptador de Salida):
```python
class Publisher(ABC):
    def publish(event: EEGEvent) -> None
    def start() -> None
    def stop() -> None
```

### Tipos de Eventos

```python
@dataclass
class MentalCommandEvent: 
    timestamp: float
    source_id: str
    command: MentalCommand  # Enum:  LEFT, RIGHT, LIFT, etc.
    power: float  # 0.0 a 1.0
```

### Estructura de Módulos Propuesta

```
bcipydummies/
├── core/
│   ├── engine.py           # Orquestador BCIPipeline
│   ├── events.py           # Clases de datos de eventos
│   └── config.py           # Gestión de configuración
│
├── sources/
│   ├── base.py             # Protocolo EEGSource
│   ├── emotiv/
│   │   ├── cortex_client.py
│   │   └── auth.py
│   └── mock. py             # Fuente para pruebas
│
├── processors/
│   ├── base.py             # Protocolo Processor
│   ├── threshold.py        # Filtro de umbral de potencia
│   └── mapper.py           # Mapeador de comando a acción
│
├── publishers/
│   ├── base. py             # Protocolo Publisher
│   ├── keyboard/
│   │   ├── windows.py
│   │   └── base.py
│   └── console. py          # Salida de debug
│
└── cli/
    └── main.py             # Interfaz de línea de comandos
```

### Sistema de Configuración

Configuración basada en YAML: 

```yaml
source:
  type: emotiv
  client_id: ${EMOTIV_CLIENT_ID}
  client_secret: ${EMOTIV_CLIENT_SECRET}

processors:
  - type: threshold
    thresholds:
      left: 0.80
      right: 0.00

  - type: mapper
    mappings:
      left: A
      right: D
      lift: SPACE

publishers:
  - type: keyboard
    target_window: "Mi Juego"
```

### Beneficios de la Nueva Arquitectura

| Aspecto | Actual | Planificado |
|---------|--------|-------------|
| **Pruebas** | Requiere hardware Emotiv | Mockear todo |
| **Plataformas** | Solo Windows | Adaptadores de teclado intercambiables |
| **Fuentes** | Solo Emotiv | Agregar fuentes vía interfaz |
| **Config** | Hardcodeado | Archivo + CLI + variables de entorno |
| **Debugging** | Sentencias print | Publisher de consola + logging |

## Ruta de Migración

1. **Fase 1**: Agregar abstracciones sin romper API existente
2. **Fase 2**: Extraer componentes de EmotivController
3. **Fase 3**: Conectar componentes a través de BCIPipeline
4. **Fase 4**: Deprecar EmotivController
5. **Fase 5**: Eliminar EmotivController en v1.0

## Relacionado

- [Referencia API](../api/emotiv-controller.md)
- [Protocolo Cortex](cortex-protocol.md)
- [Guía de Contribución](../contributing/index.md)