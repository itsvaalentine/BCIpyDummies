# EmotivController API Reference

Complete API documentation for the `EmotivController` class.

## Module

```python
from bcipydummies.emotiv_controller import EmotivController
```

## Class: EmotivController

The main controller class that manages Emotiv headset connections and keyboard simulation.

### Constructor

```python
EmotivController(window_name: str)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `window_name` | `str` | Exact name of the target window |

**Raises:**

- `RuntimeError`: If the specified window is not found

**Behavior:**

1. Searches for a window matching `window_name`
2. Stores the window handle (`hwnd`)
3. Brings the window to the foreground
4. Initializes WebSocket connection parameters

**Example:**

```python
# Will raise RuntimeError if "Notepad" window doesn't exist
controller = EmotivController("Notepad")
```

### Static Methods

#### list_windows()

```python
@staticmethod
list_windows() -> List[str]
```

Enumerates all visible windows on the system.

**Returns:** List of window title strings

**Example:**

```python
windows = EmotivController.list_windows()
for window in windows:
    print(window)
```

**Notes:**

- Only returns windows that are visible
- Only returns windows with non-empty titles
- Uses Win32 `EnumWindows` API

### Instance Methods

#### connect()

```python
connect() -> threading.Thread
```

Establishes a WebSocket connection to the Emotiv Cortex API.

**Returns:** The background thread running the WebSocket connection

**Behavior:**

1. Creates WebSocket connection to `wss://127.0.0.1:6868`
2. Starts authentication flow
3. Creates session with connected headset
4. Subscribes to mental command stream
5. Begins processing commands

**Example:**

```python
controller = EmotivController("My App")
thread = controller.connect()

# Connection runs in background
# Main thread can continue
```

**Notes:**

- Returns immediately; connection happens asynchronously
- The returned thread is not a daemon thread
- Use `close()` to stop the connection

#### close()

```python
close() -> None
```

Closes the WebSocket connection.

**Behavior:**

1. Calls `ws_app.close()` to terminate the WebSocket
2. The background thread will exit

**Example:**

```python
controller.connect()
# ... use the controller ...
controller.close()
```

### Instance Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `window_name` | `str` | Name of the target window |
| `hwnd` | `int` | Win32 window handle |
| `cortex_token` | `str` | Authentication token (set after connect) |
| `headset_id` | `str` | Connected headset ID (set after connect) |
| `session_id` | `str` | Active session ID (set after connect) |
| `ws_app` | `WebSocketApp` | WebSocket application instance |
| `lastMove` | `str` | Last directional command ('A' or 'D') |

### Mental Command Processing

The controller processes these mental commands:

| Command | Power Threshold | Key Action |
|---------|----------------|------------|
| `left` | >= 0.80 | Press 'A' (50ms) |
| `right` | >= 0.00 | Press 'D' (200ms) |
| `lift` | >= 0.00 | Press 'SPACE' (450ms) + last direction (20ms) |

### Supported Virtual Key Codes

The controller supports these keys:

```python
VK_CODES = {
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'W': 0x57,
    'SPACE': 0x20
}
```

### Error Handling

The controller prints errors to stdout but does not raise exceptions during operation:

- WebSocket errors: Printed via `_on_error`
- Connection close: Logged via `_on_close`
- Invalid keys: Warning printed, operation skipped

### Thread Safety

- The controller uses a single background thread for WebSocket operations
- Keyboard simulation happens on the WebSocket thread
- Window handle is stored at construction time
- No locks are used; avoid modifying controller state from multiple threads

## Complete Example

```python
from bcipydummies.emotiv_controller import EmotivController
import time
import signal
import sys

def main():
    # Setup
    controller = EmotivController("Target Application")

    # Graceful shutdown handler
    def shutdown(sig, frame):
        print("Shutting down...")
        controller.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Connect and run
    thread = controller.connect()
    print(f"Connected to window: {controller.window_name}")
    print(f"Window handle: {controller.hwnd}")

    # Keep running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
```

## Known Limitations

1. **Windows Only**: Uses `win32gui` and `win32con`
2. **Hardcoded Thresholds**: Power thresholds cannot be configured
3. **Limited Keys**: Only 5 keys are supported
4. **No Reconnection**: Connection failures require restart
5. **Placeholder Credentials**: Default credentials in source must be replaced

## Related

- [Installation Guide](../getting-started/installation.md)
- [Quickstart](../getting-started/quickstart.md)
- [Architecture](../architecture/system-design.md)
