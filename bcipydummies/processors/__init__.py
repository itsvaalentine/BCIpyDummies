"""Processors module for BCIpyDummies.

This module provides a pipeline of processors for filtering, transforming,
and mapping BCI events. Each processor implements the Processor protocol
and can be composed into processing chains.

Example:
    >>> from bcipydummies.processors import (
    ...     ThresholdProcessor,
    ...     DebounceProcessor,
    ...     CommandMapper,
    ... )
    >>>
    >>> # Create a processing pipeline
    >>> threshold = ThresholdProcessor(thresholds={"left": 0.8, "right": 0.5})
    >>> debounce = DebounceProcessor(cooldown=0.3)
    >>> mapper = CommandMapper(mapping={"left": "A", "right": "D"})
    >>>
    >>> # Process an event through the pipeline
    >>> event = threshold.process(raw_event)
    >>> if event:
    ...     event = debounce.process(event)
    >>> if event:
    ...     event = mapper.process(event)
"""

from bcipydummies.processors.base import Processor
from bcipydummies.processors.threshold import ThresholdProcessor, ThresholdConfig
from bcipydummies.processors.debounce import DebounceProcessor, DebounceConfig
from bcipydummies.processors.mapper import CommandMapper, MapperConfig

__all__ = [
    "Processor",
    "ThresholdProcessor",
    "ThresholdConfig",
    "DebounceProcessor",
    "DebounceConfig",
    "CommandMapper",
    "MapperConfig",
]
