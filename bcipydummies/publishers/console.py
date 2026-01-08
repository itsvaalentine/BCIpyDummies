"""Console publisher for debugging and development.

This module provides a simple publisher that outputs events to stdout,
useful for debugging, testing, and development purposes.
"""

import sys
from datetime import datetime
from typing import TYPE_CHECKING, TextIO

from bcipydummies.publishers.base import Publisher

if TYPE_CHECKING:
    from bcipydummies.core.events import EEGEvent


class ConsolePublisher(Publisher):
    """Publisher that prints events to the console.

    Useful for debugging and development. Supports configurable
    formatting and output streams.

    Attributes:
        format_string: Template for formatting events. Supports placeholders:
            - {timestamp}: Current ISO timestamp
            - {event_type}: Type name of the event
            - {event}: String representation of the event
        stream: Output stream (defaults to sys.stdout)
        prefix: Optional prefix for all messages

    Example:
        publisher = ConsolePublisher(
            format_string="[{timestamp}] {event_type}: {event}",
            prefix="DEBUG"
        )
        with publisher:
            publisher.publish(mental_command_event)
        # Output: DEBUG [2024-01-15T10:30:00] MentalCommandEvent: ...
    """

    DEFAULT_FORMAT = "[{timestamp}] {event_type}: {event}"

    def __init__(
        self,
        format_string: str | None = None,
        stream: TextIO | None = None,
        prefix: str | None = None,
        include_timestamp: bool = True,
    ) -> None:
        """Initialize the console publisher.

        Args:
            format_string: Custom format string for output. Uses DEFAULT_FORMAT
                if not specified.
            stream: Output stream. Defaults to sys.stdout.
            prefix: Optional prefix prepended to all output lines.
            include_timestamp: Whether to include timestamp in default format.
        """
        self._format_string = format_string or self.DEFAULT_FORMAT
        self._stream = stream or sys.stdout
        self._prefix = prefix
        self._include_timestamp = include_timestamp
        self._is_ready = False
        self._event_count = 0

    def start(self) -> None:
        """Initialize the console publisher.

        For console output, this simply marks the publisher as ready.
        """
        self._is_ready = True
        self._event_count = 0
        self._write_line("Console publisher started")

    def stop(self) -> None:
        """Stop the console publisher.

        Flushes the output stream and marks as not ready.
        """
        if self._is_ready:
            self._write_line(f"Console publisher stopped (published {self._event_count} events)")
            self._stream.flush()
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        """Check if the publisher is ready."""
        return self._is_ready

    def publish(self, event: "EEGEvent") -> None:
        """Print the event to the console.

        Args:
            event: The EEG event to print.

        Raises:
            RuntimeError: If the publisher has not been started.
        """
        if not self._is_ready:
            raise RuntimeError("Console publisher not started. Call start() first.")

        formatted = self._format_event(event)
        self._write_line(formatted)
        self._event_count += 1

    def _format_event(self, event: "EEGEvent") -> str:
        """Format an event using the configured format string.

        Args:
            event: The event to format.

        Returns:
            Formatted string representation.
        """
        timestamp = datetime.now().isoformat() if self._include_timestamp else ""
        event_type = type(event).__name__

        return self._format_string.format(
            timestamp=timestamp,
            event_type=event_type,
            event=event,
        )

    def _write_line(self, message: str) -> None:
        """Write a line to the output stream.

        Args:
            message: The message to write.
        """
        if self._prefix:
            message = f"{self._prefix} {message}"
        self._stream.write(message + "\n")

    @property
    def event_count(self) -> int:
        """Get the number of events published since start().

        Returns:
            Number of events published.
        """
        return self._event_count
