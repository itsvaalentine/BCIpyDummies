# BCIpyDummies Documentation

**Middleware library to bridge Emotiv EEG headsets with Windows applications through mental commands.**

## What is BCIpyDummies?

BCIpyDummies acts as a translator between your brain and your computer. It connects to Emotiv EEG headsets via the Cortex API and converts mental commands into keyboard inputs for any Windows application.

**Use cases:**
- Control games with your mind
- Hands-free application control
- BCI research and experimentation
- Accessibility solutions

## Quick Links

| Section | Description |
|---------|-------------|
| [Installation](getting-started/installation.md) | System requirements and setup |
| [Quickstart](getting-started/quickstart.md) | Get running in 5 minutes |
| [Emotiv Setup](hardware/emotiv-setup.md) | Hardware configuration guide |
| [API Reference](api/emotiv-controller.md) | Class and method documentation |
| [Architecture](architecture/system-design.md) | System design overview |

## Current Features

- WebSocket connection to Emotiv Cortex API
- Mental command processing (left, right, lift)
- Keyboard simulation to target Windows applications
- Window enumeration utility

## Requirements

- Windows 10/11
- Python 3.9+
- Emotiv EEG headset
- Emotiv Cortex app

## Getting Started

```python
from bcipydummies.emotiv_controller import EmotivController

# Find your target window
windows = EmotivController.list_windows()
print(windows)

# Start controlling
controller = EmotivController("Your Window Name")
controller.connect()
```

## Project Status

BCIpyDummies is in active development (v0.1.0). Current focus:
- Documentation improvements
- Architecture refactoring for extensibility
- Cross-platform support planning

## Contributing

We welcome contributions! See our [Contributing Guide](contributing/index.md) for details.

## Support

- [GitHub Issues](https://github.com/itsvaalentine/BCIpyDummies/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/itsvaalentine/BCIpyDummies/discussions) - Questions and community
