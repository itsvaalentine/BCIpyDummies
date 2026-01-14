# Quickstart Guide

Get BCIpyDummies running in 5 minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.9+ installed
- [ ] BCIpyDummies installed (`pip install -e .`)
- [ ] Emotiv Cortex app running
- [ ] Emotiv headset connected to Cortex
- [ ] Mental commands trained in EmotivBCI app
- [ ] API credentials set as environment variables

## Step 1: Find Your Target Window

First, identify the exact name of the window you want to control:

```python
from bcipydummies.emotiv_controller import EmotivController

# List all visible windows
windows = EmotivController.list_windows()

for window in windows:
    print(window)
```

Example output:
```
Google Chrome
Visual Studio Code
Notepad
...
```

Copy the exact window name you want to control.

## Step 2: Create the Controller

```python
from bcipydummies.emotiv_controller import EmotivController

# Replace with your actual window name
controller = EmotivController("Notepad")
```

This will:
1. Find the window by name
2. Bring it to the foreground
3. Prepare for keyboard simulation

## Step 3: Connect to Emotiv

```python
# Start the connection (runs in background thread)
thread = controller.connect()

print("Connected! Use mental commands to control the window.")
print("Press Ctrl+C to stop.")
```

## Step 4: Use Mental Commands

Once connected, your trained mental commands will trigger keyboard inputs:

| Mental Command | Keyboard Action |
|---------------|-----------------|
| `left` (80%+ power) | Press 'A' key |
| `right` | Press 'D' key (held 200ms) |
| `lift` | Press 'SPACE' + last direction |

## Step 5: Clean Up

When you're done:

```python
controller.close()
```

## Complete Example

```python
from bcipydummies.emotiv_controller import EmotivController
import time

def main():
    # Find available windows
    print("Available windows:")
    for window in EmotivController.list_windows()[:10]:
        print(f"  - {window}")

    # Connect to target window
    window_name = input("\nEnter window name: ")
    controller = EmotivController(window_name)

    print(f"\nConnecting to '{window_name}'...")
    thread = controller.connect()

    print("Connected! Mental commands are now active.")
    print("Commands: left->A, right->D, lift->SPACE")
    print("Press Ctrl+C to stop.\n")

    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        controller.close()
        print("Done!")

if __name__ == "__main__":
    main()
```

## What's Happening

1. **WebSocket Connection**: BCIpyDummies connects to Emotiv Cortex on `wss://127.0.0.1:6868`
2. **Authentication**: Exchanges credentials for a session token
3. **Session Creation**: Creates a session with your connected headset
4. **Stream Subscription**: Subscribes to the `com` (mental command) stream
5. **Command Processing**: When commands arrive, they're translated to key presses

## Troubleshooting

### "Window not found"

The window name must match exactly (case-sensitive). Use `list_windows()` to see exact names.

### No Commands Detected

1. Check Emotiv Cortex shows "Streaming" status
2. Verify mental commands are trained in EmotivBCI
3. Ensure headset contact quality is good (green indicators)

### Commands Fire Too Often/Rarely

The current power thresholds are:
- `left`: 80% (only fires with strong signal)
- `right`: 0% (fires easily)
- `lift`: 0% (fires easily)

These are hardcoded in the current version. Customization requires modifying `emotiv_controller.py`.

## Next Steps

- [Emotiv Setup Guide](../hardware/emotiv-setup.md) - Optimize your headset configuration
- [API Reference](../api/emotiv-controller.md) - Full method documentation
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions
