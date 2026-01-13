# 🧪 Practical Examples

This guide contains practical code examples for using BCIpyDummies.  Each example is self-contained and can be run independently.

## 📋 Table of Contents

1. [Example 1: Basic Usage with MockSource](#example-1-basic-usage-with-mocksource-no-hardware)
2. [Example 2: Complete Pipeline with Processors](#example-2-complete-pipeline-with-processors)
3. [Example 3: Scripted Event Sequence](#example-3-scripted-event-sequence)
4. [Example 4: Custom Publisher](#example-4-create-a-custom-publisher)
5. [Example 5: Custom Processor](#example-5-create-a-custom-processor)
6. [Example 6: Factory Configuration](#example-6-using-factory-simplified-configuration)
7. [Example 7: Real Window Control](#example-7-real-window-control-windows)
8. [Example 8: Real Emotiv Hardware](#example-8-usage-with-real-emotiv-hardware)

> 💡 **New to BCIpyDummies? ** Start with the [Deep Dive Guide](deep-dive. md) to understand the architecture first. 

---

## Example 1: Basic Usage with MockSource (No Hardware)

```python
"""
This example works without Emotiv hardware.
Perfect for testing the library. 
"""
import time
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher
from bcipydummies.core. events import MentalCommand

# Create simulated source that generates random events
source = MockSource(
    source_id="test-source",
    random_interval=1.0,  # One event per second
    random_commands=[
        MentalCommand.LEFT,
        MentalCommand. RIGHT,
        MentalCommand.PUSH,
        MentalCommand. NEUTRAL,
    ]
)

# Create console publisher
console = ConsolePublisher(prefix="[BCI]")

# Create and run the pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[console]
)

# Use as context manager
with pipeline:
    print("Pipeline started.  Press Ctrl+C to stop.")
    try:
        time.sleep(10)  # Run for 10 seconds
    except KeyboardInterrupt:
        pass

print("Pipeline stopped.")
print(f"Statistics: {pipeline.statistics}")
```

---

## Example 2: Complete Pipeline with Processors

```python
"""
Example with processor chain. 
"""
from bcipydummies import (
    BCIPipeline,
    MockSource,
    ConsolePublisher,
    ThresholdProcessor,
    DebounceProcessor,
    CommandMapper
)

# Simulated source
source = MockSource()

# Processor chain
processors = [
    # 1. Filter by power threshold
    ThresholdProcessor(
        thresholds={
            "left": 0.7,   # Only left with 70%+ power
            "right": 0.6,  # Only right with 60%+ power
        },
        default_threshold=0.5
    ),
    
    # 2. Prevent repeated commands
    DebounceProcessor(cooldown=0.3),  # 300ms between commands
    
    # 3. Map commands to keys
    CommandMapper(
        mapping={
            "left": "A",
            "right": "D",
            "push": "W",
            "lift": "SPACE"
        }
    )
]

# Publishers
publishers = [ConsolePublisher(prefix="[EVENT]")]

# Create pipeline
pipeline = BCIPipeline(
    source=source,
    processors=processors,
    publishers=publishers
)

# Run
with pipeline:
    import time
    time.sleep(30)
```

---

## Example 3: Scripted Event Sequence

```python
"""
Example with predefined event sequence. 
Useful for reproducible tests.
"""
from bcipydummies. sources. mock import MockSource, ScriptedEvent, create_test_script
from bcipydummies.core.events import MentalCommand
from bcipydummies import BCIPipeline, ConsolePublisher

# Create event script
script = create_test_script(
    commands=["neutral", "left", "left", "right", "push", "neutral"],
    interval=0.5,  # 500ms between events
    power=0.85
)

# Source with script
source = MockSource(script=script, loop_script=False)

# Pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time.sleep(5)  # Wait for script to finish
```

---

## Example 4: Create a Custom Publisher

```python
"""
Example of how to create your own publisher.
"""
from bcipydummies. publishers.base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent

class MyPublisher(Publisher):
    """Custom publisher that counts events by command."""
    
    def __init__(self):
        self._is_ready = False
        self. counters = {}
    
    def start(self) -> None:
        self._is_ready = True
        self.counters = {}
        print("MyPublisher started!")
    
    def stop(self) -> None:
        self._is_ready = False
        print(f"MyPublisher stopped.  Counters: {self.counters}")
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event:  EEGEvent) -> None:
        if isinstance(event, MentalCommandEvent):
            cmd = event.command. name
            self.counters[cmd] = self.counters.get(cmd, 0) + 1
            print(f"Command {cmd} detected ({self.counters[cmd]} times)")


# Use the custom publisher
from bcipydummies import BCIPipeline, MockSource

source = MockSource()
my_pub = MyPublisher()

with BCIPipeline(source=source, publishers=[my_pub]):
    import time
    time. sleep(10)
```

---

## Example 5: Create a Custom Processor

```python
"""
Example of custom processor that filters NEUTRAL commands.
"""
from bcipydummies.processors.base import Processor
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand
from typing import Optional

class FilterNeutral(Processor):
    """Filters all NEUTRAL events."""
    
    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        if isinstance(event, MentalCommandEvent):
            if event.command == MentalCommand.NEUTRAL: 
                return None  # Filter
        return event  # Pass the rest
    
    def reset(self) -> None:
        pass  # No state


# Use the processor
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher

pipeline = BCIPipeline(
    source=MockSource(),
    processors=[FilterNeutral()],
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time. sleep(10)
```

---

## Example 6: Using Factory (Simplified Configuration)

```python
"""
Using factory functions to create pipelines from configuration.
"""
from bcipydummies import create_pipeline, Config, ThresholdConfig, KeyboardConfig, EmotivConfig

# Create configuration
config = Config(
    emotiv=EmotivConfig(
        client_id="your_client_id",
        client_secret="your_client_secret"
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

# Create pipeline with factory
# Use "simulated" instead of "emotiv" for testing without hardware
pipeline = create_pipeline(config, source_type="simulated")

with pipeline:
    input("Press Enter to stop...")
```

---

## Example 7: Real Window Control (Windows)

```python
"""
Real example controlling a Windows window.
NOTE:  Requires Windows and the target application open.
"""
from bcipydummies import BCIPipeline, MockSource, ThresholdProcessor, CommandMapper
from bcipydummies. publishers.keyboard. windows import WindowsKeyboardPublisher
from bcipydummies.core.events import MentalCommand

# List available windows
print("Available windows:")
for window in WindowsKeyboardPublisher. list_windows()[: 20]: 
    print(f"  - {window}")

# Configure
target_window = "Notepad"  # Change this to your window

# Simulated source for testing
source = MockSource()

# Processors
processors = [
    ThresholdProcessor(thresholds={"left": 0.7, "right": 0.7}),
    CommandMapper(mapping={
        "left": "A",
        "right": "D", 
        "push": "W",
        "lift": "SPACE"
    })
]

# Keyboard publisher
keyboard = WindowsKeyboardPublisher(
    window_name=target_window,
    command_mapping={
        MentalCommand.LEFT: "A",
        MentalCommand. RIGHT: "D",
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
        print(f"Controlling '{target_window}'...")
        print("Press Ctrl+C to stop.")
        import time
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
```

---

## Example 8: Usage with Real Emotiv Hardware

```python
"""
Example using REAL Emotiv hardware.
Shows mental commands received from the device in real time. 

REQUIREMENTS:
- Emotiv Cortex app running
- Emotiv headset connected and configured
- Mental commands trained in EmotivBCI
- Developer credentials (client_id, client_secret)
"""
import os
import time
from datetime import datetime

from bcipydummies import BCIPipeline, ConsolePublisher
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies. core.events import MentalCommandEvent, ConnectionEvent, EEGEvent
from bcipydummies.publishers.base import Publisher


class MonitorPublisher(Publisher):
    """
    Custom publisher to display detailed information
    of commands received from Emotiv hardware.
    """
    
    def __init__(self):
        self._is_ready = False
        self.total_events = 0
        self.commands_by_type = {}
        self.last_command = None
        self.start_time = None
    
    def start(self) -> None:
        self._is_ready = True
        self.start_time = datetime.now()
        print("=" * 60)
        print("🧠 EMOTIV COMMAND MONITOR - STARTED")
        print("=" * 60)
        print(f"⏰ Start:  {self.start_time. strftime('%H:%M:%S')}")
        print("-" * 60)
    
    def stop(self) -> None:
        self._is_ready = False
        duration = datetime.now() - self.start_time if self.start_time else None
        print("\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {duration}")
        print(f"📈 Total events: {self.total_events}")
        print("\n📋 Commands by type:")
        for cmd, count in sorted(self.commands_by_type.items()):
            percentage = (count / self.total_events * 100) if self.total_events > 0 else 0
            print(f"   • {cmd}: {count} ({percentage:.1f}%)")
        print("=" * 60)
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event: EEGEvent) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S. %f")[:-3]
        
        if isinstance(event, ConnectionEvent):
            status = "✅ CONNECTED" if event.connected else "❌ DISCONNECTED"
            print(f"[{timestamp}] {status}:  {event.message or ''}")
            
        elif isinstance(event, MentalCommandEvent):
            self.total_events += 1
            cmd_name = event.command.name
            self.commands_by_type[cmd_name] = self.commands_by_type.get(cmd_name, 0) + 1
            
            # Visual power bar
            power_percentage = event.power * 100
            bars = int(power_percentage / 5)  # 20 bars maximum
            visual_bar = "█" * bars + "░" * (20 - bars)
            
            # Emoji based on command
            emojis = {
                "NEUTRAL": "😐",
                "PUSH": "👊",
                "PULL": "🤚",
                "LIFT": "⬆️",
                "DROP":  "⬇️",
                "LEFT": "⬅️",
                "RIGHT": "➡️",
                "ROTATE_LEFT": "↪️",
                "ROTATE_RIGHT": "↩️",
                "DISAPPEAR": "👻"
            }
            emoji = emojis.get(cmd_name, "🧠")
            
            print(f"[{timestamp}] {emoji} {cmd_name: 12} [{visual_bar}] {power_percentage: 5.1f}%")
            
            # Save last non-neutral command
            if cmd_name != "NEUTRAL":
                self. last_command = (cmd_name, event.power)


def main():
    """
    Main function to connect with real Emotiv hardware.
    """
    print("\n🔧 Configuring Emotiv connection...")
    
    # Get credentials from environment variables
    client_id = os. environ.get("EMOTIV_CLIENT_ID")
    client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
    
    if not client_id or not client_secret: 
        print("❌ ERROR: Configure environment variables:")
        print("   export EMOTIV_CLIENT_ID='your_client_id'")
        print("   export EMOTIV_CLIENT_SECRET='your_client_secret'")
        return
    
    # Create credentials
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Create Emotiv source
    source = EmotivSource(
        credentials=credentials,
        streams=["com"]  # Mental commands only
    )
    
    # Create monitor publisher
    monitor = MonitorPublisher()
    
    # Create pipeline
    pipeline = BCIPipeline(
        source=source,
        publishers=[monitor]
    )
    
    print("🚀 Starting pipeline...")
    print("💡 Tip: Make sure your headset is connected in Emotiv Cortex")
    print()
    
    try:
        with pipeline:
            print("Pipeline running. Press Ctrl+C to stop.\n")
            while True: 
                time.sleep(1)
    except KeyboardInterrupt: 
        print("\n\n🛑 Stopping...")
    except Exception as e:
        print(f"\n❌ Error:  {e}")


if __name__ == "__main__":
    main()
```

---

## Related Documentation

- **[Deep Dive Guide](deep-dive.md)** - Complete architecture explanation
- **[Getting Started](../getting-started/quickstart.md)** - Quick setup guide
- **[API Reference](../api/emotiv-controller.md)** - API documentation
- **[Hardware Setup](../hardware/emotiv-setup.md)** - Emotiv configuration