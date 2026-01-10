"""Event data classes for BCI middleware.

This module defines the core event types used throughout the BCIpyDummies
library for representing EEG signals, mental commands, facial expressions,
performance metrics, and connection states.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional


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


class FacialExpression(Enum):
    """Enumeration of supported facial expressions.

    These expressions represent facial actions that can be detected
    by BCI devices like Emotiv headsets via the 'fac' stream.
    """

    NEUTRAL = auto()
    BLINK = auto()
    WINK_LEFT = auto()
    WINK_RIGHT = auto()
    SURPRISE = auto()
    FROWN = auto()
    SMILE = auto()
    CLENCH = auto()
    LAUGH = auto()
    SMIRK_LEFT = auto()
    SMIRK_RIGHT = auto()
    LOOK_LEFT = auto()
    LOOK_RIGHT = auto()
    LOOK_UP = auto()
    LOOK_DOWN = auto()

    @classmethod
    def from_string(cls, expression_name: str) -> "FacialExpression":
        """Convert a string expression name to FacialExpression enum.

        Args:
            expression_name: Case-insensitive expression name (e.g., 'blink', 'SMILE')

        Returns:
            The corresponding FacialExpression enum value.

        Raises:
            ValueError: If the expression name is not recognized.
        """
        # Map Cortex API names to our enum names
        name_mapping = {
            "neutral": "NEUTRAL",
            "blink": "BLINK",
            "winkL": "WINK_LEFT",
            "winkR": "WINK_RIGHT",
            "surprise": "SURPRISE",
            "frown": "FROWN",
            "smile": "SMILE",
            "clench": "CLENCH",
            "laugh": "LAUGH",
            "smirkLeft": "SMIRK_LEFT",
            "smirkRight": "SMIRK_RIGHT",
            "lookL": "LOOK_LEFT",
            "lookR": "LOOK_RIGHT",
            "lookU": "LOOK_UP",
            "lookD": "LOOK_DOWN",
        }

        # Try direct mapping first
        mapped = name_mapping.get(expression_name)
        if mapped:
            return cls[mapped]

        # Try normalized name
        normalized = expression_name.upper().replace("-", "_").replace(" ", "_")
        try:
            return cls[normalized]
        except KeyError:
            valid_expressions = ", ".join(expr.name.lower() for expr in cls)
            raise ValueError(
                f"Unknown facial expression: '{expression_name}'. "
                f"Valid expressions are: {valid_expressions}"
            )


class EmotivStream(Enum):
    """Available Emotiv data streams.

    These streams can be subscribed to receive different types of data
    from the Emotiv headset. Some streams require a license.
    """

    # Free streams (no license required)
    COM = "com"  # Mental commands
    FAC = "fac"  # Facial expressions
    SYS = "sys"  # System events (battery, signal quality)
    DEV = "dev"  # Device information
    POW = "pow"  # Power band data (alpha, beta, gamma, etc.)
    MET = "met"  # Performance metrics (attention, meditation, etc.)

    # Licensed streams
    EEG = "eeg"  # Raw EEG data (requires license)
    MOT = "mot"  # Motion data (requires license)

    @classmethod
    def free_streams(cls) -> List["EmotivStream"]:
        """Return list of streams that don't require a license."""
        return [cls.COM, cls.FAC, cls.SYS, cls.DEV, cls.POW, cls.MET]

    @classmethod
    def from_string(cls, stream_name: str) -> "EmotivStream":
        """Convert a string stream name to EmotivStream enum.

        Args:
            stream_name: Stream name (e.g., 'com', 'fac')

        Returns:
            The corresponding EmotivStream enum value.

        Raises:
            ValueError: If the stream name is not recognized.
        """
        try:
            return cls(stream_name.lower())
        except ValueError:
            valid_streams = ", ".join(s.value for s in cls)
            raise ValueError(
                f"Unknown stream: '{stream_name}'. "
                f"Valid streams are: {valid_streams}"
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


@dataclass(frozen=True)
class FacialExpressionEvent(EEGEvent):
    """Event representing a detected facial expression.

    Extends EEGEvent with facial expression information including
    the type of expression detected and its power/confidence level.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        expression: The facial expression that was detected.
        power: Confidence/power level of the expression, typically 0.0 to 1.0.
        action: Optional mapped action string.
    """

    expression: FacialExpression
    power: float
    action: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the power value is within acceptable range."""
        if not 0.0 <= self.power <= 1.0:
            raise ValueError(f"Power must be between 0.0 and 1.0, got {self.power}")


@dataclass(frozen=True)
class PerformanceMetricsEvent(EEGEvent):
    """Event representing performance metrics from Emotiv.

    Contains metrics like focus, engagement, relaxation, etc.
    These correspond to the Emotiv Cortex API "met" stream.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        focus: Focus/attention level (0.0 to 1.0) - from Cortex "foc" metric.
        engagement: Engagement level (0.0 to 1.0) - from Cortex "eng" metric.
        excitement: Short-term excitement level (0.0 to 1.0) - from Cortex "exc" metric.
        long_excitement: Long-term excitement level (0.0 to 1.0) - from Cortex "lex" metric.
        stress: Stress/frustration level (0.0 to 1.0) - from Cortex "str" metric.
        relaxation: Relaxation level (0.0 to 1.0) - from Cortex "rel" metric.
        interest: Interest/affinity level (0.0 to 1.0) - from Cortex "int" metric.
    """

    focus: Optional[float] = None
    engagement: Optional[float] = None
    excitement: Optional[float] = None
    long_excitement: Optional[float] = None
    stress: Optional[float] = None
    relaxation: Optional[float] = None
    interest: Optional[float] = None


@dataclass(frozen=True)
class PowerBandEvent(EEGEvent):
    """Event representing EEG power band data.

    Contains power values for different frequency bands.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        theta: Theta band power (4-8 Hz).
        alpha: Alpha band power (8-12 Hz).
        low_beta: Low beta band power (12-16 Hz).
        high_beta: High beta band power (16-25 Hz).
        gamma: Gamma band power (25-45 Hz).
        channel: Name of the EEG channel (e.g., 'AF3', 'F7').
    """

    channel: str
    theta: float = 0.0
    alpha: float = 0.0
    low_beta: float = 0.0
    high_beta: float = 0.0
    gamma: float = 0.0


@dataclass(frozen=True)
class DeviceInfoEvent(EEGEvent):
    """Event representing device information updates.

    Contains battery level, signal quality, and other device info.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        battery_level: Battery percentage (0-100).
        signal_quality: Overall signal quality (0.0 to 1.0).
        contact_quality: Dict mapping channel names to quality values.
    """

    battery_level: Optional[int] = None
    signal_quality: Optional[float] = None
    contact_quality: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemEvent(EEGEvent):
    """Event representing system-level events.

    Used for battery warnings, headset state changes, etc.

    Attributes:
        timestamp: Unix timestamp in seconds when the event occurred.
        source_id: Identifier of the device or source that generated this event.
        event_type: Type of system event (e.g., 'battery_low', 'headset_connected').
        data: Additional event data.
    """

    event_type: str
    data: Dict = field(default_factory=dict)
