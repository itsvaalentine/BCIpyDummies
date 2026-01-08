"""Publishers module for BCIpyDummies.

Publishers are responsible for handling EEG events and translating them
into platform-specific actions such as keyboard input, console output,
or network messages.

Available Publishers:
    - Publisher: Abstract base class defining the publisher protocol
    - ConsolePublisher: Prints events to stdout for debugging
    - KeyboardPublisher: Abstract base for keyboard simulation
    - WindowsKeyboardPublisher: Windows-specific keyboard simulation

Example:
    from bcipydummies.publishers import ConsolePublisher, Publisher

    # Use ConsolePublisher for debugging
    with ConsolePublisher(prefix="DEBUG") as publisher:
        publisher.publish(event)

    # Create platform-appropriate keyboard publisher
    from bcipydummies.publishers.keyboard import create_keyboard_publisher

    with create_keyboard_publisher(window_name="My Game") as publisher:
        publisher.press_key("SPACE")
"""

from bcipydummies.publishers.base import Publisher
from bcipydummies.publishers.console import ConsolePublisher
from bcipydummies.publishers.keyboard import (
    KeyboardPublisher,
    create_keyboard_publisher,
    get_keyboard_publisher_class,
)

# Platform-specific imports with graceful fallback
try:
    from bcipydummies.publishers.keyboard import WindowsKeyboardPublisher
except ImportError:
    WindowsKeyboardPublisher = None  # type: ignore

__all__ = [
    # Base classes
    "Publisher",
    "KeyboardPublisher",
    # Concrete implementations
    "ConsolePublisher",
    "WindowsKeyboardPublisher",
    # Factory functions
    "create_keyboard_publisher",
    "get_keyboard_publisher_class",
]
