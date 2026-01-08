"""Keyboard publisher module for BCIpyDummies.

This module provides keyboard simulation publishers that translate
EEG events into keyboard input for controlling applications.

Platform Support:
    - Windows: Full support via WindowsKeyboardPublisher
    - macOS: Not yet implemented
    - Linux: Not yet implemented

Example:
    # Automatic platform detection
    from bcipydummies.publishers.keyboard import create_keyboard_publisher

    publisher = create_keyboard_publisher(window_name="My Game")
    with publisher:
        publisher.press_key("SPACE")

    # Direct Windows usage
    from bcipydummies.publishers.keyboard import WindowsKeyboardPublisher

    publisher = WindowsKeyboardPublisher(window_name="My Game")
    with publisher:
        publisher.press_key("A", hold=0.1)
"""

from bcipydummies.publishers.keyboard.base import (
    KeyboardPublisher,
    create_keyboard_publisher,
    get_keyboard_publisher_class,
)

# Platform-specific imports with graceful fallback
try:
    from bcipydummies.publishers.keyboard.windows import (
        WindowsKeyboardPublisher,
        VK_CODES,
    )
except ImportError:
    # Not on Windows or pywin32 not installed
    WindowsKeyboardPublisher = None  # type: ignore
    VK_CODES = None  # type: ignore

__all__ = [
    "KeyboardPublisher",
    "WindowsKeyboardPublisher",
    "VK_CODES",
    "create_keyboard_publisher",
    "get_keyboard_publisher_class",
]
