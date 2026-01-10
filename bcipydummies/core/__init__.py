"""Core module for BCIpyDummies.

This module provides the foundational components of the BCIpyDummies library:
- Event data classes for representing BCI signals and states
- BCIPipeline engine for orchestrating data flow
- Configuration management
- Factory functions for pipeline creation
- Custom exceptions for error handling

Example usage:
    >>> from bcipydummies.core import (
    ...     MentalCommand,
    ...     MentalCommandEvent,
    ...     FacialExpression,
    ...     FacialExpressionEvent,
    ...     BCIPipeline,
    ...     Config,
    ...     create_pipeline,
    ... )
    >>>
    >>> # Create pipeline from configuration
    >>> config = Config.from_yaml("config.yaml")
    >>> pipeline = create_pipeline(config)
    >>>
    >>> # Or use the pipeline directly
    >>> with pipeline:
    ...     input("Press Enter to stop...")
"""

from .events import (
    ConnectionEvent,
    DeviceInfoEvent,
    EEGEvent,
    EmotivStream,
    FacialExpression,
    FacialExpressionEvent,
    MentalCommand,
    MentalCommandEvent,
    PerformanceMetricsEvent,
    PowerBandEvent,
    SystemEvent,
)
from .exceptions import (
    AuthenticationError,
    BCIError,
    ConfigurationError,
    ConnectionError,
    DeviceNotFoundError,
    SessionError,
    SubscriptionError,
    WindowNotFoundError,
)
from .config import (
    Config,
    EmotivConfig,
    KeyboardConfig,
    ThresholdConfig,
)
from .engine import BCIPipeline
from .factory import (
    create_pipeline,
    create_pipeline_from_yaml,
    create_pipeline_from_env,
    create_source,
    create_processors,
    create_publishers,
    register_source,
    register_processor,
    register_publisher,
    get_available_sources,
    get_available_processors,
    get_available_publishers,
)

__all__ = [
    # Events
    "ConnectionEvent",
    "DeviceInfoEvent",
    "EEGEvent",
    "EmotivStream",
    "FacialExpression",
    "FacialExpressionEvent",
    "MentalCommand",
    "MentalCommandEvent",
    "PerformanceMetricsEvent",
    "PowerBandEvent",
    "SystemEvent",
    # Pipeline Engine
    "BCIPipeline",
    # Configuration
    "Config",
    "EmotivConfig",
    "KeyboardConfig",
    "ThresholdConfig",
    # Factory functions
    "create_pipeline",
    "create_pipeline_from_yaml",
    "create_pipeline_from_env",
    "create_source",
    "create_processors",
    "create_publishers",
    "register_source",
    "register_processor",
    "register_publisher",
    "get_available_sources",
    "get_available_processors",
    "get_available_publishers",
    # Exceptions
    "AuthenticationError",
    "BCIError",
    "ConfigurationError",
    "ConnectionError",
    "DeviceNotFoundError",
    "SessionError",
    "SubscriptionError",
    "WindowNotFoundError",
]
