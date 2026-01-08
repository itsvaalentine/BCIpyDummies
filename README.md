# BCIpyDummies

**Middleware library to bridge Emotiv EEG headsets with Windows applications through mental commands.**

*For dummies 4 real*

[![CI](https://github.com/itsvaalentine/BCIpyDummies/actions/workflows/tests.yml/badge.svg)](https://github.com/itsvaalentine/BCIpyDummies/actions/workflows/tests.yml)

---

## Overview

BCIpyDummies acts as a translator between Emotiv Cortex API (via WebSocket) and Windows applications via keyboard input simulation. Train mental commands in the Emotiv app, then use them to control any Windows application.

**Current capabilities:**
- Connect to Emotiv headsets via Cortex API
- Process mental commands (left, right, lift)
- Simulate keyboard input to target Windows applications
- List available windows on the system

## Requirements

- **OS:** Windows 10/11
- **Python:** 3.9+
- **Hardware:** Emotiv EEG headset (EPOC X, EPOC+, Insight, etc.)
- **Software:** [Emotiv Cortex](https://www.emotiv.com/emotiv-cortex/) app installed and running

## Installation

```bash
# Clone the repository
git clone https://github.com/itsvaalentine/BCIpyDummies.git
cd BCIpyDummies

# Install in development mode
pip install -e .
```

## Configuration

### Emotiv API Credentials

You need Emotiv developer credentials. Get them at [emotiv.com/developer](https://www.emotiv.com/developer/).

**Set credentials via environment variables (recommended):**

```bash
export EMOTIV_CLIENT_ID="your_client_id"
export EMOTIV_CLIENT_SECRET="your_client_secret"
```

> **Security Note:** Never commit credentials to version control.

## Usage

### Basic Example

```python
from bcipydummies.emotiv_controller import EmotivController

# List available windows
windows = EmotivController.list_windows()
for window in windows:
    print(window)

# Connect to a specific window
controller = EmotivController("Your Target Window Name")
thread = controller.connect()

# The controller will now:
# - left command (80%+ power) -> 'A' key
# - right command -> 'D' key
# - lift command -> 'SPACE' key

# When done
controller.close()
```

### Mental Command Mapping

| Mental Command | Key | Power Threshold |
|---------------|-----|-----------------|
| `left` | A | 80% |
| `right` | D | 0% |
| `lift` | SPACE | 0% |

## Project Structure

```
bcipydummies/
├── __init__.py
└── emotiv_controller.py    # Main controller module

tests/
└── test_emotiv_controller.py
```

### Key Components

**EmotivController** (`emotiv_controller.py`):
- `__init__(window_name)` - Initialize and find target window
- `connect()` - Start WebSocket connection to Cortex API
- `close()` - Close the connection
- `list_windows()` - Static method to enumerate visible windows

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `websocket-client` | Cortex API communication |
| `pywin32` | Windows API (window management, keyboard simulation) |
| `pytest` | Testing framework |

## Known Limitations

- **Windows only** - Uses `win32gui` for window/keyboard control
- **Emotiv headsets only** - Currently no support for other EEG devices
- **Hardcoded key mappings** - Customization requires code changes

## Roadmap

- [ ] Configuration file support
- [ ] Cross-platform keyboard simulation
- [ ] CLI interface
- [ ] Additional EEG source adapters
- [ ] Configurable command mappings and thresholds

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

## License

See [LICENSE](LICENSE) for details.

---

**Note:** This project requires trained mental commands in the Emotiv app. For best results, spend time training neutral state and individual commands before using BCIpyDummies.
