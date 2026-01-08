"""EEG data sources for BCIpyDummies.

This module provides various EEG source implementations that can be used
with the BCI pipeline. All sources implement the EEGSource protocol,
providing a consistent interface regardless of the underlying hardware.

Available Sources:
    - EmotivSource: Real Emotiv devices via Cortex API
    - MockSource: Synthetic events for testing
    - ReplaySource: Replay recorded sessions

Example usage:
    >>> from bcipydummies.sources import MockSource, EmotivSource
    >>> from bcipydummies.sources.emotiv import CortexCredentials
    >>>
    >>> # For development/testing
    >>> source = MockSource()
    >>>
    >>> # For production with Emotiv hardware
    >>> credentials = CortexCredentials.from_environment()
    >>> source = EmotivSource(credentials)
    >>>
    >>> # Common interface
    >>> source.subscribe(lambda event: print(event))
    >>> source.connect()
"""

from bcipydummies.sources.base import BaseEEGSource, EEGSource, EventCallback
from bcipydummies.sources.mock import (
    MockSource,
    ReplaySource,
    ScriptedEvent,
    create_test_script,
)

# Lazy import for EmotivSource to avoid websocket dependency if not needed
def __getattr__(name: str):
    """Lazy loading for optional dependencies."""
    if name == "EmotivSource":
        from bcipydummies.sources.emotiv import EmotivSource
        return EmotivSource
    if name == "CortexCredentials":
        from bcipydummies.sources.emotiv import CortexCredentials
        return CortexCredentials
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Protocol and base class
    "EEGSource",
    "BaseEEGSource",
    "EventCallback",
    # Mock sources
    "MockSource",
    "ReplaySource",
    "ScriptedEvent",
    "create_test_script",
    # Emotiv (lazy loaded)
    "EmotivSource",
    "CortexCredentials",
]
