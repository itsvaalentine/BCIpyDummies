"""EmotivSource - EEG source implementation for Emotiv devices.

This module provides the EmotivSource class that wraps the CortexClient
and implements the EEGSource protocol. It translates raw Cortex API
events into standardized MentalCommandEvent objects.
"""

import logging
import time
from typing import Optional

from bcipydummies.core.events import (
    ConnectionEvent,
    EEGEvent,
    MentalCommand,
    MentalCommandEvent,
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

    Example usage:
        >>> from bcipydummies.sources.emotiv import EmotivSource
        >>> from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
        >>>
        >>> credentials = CortexCredentials.from_environment()
        >>> source = EmotivSource(credentials)
        >>>
        >>> def handle_event(event):
        ...     if isinstance(event, MentalCommandEvent):
        ...         print(f"Command: {event.command.name} ({event.power:.2f})")
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

    def __init__(
        self,
        credentials: CortexCredentials,
        headset_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> None:
        """Initialize the Emotiv source.

        Args:
            credentials: Cortex API credentials for authentication.
            headset_id: Optional specific headset ID to connect to.
                       If None, connects to the first available headset.
            source_id: Optional custom source identifier. If None,
                      will be generated from the headset ID after connection.
        """
        # Use a temporary source ID that will be updated after connection
        super().__init__(source_id or "emotiv-pending")
        self._custom_source_id = source_id
        self._credentials = credentials
        self._target_headset_id = headset_id

        # Create the Cortex client
        self._client = CortexClient(
            credentials=credentials,
            headset_id=headset_id,
            streams=["com"],  # Mental commands stream
        )

        # Register our handlers with the client
        self._client.on_mental_command = self._on_mental_command
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

    def connect(self) -> None:
        """Connect to the Emotiv headset via Cortex API.

        This method initiates the connection process. The actual connection
        happens asynchronously. Subscribe to events before calling connect()
        to receive the ConnectionEvent when connection completes.

        Raises:
            ConnectionError: If already connected or connection fails to start.
        """
        if self._connected:
            raise ConnectionError(
                "Already connected",
                source_id=self.source_id,
            )

        logger.info(f"Connecting EmotivSource (target: {self._target_headset_id})...")
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
