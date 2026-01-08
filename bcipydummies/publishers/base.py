"""Base publisher protocol for BCIpyDummies.

This module defines the abstract Publisher interface that all concrete
publishers must implement. Publishers are responsible for handling EEG
events and translating them into platform-specific actions.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bcipydummies.core.events import EEGEvent


class Publisher(ABC):
    """Abstract base class for all event publishers.

    Publishers receive EEG events and translate them into actions.
    This could be keyboard inputs, console output, network messages,
    or any other form of output.

    Lifecycle:
        1. Create publisher instance
        2. Call start() to initialize resources
        3. Call publish() to handle events
        4. Call stop() to release resources

    Example:
        publisher = ConcretePublisher()
        publisher.start()
        try:
            for event in event_stream:
                if publisher.is_ready:
                    publisher.publish(event)
        finally:
            publisher.stop()
    """

    @abstractmethod
    def publish(self, event: "EEGEvent") -> None:
        """Publish an EEG event.

        Args:
            event: The EEG event to publish.

        Raises:
            RuntimeError: If the publisher is not ready (start() not called).
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Initialize publisher resources.

        This method should be called before any publish() calls.
        It sets up any required connections, files, or system resources.

        Raises:
            RuntimeError: If initialization fails.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Release publisher resources.

        This method should be called when the publisher is no longer needed.
        It cleans up any connections, files, or system resources.
        Safe to call multiple times.
        """
        pass

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the publisher is ready to accept events.

        Returns:
            True if start() has been called and stop() has not,
            False otherwise.
        """
        pass

    def __enter__(self) -> "Publisher":
        """Context manager entry - starts the publisher."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the publisher."""
        self.stop()
