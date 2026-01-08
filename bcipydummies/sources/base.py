"""Base protocol and types for EEG data sources.

This module defines the abstract interface that all EEG sources must implement.
It follows the Protocol pattern from typing to enable structural subtyping,
allowing for flexible source implementations without requiring inheritance.
"""

from abc import abstractmethod
from typing import Callable, Protocol, runtime_checkable

from bcipydummies.core.events import EEGEvent


# Type alias for event callback functions
EventCallback = Callable[[EEGEvent], None]


@runtime_checkable
class EEGSource(Protocol):
    """Protocol defining the interface for EEG data sources.

    All EEG sources (Emotiv, OpenBCI, Muse, simulated, etc.) must implement
    this interface to work with the BCI pipeline. The protocol follows
    the Observer pattern for event delivery.

    The lifecycle of a source is:
        1. Create instance
        2. subscribe() - Register callbacks for events
        3. connect() - Start receiving data
        4. ... events flow to subscribers ...
        5. disconnect() - Stop receiving data
        6. unsubscribe() - Remove callbacks

    Thread Safety:
        Implementations should ensure thread-safe event delivery.
        Callbacks may be invoked from background threads.
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier for this source instance.

        Returns:
            A string uniquely identifying this source.
        """
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether the source is currently connected and streaming.

        Returns:
            True if connected and actively emitting events.
        """
        ...

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the EEG device and start streaming.

        This method should:
            - Initialize the connection to the hardware/API
            - Start emitting events to subscribers
            - Be idempotent (calling when already connected is safe)

        Raises:
            ConnectionError: If unable to establish connection.
            TimeoutError: If connection attempt times out.
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the EEG device and stop streaming.

        This method should:
            - Cleanly close the connection
            - Stop emitting events
            - Release any resources
            - Be idempotent (calling when disconnected is safe)
        """
        ...

    @abstractmethod
    def subscribe(self, callback: EventCallback) -> None:
        """Register a callback to receive EEG events.

        The callback will be invoked for each event emitted by the source.
        Multiple callbacks can be registered.

        Args:
            callback: Function to call with each EEGEvent.
                     Must accept a single EEGEvent parameter.

        Note:
            Callbacks may be invoked from a background thread.
            Ensure your callback is thread-safe.
        """
        ...

    @abstractmethod
    def unsubscribe(self, callback: EventCallback) -> None:
        """Remove a previously registered callback.

        Args:
            callback: The callback function to remove.
                     Must be the same object passed to subscribe().

        Note:
            Safe to call even if callback was not registered.
        """
        ...


class BaseEEGSource:
    """Base implementation providing common functionality for EEG sources.

    This class provides the subscriber management boilerplate that most
    sources will need. Concrete sources can inherit from this and focus
    on device-specific connection logic.

    This is an optional convenience class - sources can also implement
    the EEGSource protocol directly without inheriting from this.
    """

    def __init__(self, source_id: str) -> None:
        """Initialize the base source.

        Args:
            source_id: Unique identifier for this source instance.
        """
        self._source_id = source_id
        self._subscribers: list[EventCallback] = []
        self._connected = False

    @property
    def source_id(self) -> str:
        """Unique identifier for this source instance."""
        return self._source_id

    @property
    def is_connected(self) -> bool:
        """Whether the source is currently connected."""
        return self._connected

    def subscribe(self, callback: EventCallback) -> None:
        """Register a callback to receive EEG events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: EventCallback) -> None:
        """Remove a previously registered callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _emit(self, event: EEGEvent) -> None:
        """Emit an event to all subscribers.

        Args:
            event: The event to broadcast to subscribers.

        Note:
            Errors in individual callbacks are logged but don't
            prevent other callbacks from receiving the event.
        """
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                # Log but don't propagate - one bad callback shouldn't
                # break the entire event flow
                import logging
                logging.getLogger(__name__).exception(
                    f"Error in subscriber callback: {e}"
                )

    def connect(self) -> None:
        """Override this method to implement device connection."""
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self) -> None:
        """Override this method to implement device disconnection."""
        raise NotImplementedError("Subclasses must implement disconnect()")
