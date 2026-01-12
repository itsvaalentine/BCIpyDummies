"""EmotivSource - EEG source implementation for Emotiv devices.

This module provides the EmotivSource class that wraps the CortexClient
and implements the EEGSource protocol. It translates raw Cortex API
events into standardized event objects for mental commands, facial
expressions, performance metrics, and more.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from bcipydummies.core.events import (
    ConnectionEvent,
    DeviceInfoEvent,
    EEGEvent,
    FacialExpression,
    FacialExpressionEvent,
    MentalCommand,
    MentalCommandEvent,
    PerformanceMetricsEvent,
    PowerBandEvent,
    SystemEvent,
)
from bcipydummies.core.exceptions import BCIError, ConnectionError
from bcipydummies.sources.base import BaseEEGSource
from bcipydummies.sources.emotiv.cortex_client import (
    CortexClient,
    CortexCredentials,
    CortexState,
)


logger = logging.getLogger(__name__)


class EmotivSource(BaseEEGSource):
    """EEG source implementation for Emotiv devices via Cortex API.

    This class wraps the low-level CortexClient and provides the standard
    EEGSource interface. It converts Cortex API events into the library's
    standardized event types.

    Supported streams (no license required):
        - com: Mental commands (push, pull, lift, drop, left, right, etc.)
        - fac: Facial expressions (blink, wink, smile, frown, etc.)
        - met: Performance metrics (attention, stress, relaxation, etc.)
        - pow: Power band data (theta, alpha, beta, gamma)
        - dev: Device info (battery, signal quality)
        - sys: System events

    Example usage with all streams:
        >>> from bcipydummies.sources.emotiv import EmotivSource
        >>> from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
        >>>
        >>> credentials = CortexCredentials.from_environment()
        >>> source = EmotivSource(
        ...     credentials,
        ...     streams=["com", "fac", "met"]  # Subscribe to multiple streams
        ... )
        >>>
        >>> def handle_event(event):
        ...     if isinstance(event, MentalCommandEvent):
        ...         print(f"Mental: {event.command.name} ({event.power:.2f})")
        ...     elif isinstance(event, FacialExpressionEvent):
        ...         print(f"Facial: {event.expression.name} ({event.power:.2f})")
        >>>
        >>> source.subscribe(handle_event)
        >>> source.connect()
        >>> # ... events flow to handle_event ...
        >>> source.disconnect()
    """

    # Mapping from Cortex API action strings to MentalCommand enum
    _COMMAND_MAP = {
        "neutral": MentalCommand.NEUTRAL,
        "push": MentalCommand.PUSH,
        "pull": MentalCommand.PULL,
        "lift": MentalCommand.LIFT,
        "drop": MentalCommand.DROP,
        "left": MentalCommand.LEFT,
        "right": MentalCommand.RIGHT,
        "rotateLeft": MentalCommand.ROTATE_LEFT,
        "rotateRight": MentalCommand.ROTATE_RIGHT,
        "disappear": MentalCommand.DISAPPEAR,
    }

    # Mapping from Cortex API facial expression strings to FacialExpression enum
    _EXPRESSION_MAP = {
        "neutral": FacialExpression.NEUTRAL,
        "blink": FacialExpression.BLINK,
        "winkL": FacialExpression.WINK_LEFT,
        "winkR": FacialExpression.WINK_RIGHT,
        "surprise": FacialExpression.SURPRISE,
        "frown": FacialExpression.FROWN,
        "smile": FacialExpression.SMILE,
        "clench": FacialExpression.CLENCH,
        "laugh": FacialExpression.LAUGH,
        "smirkLeft": FacialExpression.SMIRK_LEFT,
        "smirkRight": FacialExpression.SMIRK_RIGHT,
        "lookL": FacialExpression.LOOK_LEFT,
        "lookR": FacialExpression.LOOK_RIGHT,
        "lookU": FacialExpression.LOOK_UP,
        "lookD": FacialExpression.LOOK_DOWN,
    }

    def __init__(
        self,
        credentials: CortexCredentials,
        headset_id: Optional[str] = None,
        source_id: Optional[str] = None,
        streams: Optional[List[str]] = None,
    ) -> None:
        """Initialize the Emotiv source.

        Args:
            credentials: Cortex API credentials for authentication.
            headset_id: Optional specific headset ID to connect to.
                       If None, connects to the first available headset.
            source_id: Optional custom source identifier. If None,
                      will be generated from the headset ID after connection.
            streams: List of data streams to subscribe to.
                    Available streams (no license required):
                    - "com": Mental commands
                    - "fac": Facial expressions
                    - "met": Performance metrics
                    - "pow": Power band data
                    - "dev": Device info
                    - "sys": System events
                    Defaults to ["com"] for backward compatibility.
        """
        # Use a temporary source ID that will be updated after connection
        super().__init__(source_id or "emotiv-pending")
        self._custom_source_id = source_id
        self._credentials = credentials
        self._target_headset_id = headset_id
        self._streams = streams or ["com"]

        # Create the Cortex client
        self._client = CortexClient(
            credentials=credentials,
            headset_id=headset_id,
            streams=self._streams,
        )

        # Register our handlers with the client
        self._client.on_mental_command = self._on_mental_command
        self._client.on_facial_expression = self._on_facial_expression
        self._client.on_performance_metrics = self._on_performance_metrics
        self._client.on_power_band = self._on_power_band
        self._client.on_device_info = self._on_device_info
        self._client.on_system_event = self._on_system_event
        self._client.on_connection_change = self._on_connection_change
        self._client.on_error = self._on_error

        self._last_error: Optional[BCIError] = None

    @property
    def source_id(self) -> str:
        """Unique identifier for this source.

        Returns the custom source ID if provided, otherwise generates
        an ID from the connected headset ID.
        """
        if self._custom_source_id:
            return self._custom_source_id

        headset = self._client.headset_id
        if headset:
            return f"emotiv-{headset}"

        return self._source_id

    @property
    def is_connected(self) -> bool:
        """Check if the source is connected and streaming."""
        return self._client.is_connected

    @property
    def headset_id(self) -> Optional[str]:
        """ID of the connected headset, if any."""
        return self._client.headset_id

    @property
    def session_id(self) -> Optional[str]:
        """ID of the active Cortex session, if any."""
        return self._client.session_id

    @property
    def last_error(self) -> Optional[BCIError]:
        """Last error that occurred, if any."""
        return self._last_error

    @property
    def streams(self) -> List[str]:
        """List of subscribed data streams."""
        return self._streams.copy()

    def connect(self) -> None:
        """Connect to the Emotiv headset via Cortex API.

        This method initiates the connection process. The actual connection
        happens asynchronously. Subscribe to events before calling connect()
        to receive the ConnectionEvent when connection completes.

        The connection flow:
        1. Request access (shows popup in Cortex if not yet approved)
        2. Authorize with credentials
        3. Query available headsets
        4. Create session with headset
        5. Subscribe to requested streams

        Raises:
            ConnectionError: If already connected or connection fails to start.
        """
        if self._connected:
            raise ConnectionError(
                "Already connected",
                source_id=self.source_id,
            )

        logger.info(f"Connecting EmotivSource (target: {self._target_headset_id}, streams: {self._streams})...")
        self._last_error = None
        self._client.connect()

    def disconnect(self) -> None:
        """Disconnect from the Emotiv headset.

        Safe to call even if not connected.
        """
        logger.info("Disconnecting EmotivSource...")
        self._client.disconnect()
        self._connected = False

    def _on_mental_command(self, action: str, power: float) -> None:
        """Handle mental command from Cortex client.

        Converts the raw action string and power value into a
        MentalCommandEvent and emits it to subscribers.

        Args:
            action: The action name from Cortex API (e.g., "push", "left").
            power: The power/confidence level (0.0 to 1.0).
        """
        # Map the action string to enum
        command = self._COMMAND_MAP.get(action.lower())
        if command is None:
            logger.warning(f"Unknown mental command action: {action}")
            # Try using from_string as fallback
            try:
                command = MentalCommand.from_string(action)
            except ValueError:
                logger.error(f"Could not map mental command: {action}")
                return

        # Clamp power to valid range
        power = max(0.0, min(1.0, power))

        # Create and emit the event
        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id=self.source_id,
            command=command,
            power=power,
        )

        logger.debug(f"Mental command: {command.name} ({power:.2f})")
        self._emit(event)

    def _on_facial_expression(self, expression: str, power: float) -> None:
        """Handle facial expression from Cortex client.

        Converts the raw expression string and power value into a
        FacialExpressionEvent and emits it to subscribers.

        Args:
            expression: The expression name from Cortex API (e.g., "smile", "blink").
            power: The power/confidence level (0.0 to 1.0).
        """
        # Map the expression string to enum
        expr = self._EXPRESSION_MAP.get(expression)
        if expr is None:
            logger.warning(f"Unknown facial expression: {expression}")
            try:
                expr = FacialExpression.from_string(expression)
            except ValueError:
                logger.error(f"Could not map facial expression: {expression}")
                return

        # Clamp power to valid range
        power = max(0.0, min(1.0, power))

        # Create and emit the event
        event = FacialExpressionEvent(
            timestamp=time.time(),
            source_id=self.source_id,
            expression=expr,
            power=power,
        )

        logger.debug(f"Facial expression: {expr.name} ({power:.2f})")
        self._emit(event)

    def _on_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """Handle performance metrics from Cortex client.

        Args:
            metrics: Dict with keys like 'engagement', 'stress', 'relaxation', 'focus', etc.
        """
        event = PerformanceMetricsEvent(
            timestamp=time.time(),
            source_id=self.source_id,
            focus=metrics.get("focus"),
            engagement=metrics.get("engagement"),
            excitement=metrics.get("excitement"),
            long_excitement=metrics.get("long_excitement"),
            stress=metrics.get("stress"),
            relaxation=metrics.get("relaxation"),
            interest=metrics.get("interest"),
        )

        logger.debug(f"Performance metrics: {metrics}")
        self._emit(event)

    def _on_power_band(self, band_data: List[Dict[str, Any]]) -> None:
        """Handle power band data from Cortex client.

        Args:
            band_data: List of dicts with channel power band values.
        """
        for channel_data in band_data:
            event = PowerBandEvent(
                timestamp=time.time(),
                source_id=self.source_id,
                channel=channel_data.get("channel", "unknown"),
                theta=channel_data.get("theta", 0.0),
                alpha=channel_data.get("alpha", 0.0),
                low_beta=channel_data.get("low_beta", 0.0),
                high_beta=channel_data.get("high_beta", 0.0),
                gamma=channel_data.get("gamma", 0.0),
            )
            self._emit(event)

    def _on_device_info(self, info: Dict[str, Any]) -> None:
        """Handle device info from Cortex client.

        Args:
            info: Dict with device status information.
        """
        event = DeviceInfoEvent(
            timestamp=time.time(),
            source_id=self.source_id,
            battery_level=info.get("battery"),
            signal_quality=info.get("signal"),
            contact_quality=info.get("contact_quality", {}),
        )

        logger.debug(f"Device info: battery={info.get('battery')}, signal={info.get('signal')}")
        self._emit(event)

    def _on_system_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system event from Cortex client.

        Args:
            event_type: Type of system event.
            data: Additional event data.
        """
        event = SystemEvent(
            timestamp=time.time(),
            source_id=self.source_id,
            event_type=event_type,
            data=data,
        )

        logger.debug(f"System event: {event_type} - {data}")
        self._emit(event)

    def _on_connection_change(self, connected: bool, message: str) -> None:
        """Handle connection state change from Cortex client.

        Args:
            connected: Whether now connected or disconnected.
            message: Human-readable description of the state change.
        """
        self._connected = connected

        # Update source ID now that we know the headset
        if connected and self._client.headset_id:
            self._source_id = f"emotiv-{self._client.headset_id}"

        # Emit connection event
        event = ConnectionEvent(
            connected=connected,
            message=message,
        )

        logger.info(f"Connection state: {connected} - {message}")
        self._emit(event)

    def _on_error(self, error: Exception) -> None:
        """Handle error from Cortex client.

        Args:
            error: The exception that occurred.
        """
        if isinstance(error, BCIError):
            self._last_error = error
        else:
            self._last_error = ConnectionError(str(error), cause=error)

        logger.error(f"EmotivSource error: {error}")

        # Emit disconnection event on error
        event = ConnectionEvent(
            connected=False,
            message=f"Error: {error}",
        )
        self._emit(event)

    def __enter__(self) -> "EmotivSource":
        """Context manager entry - connect to the device."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - disconnect from the device."""
        self.disconnect()
