"""Abstract keyboard publisher for BCIpyDummies.

This module defines the abstract KeyboardPublisher interface that
platform-specific implementations must follow. It provides the base
functionality for simulating keyboard input based on EEG events.
"""

import sys
from abc import abstractmethod
from typing import TYPE_CHECKING, Callable

from bcipydummies.publishers.base import Publisher

if TYPE_CHECKING:
    from bcipydummies.core.events import EEGEvent, MentalCommandEvent


class KeyboardPublisher(Publisher):
    """Abstract base class for keyboard-based publishers.

    This class extends Publisher with keyboard-specific functionality.
    Subclasses must implement platform-specific key simulation.

    The publisher maintains a mapping from mental commands to keys and
    can optionally apply power thresholds before triggering actions.

    Attributes:
        command_mapping: Dict mapping MentalCommand enum values to key strings.
        power_threshold: Minimum power level (0.0-1.0) to trigger actions.
        default_hold_time: Default duration to hold keys in seconds.

    Example:
        from bcipydummies.core.events import MentalCommand

        publisher = WindowsKeyboardPublisher(window_name="My Game")
        publisher.command_mapping = {
            MentalCommand.LEFT: "A",
            MentalCommand.RIGHT: "D",
            MentalCommand.PUSH: "SPACE",
        }
        publisher.power_threshold = 0.3

        with publisher:
            publisher.publish(mental_command_event)
    """

    def __init__(
        self,
        command_mapping: dict | None = None,
        power_threshold: float = 0.0,
        default_hold_time: float = 0.05,
    ) -> None:
        """Initialize the keyboard publisher.

        Args:
            command_mapping: Optional dict mapping MentalCommand to key strings.
            power_threshold: Minimum power (0.0-1.0) to trigger key press.
            default_hold_time: Default key hold duration in seconds.

        Raises:
            ValueError: If power_threshold is not in range [0.0, 1.0].
        """
        if not 0.0 <= power_threshold <= 1.0:
            raise ValueError(f"power_threshold must be between 0.0 and 1.0, got {power_threshold}")

        self._command_mapping: dict = command_mapping or {}
        self._power_threshold = power_threshold
        self._default_hold_time = default_hold_time
        self._is_ready = False
        self._on_key_press: Callable[[str, float], None] | None = None

    @property
    def command_mapping(self) -> dict:
        """Get the current command-to-key mapping."""
        return self._command_mapping

    @command_mapping.setter
    def command_mapping(self, mapping: dict) -> None:
        """Set the command-to-key mapping."""
        self._command_mapping = mapping

    @property
    def power_threshold(self) -> float:
        """Get the current power threshold."""
        return self._power_threshold

    @power_threshold.setter
    def power_threshold(self, threshold: float) -> None:
        """Set the power threshold.

        Args:
            threshold: New threshold value (0.0-1.0).

        Raises:
            ValueError: If threshold is not in range [0.0, 1.0].
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"power_threshold must be between 0.0 and 1.0, got {threshold}")
        self._power_threshold = threshold

    @property
    def default_hold_time(self) -> float:
        """Get the default key hold time in seconds."""
        return self._default_hold_time

    @default_hold_time.setter
    def default_hold_time(self, hold_time: float) -> None:
        """Set the default key hold time.

        Args:
            hold_time: Duration in seconds (must be positive).

        Raises:
            ValueError: If hold_time is not positive.
        """
        if hold_time <= 0:
            raise ValueError(f"default_hold_time must be positive, got {hold_time}")
        self._default_hold_time = hold_time

    @property
    def is_ready(self) -> bool:
        """Check if the publisher is ready."""
        return self._is_ready

    def set_key_press_callback(self, callback: Callable[[str, float], None] | None) -> None:
        """Set a callback to be invoked on each key press.

        Useful for logging, testing, or chaining actions.

        Args:
            callback: Function taking (key: str, hold_time: float) or None to clear.
        """
        self._on_key_press = callback

    @abstractmethod
    def press_key(self, key: str, hold: float | None = None) -> None:
        """Simulate a key press and release.

        Args:
            key: The key to press (e.g., "A", "SPACE", "ENTER").
            hold: Duration to hold the key in seconds. Uses default_hold_time if None.

        Raises:
            ValueError: If the key is not recognized.
            RuntimeError: If the publisher is not ready.
        """
        pass

    def publish(self, event: "EEGEvent") -> None:
        """Publish an EEG event as keyboard input.

        For MentalCommandEvent, looks up the command in command_mapping
        and presses the corresponding key if power exceeds threshold.

        Args:
            event: The EEG event to publish.

        Raises:
            RuntimeError: If the publisher is not ready.
        """
        if not self._is_ready:
            raise RuntimeError("Keyboard publisher not started. Call start() first.")

        # Import here to avoid circular imports at module level
        from bcipydummies.core.events import MentalCommandEvent

        if isinstance(event, MentalCommandEvent):
            self._handle_mental_command(event)

    def _handle_mental_command(self, event: "MentalCommandEvent") -> None:
        """Handle a mental command event.

        Args:
            event: The mental command event to process.
        """
        if event.power < self._power_threshold:
            return

        key = self._command_mapping.get(event.command)
        if key is None:
            return

        hold_time = self._default_hold_time
        self.press_key(key, hold_time)

        if self._on_key_press:
            self._on_key_press(key, hold_time)


def get_keyboard_publisher_class() -> type[KeyboardPublisher]:
    """Get the appropriate KeyboardPublisher class for the current platform.

    Returns:
        The platform-specific KeyboardPublisher subclass.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """
    if sys.platform == "win32":
        from bcipydummies.publishers.keyboard.windows import WindowsKeyboardPublisher
        return WindowsKeyboardPublisher
    elif sys.platform == "darwin":
        raise NotImplementedError(
            "macOS keyboard publisher not yet implemented. "
            "Consider using pyautogui or Quartz.CoreGraphics."
        )
    elif sys.platform.startswith("linux"):
        raise NotImplementedError(
            "Linux keyboard publisher not yet implemented. "
            "Consider using python-xlib or pynput."
        )
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")


def create_keyboard_publisher(**kwargs) -> KeyboardPublisher:
    """Factory function to create a platform-appropriate KeyboardPublisher.

    Args:
        **kwargs: Arguments to pass to the publisher constructor.

    Returns:
        A platform-specific KeyboardPublisher instance.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """
    cls = get_keyboard_publisher_class()
    return cls(**kwargs)
