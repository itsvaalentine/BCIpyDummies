# System Architecture

This document describes the architecture of BCIpyDummies and its planned evolution.

## Current Architecture (v0.1.0)

### Overview

BCIpyDummies currently follows a monolithic design with all functionality in a single class:

```
┌─────────────────────────────────────────────────────────────┐
│                     EmotivController                         │
├─────────────────────────────────────────────────────────────┤
│  • WebSocket communication                                   │
│  • Emotiv Cortex protocol (auth, session, subscribe)        │
│  • Mental command processing                                 │
│  • Window management                                         │
│  • Keyboard simulation                                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Emotiv Headset
      │
      ▼
Emotiv Cortex App (wss://127.0.0.1:6868)
      │
      ▼ WebSocket
┌─────────────────────┐
│  EmotivController   │
│  ┌───────────────┐  │
│  │ _on_message() │  │  Receive mental command
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │_process_cmd() │  │  Apply power threshold
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │  _control()   │  │  Map command to key
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │ _press_key()  │  │  Simulate keypress
│  └───────────────┘  │
└─────────┬───────────┘
          │
          ▼ Win32 API
   Target Window
```

### Authentication Flow

The Cortex API uses a sequential authentication flow:

```
┌──────────────┐          ┌──────────────┐
│    Client    │          │    Cortex    │
└──────┬───────┘          └──────┬───────┘
       │                         │
       │──── authorize ─────────▶│
       │     (id=1)              │
       │◀─── cortexToken ────────│
       │                         │
       │──── queryHeadsets ─────▶│
       │     (id=2)              │
       │◀─── headset list ───────│
       │                         │
       │──── createSession ─────▶│
       │     (id=3)              │
       │◀─── session id ─────────│
       │                         │
       │──── subscribe ─────────▶│
       │     (id=4, "com")       │
       │◀─── streaming data ─────│
       │                         │
```

### Current Limitations

1. **Tight Coupling**: Cannot swap EEG source or output method
2. **Windows Only**: Hard dependency on `win32gui`
3. **No Configuration**: Hardcoded thresholds and key mappings
4. **Limited Error Handling**: Errors logged but not propagated
5. **Single Threaded Processing**: Can cause message backlog

---

## Planned Architecture (v0.2.0+)

### Design Principles

- **Separation of Concerns**: Each component has a single responsibility
- **Dependency Inversion**: Depend on abstractions, not concretions
- **Open/Closed**: Extend via new implementations, not modification
- **Testability**: All components mockable for unit testing

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           BCIPipeline                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Sources   │───▶│ Processors  │───▶│      Publishers         │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│                                                                      │
│  • EmotivSource      • ThresholdProc    • KeyboardPublisher        │
│  • MockSource        • DebounceProc     • ConsolePublisher         │
│  • FileSource        • MapperProc       • WebSocketPublisher       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Interfaces

**EEGSource** (Input Adapter):
```python
class EEGSource(ABC):
    def connect(self) -> None
    def disconnect(self) -> None
    def subscribe(callback: Callable[[EEGEvent], None]) -> None
    def is_connected -> bool
```

**Processor** (Transform/Filter):
```python
class Processor(ABC):
    def process(event: EEGEvent) -> Optional[EEGEvent]
    def reset() -> None
```

**Publisher** (Output Adapter):
```python
class Publisher(ABC):
    def publish(event: EEGEvent) -> None
    def start() -> None
    def stop() -> None
```

### Event Types

```python
@dataclass
class MentalCommandEvent:
    timestamp: float
    source_id: str
    command: MentalCommand  # Enum: LEFT, RIGHT, LIFT, etc.
    power: float  # 0.0 to 1.0
```

### Proposed Module Structure

```
bcipydummies/
├── core/
│   ├── engine.py           # BCIPipeline orchestrator
│   ├── events.py           # Event data classes
│   └── config.py           # Configuration management
│
├── sources/
│   ├── base.py             # EEGSource protocol
│   ├── emotiv/
│   │   ├── cortex_client.py
│   │   └── auth.py
│   └── mock.py             # Testing source
│
├── processors/
│   ├── base.py             # Processor protocol
│   ├── threshold.py        # Power threshold filter
│   └── mapper.py           # Command to action mapper
│
├── publishers/
│   ├── base.py             # Publisher protocol
│   ├── keyboard/
│   │   ├── windows.py
│   │   └── base.py
│   └── console.py          # Debug output
│
└── cli/
    └── main.py             # Command-line interface
```

### Configuration System

YAML-based configuration:

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
    target_window: "My Game"
```

### Benefits of New Architecture

| Aspect | Current | Planned |
|--------|---------|---------|
| **Testing** | Requires Emotiv hardware | Mock everything |
| **Platforms** | Windows only | Pluggable keyboard adapters |
| **Sources** | Emotiv only | Add sources via interface |
| **Config** | Hardcoded | File + CLI + env vars |
| **Debugging** | Print statements | Console publisher + logging |

## Migration Path

1. **Phase 1**: Add abstractions without breaking existing API
2. **Phase 2**: Extract components from EmotivController
3. **Phase 3**: Wire components through BCIPipeline
4. **Phase 4**: Deprecate EmotivController
5. **Phase 5**: Remove EmotivController in v1.0

## Related

- [API Reference](../api/emotiv-controller.md)
- [Cortex Protocol](cortex-protocol.md)
- [Contributing Guide](../contributing/index.md)
