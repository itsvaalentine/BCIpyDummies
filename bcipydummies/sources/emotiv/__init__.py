"""Emotiv EEG source implementation.

This module provides the EmotivSource class for connecting to Emotiv
devices (EPOC, EPOC+, EPOC X, Insight, etc.) via the Cortex API.

Example usage:
    >>> from bcipydummies.sources.emotiv import EmotivSource, CortexCredentials
    >>>
    >>> # Get credentials from environment variables
    >>> credentials = CortexCredentials.from_environment()
    >>>
    >>> # Or provide them directly
    >>> credentials = CortexCredentials(
    ...     client_id="your-client-id",
    ...     client_secret="your-client-secret",
    ... )
    >>>
    >>> source = EmotivSource(credentials)
    >>> source.subscribe(lambda event: print(event))
    >>> source.connect()
"""

from bcipydummies.sources.emotiv.cortex_client import (
    CortexClient,
    CortexCredentials,
    CortexState,
)
from bcipydummies.sources.emotiv.source import EmotivSource

__all__ = [
    "CortexClient",
    "CortexCredentials",
    "CortexState",
    "EmotivSource",
]
