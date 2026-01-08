"""BCIpyDummies - EEG to action middleware library.

A middleware library to bridge Emotiv EEG headsets with Windows applications
through mental commands.

Basic usage:
    from bcipydummies import BCIPipeline, EmotivSource, KeyboardPublisher

    pipeline = BCIPipeline(
        source=EmotivSource(client_id="...", client_secret="..."),
        publishers=[KeyboardPublisher(target_window="My App")]
    )
    pipeline.start()

Or use the factory for configuration-driven setup:
    from bcipydummies import create_pipeline, Config

    config = Config.from_env()
    pipeline = create_pipeline(config)
    with pipeline:
        input("Press Enter to stop...")
"""

__version__ = "0.2.0"

# Core classes
from .core.engine import BCIPipeline
from .core.config import Config, ThresholdConfig, KeyboardConfig, EmotivConfig
from .core.events import EEGEvent, MentalCommandEvent, ConnectionEvent, MentalCommand
from .core.exceptions import (
    BCIError,
    ConnectionError,
    ConfigurationError,
    DeviceNotFoundError,
    WindowNotFoundError,
)
from .core.factory import (
    create_pipeline,
    create_pipeline_from_yaml,
    create_pipeline_from_env,
    create_source,
    create_processors,
    create_publishers,
)

# Sources
from .sources.base import EEGSource
from .sources.mock import MockSource

# Processors
from .processors.base import Processor
from .processors.threshold import ThresholdProcessor
from .processors.debounce import DebounceProcessor
from .processors.mapper import CommandMapper

# Publishers
from .publishers.base import Publisher
from .publishers.console import ConsolePublisher

# Keyboard publisher (may not be available on non-Windows)
try:
    from .publishers.keyboard import KeyboardPublisher, create_keyboard_publisher
except ImportError:
    KeyboardPublisher = None
    create_keyboard_publisher = None

# Emotiv source (may not be available if websocket not installed)
try:
    from .sources.emotiv import EmotivSource
except ImportError:
    EmotivSource = None

# Legacy controller (deprecated, for backwards compatibility)
try:
    from .emotiv_controller import EmotivController
except ImportError:
    EmotivController = None

__all__ = [
    # Version
    "__version__",
    # Core
    "BCIPipeline",
    "Config",
    "ThresholdConfig",
    "KeyboardConfig",
    "EmotivConfig",
    # Events
    "EEGEvent",
    "MentalCommandEvent",
    "ConnectionEvent",
    "MentalCommand",
    # Exceptions
    "BCIError",
    "ConnectionError",
    "ConfigurationError",
    "DeviceNotFoundError",
    "WindowNotFoundError",
    # Factory functions
    "create_pipeline",
    "create_pipeline_from_yaml",
    "create_pipeline_from_env",
    "create_source",
    "create_processors",
    "create_publishers",
    # Sources
    "EEGSource",
    "EmotivSource",
    "MockSource",
    # Processors
    "Processor",
    "ThresholdProcessor",
    "DebounceProcessor",
    "CommandMapper",
    # Publishers
    "Publisher",
    "ConsolePublisher",
    "KeyboardPublisher",
    "create_keyboard_publisher",
    # Legacy (deprecated)
    "EmotivController",
]
