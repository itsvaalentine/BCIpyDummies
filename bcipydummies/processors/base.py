"""Abstract base class for all event processors.

This module defines the Processor protocol that all processors must implement.
Processors form the building blocks of event processing pipelines, allowing
for modular composition of filtering, transformation, and mapping operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, TypeVar

from bcipydummies.core.events import EEGEvent


# Type variable for more specific event types in subclasses
E = TypeVar("E", bound=EEGEvent)


class Processor(ABC):
    """Abstract base class defining the processor interface.

    All processors in the BCIpyDummies library must implement this interface.
    Processors receive events, optionally transform them, and either return
    the (possibly modified) event or None to filter it out.

    The Processor pattern enables:
    - Composable processing pipelines
    - Single responsibility (each processor does one thing)
    - Easy testing of individual components
    - Runtime configuration of processing behavior

    Example:
        >>> class LoggingProcessor(Processor):
        ...     def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        ...         print(f"Processing: {event}")
        ...         return event
        ...
        ...     def reset(self) -> None:
        ...         pass
    """

    @abstractmethod
    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        """Process an incoming EEG event.

        This method receives an event and can either:
        - Return the event unchanged (pass-through)
        - Return a modified/transformed event
        - Return None to filter out the event

        Args:
            event: The EEG event to process.

        Returns:
            The processed event, or None if the event should be filtered out.

        Note:
            Since EEGEvent is frozen (immutable), processors that need to
            modify events should use dataclasses.replace() to create a
            new instance with the desired changes.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the processor's internal state.

        This method should clear any accumulated state, such as:
        - Timing information for debouncing
        - Cached values
        - Running statistics

        Call this method when starting a new session or when the
        processing pipeline needs to be reinitialized.
        """
        pass
