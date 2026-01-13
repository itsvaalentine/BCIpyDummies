# 🧠 BCIpyDummies Complete Architecture

This guide will help you understand the project structure, how each part communicates, and what each function does so you can use and test this library. 

## 📋 Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Main Components](#main-components)
4. [Data Flow](#data-flow)
5. [Component Communication](#component-communication)
6. [Usage and Testing Guide](#usage-and-testing-guide)

> 💡 **Looking for code examples? ** Check out the [Examples Guide](../examples/examples.md) for practical usage patterns. 

---

## Overview

BCIpyDummies is a **middleware** that acts as a translator between Emotiv EEG devices and Windows applications. The library captures mental commands from the Emotiv headset and translates them into keyboard inputs for any Windows application.

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              BCIPipeline (Orchestrator)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐  │
│  │    SOURCES     │───▶│   PROCESSORS     │───▶│     PUBLISHERS          │  │
│  │    (Input)     │    │  (Processing)    │    │     (Output)            │  │
│  └────────────────┘    └──────────────────┘    └─────────────────────────┘  │
│                                                                              │
│  • EmotivSource       • ThresholdProcessor    • KeyboardPublisher           │
│  • MockSource         • DebounceProcessor     • ConsolePublisher            │
│                       • CommandMapper                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
bcipydummies/
├── __init__.py              # Entry point, exports all public classes
├── __main__.py              # Allows running:  python -m bcipydummies
├── emotiv_controller.py     # Legacy controller (old, simple version)
│
├── core/                    # System core
│   ├── __init__.py
│   ├── config.py            # Configuration (ThresholdConfig, KeyboardConfig, etc.)
│   ├── engine.py            # BCIPipeline - Main orchestrator
│   ├── events.py            # Event types (MentalCommandEvent, etc.)
│   ├── exceptions.py        # Custom exceptions
│   └── factory.py           # Factory functions to create components
│
├── sources/                 # EEG data sources
│   ├── __init__.py
│   ├── base.py              # EEGSource protocol/interface
│   ├── mock.py              # Simulated source for testing
│   └── emotiv/              # Emotiv implementation
│       ├── __init__.py
│       ├── cortex_client.py # WebSocket client for Cortex API
│       └── source. py        # EmotivSource
│
├── processors/              # Event processors
│   ├── __init__.py
│   ├── base.py              # Processor interface
│   ├── threshold. py         # Power threshold filter
│   ├── debounce.py          # Prevents rapid repeated commands
│   └── mapper.py            # Maps commands to actions
│
├── publishers/              # Output publishers
│   ├── __init__.py
│   ├── base. py              # Publisher interface
│   ├── console.py           # Prints to console (debugging)
│   └── keyboard/            # Keyboard simulation
│       ├── __init__.py
│       ├── base.py          # Base KeyboardPublisher
│       └── windows.py       # Windows implementation
│
└── cli/                     # Command-line interface
    ├── __init__.py
    ├── main.py              # CLI entry point
    └── commands/            # Available commands
```

---

## Main Components

### 1. 🔌 Sources (Data Sources)

**Sources** are responsible for capturing EEG data and converting them into events. 

#### `EEGSource` (Base Protocol)
```python
# Location: bcipydummies/sources/base.py

class EEGSource(Protocol):
    """Interface that all sources must implement."""
    
    @property
    def source_id(self) -> str:
        """Unique identifier for the source."""
        
    @property
    def is_connected(self) -> bool:
        """True if connected and transmitting."""
        
    def connect(self) -> None:
        """Establishes connection with the EEG device."""
        
    def disconnect(self) -> None:
        """Disconnects from the EEG device."""
        
    def subscribe(self, callback: EventCallback) -> None:
        """Registers a callback to receive events."""
        
    def unsubscribe(self, callback: EventCallback) -> None:
        """Removes a registered callback."""
```

#### `EmotivSource` (Emotiv Implementation)
```python
# Location: bcipydummies/sources/emotiv/source.py

class EmotivSource(BaseEEGSource):
    """
    EEG source for Emotiv devices via Cortex API.
    
    Available streams (without license):
    - "com":  Mental commands (push, pull, left, right, lift, etc.)
    - "fac": Facial expressions (blink, smile, frown, wink, etc.)
    - "met": Performance metrics (attention, stress, relaxation)
    - "pow": Power bands (theta, alpha, beta, gamma)
    - "dev": Device info (battery, signal quality)
    - "sys": System events
    
    Connection flow:
    1. Connects via WebSocket to wss://localhost:6868
    2. Requests access (shows popup in Cortex if not approved)
    3. Authenticates with client_id and client_secret
    4. Searches for available headsets
    5. Creates session with the headset
    6. Subscribes to configured streams
    
    Example with multiple streams:
        source = EmotivSource(
            credentials=credentials,
            streams=["com", "fac", "met"]  # Commands, facial, metrics
        )
    """
```

#### `MockSource` (For Testing)
```python
# Location: bcipydummies/sources/mock.py

class MockSource(BaseEEGSource):
    """
    Simulated source for development and testing.
    
    Two operation modes:
    - Random: generates random commands periodically
    - Scripted: replays a predefined sequence of events
    """
```

### 2. ⚙️ Processors

**Processors** transform and filter events in a sequential chain.

#### `Processor` (Base Interface)
```python
# Location: bcipydummies/processors/base.py

class Processor(ABC):
    """
    Base interface for processors.
    
    Each processor receives an event and can: 
    - Pass it unchanged
    - Transform it
    - Filter it (returns None)
    """
    
    @abstractmethod
    def process(self, event: EEGEvent) -> Optional[EEGEvent]: 
        """Processes an event.  Returns None to filter."""
        
    @abstractmethod
    def reset(self) -> None:
        """Resets the processor's internal state."""
```

#### `ThresholdProcessor` (Threshold Filter)
```python
# Location: bcipydummies/processors/threshold.py

class ThresholdProcessor(Processor):
    """
    Filters events below the configured power threshold.
    
    Example: 
        processor = ThresholdProcessor(thresholds={"left": 0.8})
        # Only 'left' events with power >= 80% pass through
    """
```

#### `DebounceProcessor` (Anti-bounce)
```python
# Location: bcipydummies/processors/debounce.py

class DebounceProcessor(Processor):
    """
    Prevents repeated commands within a time period (cooldown).
    
    Example:
        processor = DebounceProcessor(cooldown=0.3)
        # Ignores the same command if it arrives before 300ms
    """
```

#### `CommandMapper` (Command Mapping)
```python
# Location: bcipydummies/processors/mapper.py

class CommandMapper(Processor):
    """
    Maps mental commands to actions (keys).
    
    Example:
        mapper = CommandMapper(mapping={
            "left": "A",
            "right": "D",
            "lift": "SPACE"
        })
    """
```

### 3. 📤 Publishers

**Publishers** receive processed events and execute actions.

#### `Publisher` (Base Interface)
```python
# Location: bcipydummies/publishers/base.py

class Publisher(ABC):
    """
    Base interface for publishers.
    
    Lifecycle:
    1. start() - Initializes resources
    2. publish(event) - Processes events
    3. stop() - Releases resources
    """
    
    @abstractmethod
    def publish(self, event: EEGEvent) -> None:
        """Publishes an EEG event."""
        
    @abstractmethod
    def start(self) -> None:
        """Initializes the publisher."""
        
    @abstractmethod
    def stop(self) -> None:
        """Stops the publisher."""
        
    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """True if ready to receive events."""
```

#### `ConsolePublisher` (Console Output)
```python
# Location: bcipydummies/publishers/console.py

class ConsolePublisher(Publisher):
    """
    Prints events to the console.
    Useful for debugging and development.
    """
```

#### `WindowsKeyboardPublisher` (Windows Keyboard)
```python
# Location: bcipydummies/publishers/keyboard/windows.py

class WindowsKeyboardPublisher: 
    """
    Simulates keyboard presses on Windows.
    
    Uses the win32 API to send keyboard events
    to a specific window. 
    """
```

### 4. 🎛️ BCIPipeline (Orchestrator)

```python
# Location: bcipydummies/core/engine.py

class BCIPipeline:
    """
    Central orchestrator that connects Source -> Processors -> Publishers.
    
    Features:
    - Thread-safe via locks
    - Manages component lifecycle
    - Processed event statistics
    - Supports context manager (with)
    """
```

### 5. 📊 Events

```python
# Location: bcipydummies/core/events.py

class MentalCommand(Enum):
    """
    Supported mental commands: 
    NEUTRAL, PUSH, PULL, LIFT, DROP,
    LEFT, RIGHT, ROTATE_LEFT, ROTATE_RIGHT, DISAPPEAR
    """

class FacialExpression(Enum):
    """
    Supported facial expressions:
    NEUTRAL, BLINK, WINK_LEFT, WINK_RIGHT, SURPRISE, FROWN,
    SMILE, CLENCH, LAUGH, SMIRK_LEFT, SMIRK_RIGHT,
    LOOK_LEFT, LOOK_RIGHT, LOOK_UP, LOOK_DOWN
    """

class EmotivStream(Enum):
    """
    Available data streams:
    COM (commands), FAC (facial), MET (metrics), 
    POW (power), DEV (device), SYS (system)
    """

@dataclass(frozen=True)
class MentalCommandEvent(EEGEvent):
    """
    Mental command event.
    
    Attributes:
    - timestamp: Event moment
    - source_id: Source ID
    - command: Command type (MentalCommand)
    - power: Power/confidence (0.0 - 1.0)
    - action:  Mapped action (optional)
    """

@dataclass(frozen=True)
class FacialExpressionEvent(EEGEvent):
    """
    Facial expression event.
    
    Attributes:
    - timestamp: Event moment
    - source_id: Source ID
    - expression: Expression type (FacialExpression)
    - power: Power/confidence (0.0 - 1.0)
    """

@dataclass(frozen=True)
class PerformanceMetricsEvent(EEGEvent):
    """
    Performance metrics event.
    
    Attributes:
    - focus:  Focus/attention level (0.0 - 1.0)
    - engagement: Engagement level (0.0 - 1.0)
    - excitement: Excitement level (0.0 - 1.0)
    - long_excitement: Long-term excitement (0.0 - 1.0)
    - stress: Stress level (0.0 - 1.0)
    - relaxation: Relaxation level (0.0 - 1.0)
    - interest: Interest level (0.0 - 1.0)
    """

@dataclass(frozen=True)
class DeviceInfoEvent(EEGEvent):
    """
    Device information event.
    
    Attributes:
    - battery_level: Battery level (0-100%)
    - signal_quality: Signal quality (0.0 - 1.0)
    - contact_quality: Quality per channel (dict)
    """
```

---

## Data Flow

### Complete Flow Diagram

```
┌──────────────────┐
│  Emotiv Headset  │ (EEG Hardware)
└────────┬─────────┘
         │ Bluetooth/USB
         ▼
┌──────────────────┐
│ Emotiv Cortex App│ (Emotiv Software)
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
│        command:  LEFT, │  └──────────┘  └──────────┘  │     │ │
│        power: 0.85    │                              │     │ │
│      }                │  ┌──────────┐                │     │ │
│                   ────┼─▶│Command   │◀───────────────┘     �� │
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
                    │ Target Application│ (Game, Notepad, etc.)
                    └──────────────────┘
```

### Emotiv Authentication Flow

```
┌──────────────┐                    ┌──────────────┐
│    Client    │                    │  Cortex API  │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │──── 1. authorize() ──────────────▶│
       │      {clientId, clientSecret}     │
       │◀─── cortexToken ─────────────────│
       │                                   │
       │──── 2. queryHeadsets() ─────────▶│
       │◀─── headset list ────────────────│
       │                                   │
       │──── 3. createSession() ─────────▶│
       │      {headsetId}                  │
       │◀─── sessionId ───────────────────│
       │                                   │
       │──── 4. subscribe() ─────────────▶│
       │      {streams:  ["com"]}           │
       │◀─── streaming data ──────────────│
       │                                   │
```

---

## Component Communication

### 1. Observer Pattern (Source → Pipeline)

The source emits events through registered callbacks:

```python
# The Pipeline subscribes to the source
source.subscribe(callback=self._on_event)

# When an event arrives, the source emits it
def _emit(self, event: EEGEvent) -> None:
    for callback in self._subscribers:
        callback(event)
```

### 2. Chain of Responsibility Pattern (Processors)

Processors execute in sequence: 

```python
# In BCIPipeline._on_event():
current_event = event
for processor in self._processors:
    if current_event is None:
        break  # Event filtered
    current_event = processor.process(current_event)
```

### 3. Fan-out Pattern (Pipeline → Publishers)

The processed event is sent to all publishers:

```python
# In BCIPipeline._on_event():
for publisher in self._publishers:
    if publisher.is_ready:
        publisher.publish(current_event)
```

---

## Usage and Testing Guide

### Installation

```bash
# Clone the repository
git clone https://github.com/itsvaalentine/BCIpyDummies.git
cd BCIpyDummies

# Install in development mode
pip install -e . 

# Install development dependencies (for tests)
pip install -e ".[dev]"
```

### Credential Configuration

```bash
# Environment variables (recommended)
export EMOTIV_CLIENT_ID="your_client_id"
export EMOTIV_CLIENT_SECRET="your_client_secret"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_core.py -v
pytest tests/test_processors.py -v
pytest tests/test_sources.py -v
pytest tests/test_publishers.py -v
```

---

## Related Documentation

- **[Getting Started](../getting-started/index.md)** - Installation and quickstart
- **[API Reference](../api/emotiv-controller.md)** - EmotivController documentation
- **[System Design](../architecture/system-design.md)** - Architecture evolution
- **[Hardware Setup](../hardware/emotiv-setup.md)** - Emotiv headset configuration

---

*For practical code examples, see the [Examples Guide](../examples/examples.md).*