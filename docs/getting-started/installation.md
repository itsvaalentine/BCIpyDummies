# Installation Guide

This guide walks you through installing BCIpyDummies and its dependencies.

## System Requirements

| Requirement | Details |
|------------|---------|
| **Operating System** | Windows 10 or Windows 11 |
| **Python** | 3.9 or higher |
| **Hardware** | Emotiv EEG headset (EPOC X, EPOC+, Insight) |
| **Software** | Emotiv Cortex app installed |

## Prerequisites

### 1. Python Installation

Ensure Python 3.9+ is installed:

```bash
python --version
```

If not installed, download from [python.org](https://www.python.org/downloads/).

### 2. Emotiv Cortex App

Download and install the Emotiv Cortex app:

1. Visit [emotiv.com/emotiv-cortex](https://www.emotiv.com/emotiv-cortex/)
2. Download the installer for Windows
3. Run the installer
4. Launch Cortex and sign in with your Emotiv account

### 3. Emotiv Developer Credentials

You need API credentials to connect to Cortex:

1. Go to [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Sign in or create an account
3. Create a new application
4. Copy your `Client ID` and `Client Secret`

## Installation Methods

### Development Install (Recommended)

Clone and install in editable mode:

```bash
# Clone the repository
git clone https://github.com/itsvaalentine/BCIpyDummies.git
cd BCIpyDummies

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .
```

### Dependencies Installed

The installation includes:

| Package | Purpose |
|---------|---------|
| `websocket-client` | WebSocket communication with Cortex API |
| `pywin32` | Windows API for keyboard simulation |

## Configuration

### Setting API Credentials

**Option 1: Environment Variables (Recommended)**

```bash
# Windows Command Prompt
set EMOTIV_CLIENT_ID=your_client_id
set EMOTIV_CLIENT_SECRET=your_client_secret

# Windows PowerShell
$env:EMOTIV_CLIENT_ID="your_client_id"
$env:EMOTIV_CLIENT_SECRET="your_client_secret"
```

**Option 2: Modify Source (Not Recommended)**

Edit `bcipydummies/emotiv_controller.py` directly. This is not recommended as credentials may be accidentally committed to version control.

## Verification

Verify the installation:

```python
python -c "from bcipydummies.emotiv_controller import EmotivController; print('Installation successful!')"
```

List available windows to confirm Win32 integration:

```python
from bcipydummies.emotiv_controller import EmotivController
windows = EmotivController.list_windows()
print(f"Found {len(windows)} windows")
```

## Troubleshooting

### Import Error: No module named 'win32gui'

The pywin32 package didn't install correctly:

```bash
pip uninstall pywin32
pip install pywin32
python -c "import win32gui; print('OK')"
```

### WebSocket Connection Refused

1. Ensure Emotiv Cortex app is running
2. Check that Cortex is listening on port 6868
3. Verify your firewall isn't blocking local connections

### Headset Not Detected

1. Ensure your Emotiv headset is paired with the Cortex app
2. Check USB dongle or Bluetooth connection
3. Verify headset battery level

## Next Steps

- [Quickstart Guide](quickstart.md) - Get running in 5 minutes
- [Emotiv Setup](../hardware/emotiv-setup.md) - Configure your headset
