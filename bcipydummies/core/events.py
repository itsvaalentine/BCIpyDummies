"""Event data classes for BCI middleware.

This module defines the core event types used throughout the BCIpyDummies
library for representing EEG signals, mental commands, and connection states.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class MentalCommand(Enum):
    """Enumeration of supported mental commands.

    These commands represent the mental actions that can be detected
    by BCI devices like Emotiv headsets.
    """

    NEUTRAL = auto()
    PUSH = auto()
    PULL = auto()
    LIFT = auto()
    DROP = auto()
    LEFT = auto()
    RIGHT = auto()
    ROTATE_LEFT = auto()
    ROTATE_RIGHT = auto()
    DISAPPEAR = auto()

    @classmethod
    def from_string(cls, command_name: str) -> "MentalCommand":
        """Convert a string command name to MentalCommand enum.

        Args:
            command_name: Case-insensitive command name (e.g., 'left', 'PUSH')

        Returns:
            The corresponding MentalCommand enum value.

        Raises:
            ValueError: If the command name is not recognized.
        """
        normalized = command_name.upper().replace("-", "_").replace(" ", "_")
        try:
            return cls[normalized]
        except KeyError:
            valid_commands = ", ".join(cmd.name.lower() for cmd in cls)
            raise ValueError(
                f"Unknown mental command: '{command_name}'. "
                f"Valid commands are: {valid_commands}"
            )


@dataclass(frozen=True)
class EEGEvent:
    """Base event class for EEG-related data.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
    """

    timestamp: float
    source_id: str


@dataclass(frozen=True)
class MentalCommandEvent(EEGEvent):
    """Event representing a detected mental command.

    Extends EEGEvent with command-specific information including
    the type of command detected and its power/confidence level.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        command: The mental command that was detected.
        power: Confidence/power level of the command, typically 0.0 to 1.0.
        action: Optional mapped action string (e.g., key name).
                Populated by CommandMapper processor.
    """

    command: MentalCommand
    power: float
    action: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the power value is within acceptable range."""
        if not 0.0 <= self.power <= 1.0:
            raise ValueError(f"Power must be between 0.0 and 1.0, got {self.power}")


@dataclass(frozen=True)
class ConnectionEvent:
    """Event representing a connection state change.

    Used to notify when a BCI device connects or disconnects.

    Attributes:
        connected: True if the device is now connected, False if disconnected.
        message: Optional human-readable message describing the connection state.
    """

    connected: bool
    message: Optional[str] = None
