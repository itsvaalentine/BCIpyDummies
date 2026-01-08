"""Factory functions for creating BCI pipeline components.

This module provides factory functions that create pipeline components
based on configuration. These functions encapsulate the logic for
selecting appropriate implementations and configuring them correctly.

The factories decouple component creation from usage, enabling:
- Configuration-driven pipeline construction
- Easy testing with mock components
- Support for new implementations without changing client code

Usage:
    >>> from bcipydummies.core.config import Config
    >>> from bcipydummies.core.factory import create_pipeline
    >>>
    >>> config = Config.from_yaml("config.yaml")
    >>> pipeline = create_pipeline(config)
    >>> pipeline.start()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Type

from bcipydummies.core.config import Config
from bcipydummies.core.engine import BCIPipeline
from bcipydummies.core.exceptions import ConfigurationError
from bcipydummies.processors.base import Processor
from bcipydummies.publishers.base import Publisher
from bcipydummies.sources.base import EEGSource

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


# Registry of available source types
# Maps source type name to source class
_SOURCE_REGISTRY: Dict[str, Type[EEGSource]] = {}


# Registry of available processor types
# Maps processor type name to processor class
_PROCESSOR_REGISTRY: Dict[str, Type[Processor]] = {}


# Registry of available publisher types
# Maps publisher type name to publisher class
_PUBLISHER_REGISTRY: Dict[str, Type[Publisher]] = {}


def register_source(name: str, source_class: Type[EEGSource]) -> None:
    """Register a source implementation for factory use.

    Args:
        name: Name to register the source under (e.g., "emotiv", "simulated").
        source_class: The source class to register.
    """
    _SOURCE_REGISTRY[name.lower()] = source_class
    logger.debug("Registered source: %s -> %s", name, source_class.__name__)


def register_processor(name: str, processor_class: Type[Processor]) -> None:
    """Register a processor implementation for factory use.

    Args:
        name: Name to register the processor under (e.g., "threshold", "debounce").
        processor_class: The processor class to register.
    """
    _PROCESSOR_REGISTRY[name.lower()] = processor_class
    logger.debug("Registered processor: %s -> %s", name, processor_class.__name__)


def register_publisher(name: str, publisher_class: Type[Publisher]) -> None:
    """Register a publisher implementation for factory use.

    Args:
        name: Name to register the publisher under (e.g., "console", "keyboard").
        publisher_class: The publisher class to register.
    """
    _PUBLISHER_REGISTRY[name.lower()] = publisher_class
    logger.debug("Registered publisher: %s -> %s", name, publisher_class.__name__)


def _register_defaults() -> None:
    """Register default implementations from the library.

    This function is called automatically on first use of factory functions.
    It populates the registries with built-in implementations.
    """
    # Register processors
    try:
        from bcipydummies.processors import (
            ThresholdProcessor,
            DebounceProcessor,
            CommandMapper,
        )
        register_processor("threshold", ThresholdProcessor)
        register_processor("debounce", DebounceProcessor)
        register_processor("mapper", CommandMapper)
        register_processor("command_mapper", CommandMapper)
    except ImportError as e:
        logger.debug("Could not import processors: %s", e)

    # Register publishers
    try:
        from bcipydummies.publishers import ConsolePublisher
        register_publisher("console", ConsolePublisher)
    except ImportError as e:
        logger.debug("Could not import ConsolePublisher: %s", e)

    try:
        from bcipydummies.publishers.keyboard import create_keyboard_publisher
        # Note: keyboard publisher requires special handling
        # Register a placeholder - actual creation uses create_keyboard_publisher
        pass
    except ImportError as e:
        logger.debug("Could not import keyboard publisher: %s", e)


# Track whether defaults have been registered
_defaults_registered = False


def _ensure_defaults_registered() -> None:
    """Ensure default implementations are registered."""
    global _defaults_registered
    if not _defaults_registered:
        _register_defaults()
        _defaults_registered = True


def create_source(source_type: str, config: Config) -> EEGSource:
    """Create an EEG source based on type and configuration.

    This factory function creates the appropriate source implementation
    based on the requested type. It handles configuration mapping and
    dependency injection.

    Args:
        source_type: Type of source to create. Supported values:
            - "emotiv": Emotiv Cortex API source
            - "simulated": Simulated source for testing
        config: Configuration containing source settings.

    Returns:
        A configured EEGSource instance.

    Raises:
        ConfigurationError: If the source type is unknown or config is invalid.

    Example:
        >>> config = Config.from_env()
        >>> source = create_source("emotiv", config)
    """
    _ensure_defaults_registered()

    source_type = source_type.lower()
    logger.debug("Creating source of type: %s", source_type)

    if source_type == "emotiv":
        return _create_emotiv_source(config)
    elif source_type == "simulated":
        return _create_simulated_source(config)
    elif source_type in _SOURCE_REGISTRY:
        source_class = _SOURCE_REGISTRY[source_type]
        # Generic instantiation - may need config adaptation
        return source_class(source_id=f"{source_type}-source")
    else:
        available = list(_SOURCE_REGISTRY.keys()) + ["emotiv", "simulated"]
        raise ConfigurationError(
            f"Unknown source type: '{source_type}'. "
            f"Available types: {', '.join(sorted(set(available)))}"
        )


def _create_emotiv_source(config: Config) -> EEGSource:
    """Create an Emotiv source from configuration.

    Args:
        config: Configuration with Emotiv settings.

    Returns:
        Configured EmotivSource instance.

    Raises:
        ConfigurationError: If Emotiv source cannot be created.
    """
    try:
        from bcipydummies.sources.emotiv import EmotivSource
    except ImportError as e:
        raise ConfigurationError(
            "Emotiv source requires additional dependencies. "
            "Install with: pip install bcipydummies[emotiv]"
        ) from e

    return EmotivSource(
        client_id=config.emotiv.client_id,
        client_secret=config.emotiv.client_secret,
        headset_id=config.emotiv.headset_id,
        profile=config.emotiv.profile,
    )


def _create_simulated_source(config: Config) -> EEGSource:
    """Create a simulated source for testing.

    Args:
        config: Configuration (mostly ignored for simulated source).

    Returns:
        Configured SimulatedSource instance.

    Raises:
        ConfigurationError: If simulated source cannot be created.
    """
    try:
        from bcipydummies.sources.simulated import SimulatedSource
    except ImportError:
        # Provide a basic simulated source inline
        return _create_basic_simulated_source()

    return SimulatedSource()


def _create_basic_simulated_source() -> EEGSource:
    """Create a basic simulated source when the full implementation is unavailable.

    Returns:
        A basic simulated source for testing.
    """
    from bcipydummies.sources.base import BaseEEGSource
    from bcipydummies.core.events import MentalCommand, MentalCommandEvent
    import threading
    import time
    import random

    class BasicSimulatedSource(BaseEEGSource):
        """Basic simulated source that emits random mental commands."""

        def __init__(self) -> None:
            super().__init__("simulated-basic")
            self._thread: Optional[threading.Thread] = None
            self._stop_event = threading.Event()

        def connect(self) -> None:
            if self._connected:
                return
            self._connected = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._emit_loop, daemon=True)
            self._thread.start()

        def disconnect(self) -> None:
            if not self._connected:
                return
            self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=2.0)
            self._connected = False

        def _emit_loop(self) -> None:
            commands = list(MentalCommand)
            while not self._stop_event.wait(timeout=0.5):
                command = random.choice(commands)
                power = random.uniform(0.3, 1.0)
                event = MentalCommandEvent(
                    source_id=self._source_id,
                    command=command,
                    power=power,
                )
                self._emit(event)

    return BasicSimulatedSource()


def create_processors(config: Config) -> List[Processor]:
    """Create the standard processor chain from configuration.

    This function creates processors based on the configuration,
    setting up the typical processing pipeline:
        1. ThresholdProcessor - Filter low-confidence commands
        2. DebounceProcessor - Prevent rapid-fire commands
        3. CommandMapper - Map commands to actions (optional)

    Args:
        config: Configuration containing processor settings.

    Returns:
        List of configured processor instances.

    Example:
        >>> config = Config.from_yaml("config.yaml")
        >>> processors = create_processors(config)
        >>> for p in processors:
        ...     print(type(p).__name__)
        ThresholdProcessor
        DebounceProcessor
    """
    _ensure_defaults_registered()

    processors: List[Processor] = []
    logger.debug("Creating processor chain from config")

    # Create threshold processor
    try:
        from bcipydummies.processors import ThresholdProcessor

        # Build thresholds dict from config
        thresholds = {}
        for command_name in [
            "push", "pull", "lift", "drop", "left", "right",
            "rotate_left", "rotate_right", "disappear"
        ]:
            threshold = getattr(config.thresholds, command_name, None)
            if threshold is not None:
                thresholds[command_name] = threshold

        threshold_proc = ThresholdProcessor(
            thresholds=thresholds,
            default_threshold=config.thresholds.default,
        )
        processors.append(threshold_proc)
        logger.debug("Created ThresholdProcessor with %d thresholds", len(thresholds))
    except ImportError as e:
        logger.warning("Could not create ThresholdProcessor: %s", e)

    # Create debounce processor
    try:
        from bcipydummies.processors import DebounceProcessor

        debounce_proc = DebounceProcessor(cooldown=0.3)  # 300ms default cooldown
        processors.append(debounce_proc)
        logger.debug("Created DebounceProcessor")
    except ImportError as e:
        logger.warning("Could not create DebounceProcessor: %s", e)

    return processors


def create_publishers(config: Config) -> List[Publisher]:
    """Create publishers from configuration.

    This function creates publishers based on the configuration.
    By default, it creates:
        - ConsolePublisher (always, for debugging)
        - KeyboardPublisher (if target_window is configured)

    Args:
        config: Configuration containing publisher settings.

    Returns:
        List of configured publisher instances.

    Example:
        >>> config = Config.from_yaml("config.yaml")
        >>> publishers = create_publishers(config)
    """
    _ensure_defaults_registered()

    publishers: List[Publisher] = []
    logger.debug("Creating publishers from config")

    # Always create console publisher for visibility
    try:
        from bcipydummies.publishers import ConsolePublisher

        console_pub = ConsolePublisher(prefix="[BCI]")
        publishers.append(console_pub)
        logger.debug("Created ConsolePublisher")
    except ImportError as e:
        logger.warning("Could not create ConsolePublisher: %s", e)

    # Create keyboard publisher if target window is configured
    if config.target_window:
        try:
            from bcipydummies.publishers.keyboard import create_keyboard_publisher

            keyboard_pub = create_keyboard_publisher(
                window_name=config.target_window,
                key_mapping=_build_key_mapping(config),
            )
            publishers.append(keyboard_pub)
            logger.debug(
                "Created KeyboardPublisher for window: %s",
                config.target_window
            )
        except ImportError as e:
            logger.warning("Could not create KeyboardPublisher: %s", e)
        except Exception as e:
            logger.error("Failed to create KeyboardPublisher: %s", e)

    return publishers


def _build_key_mapping(config: Config) -> Dict[str, str]:
    """Build a command-to-key mapping from configuration.

    Args:
        config: Configuration with keyboard mappings.

    Returns:
        Dict mapping command names to key names.
    """
    mapping = {}
    for command_name in [
        "push", "pull", "lift", "drop", "left", "right",
        "rotate_left", "rotate_right", "disappear"
    ]:
        key = getattr(config.keyboard, command_name, None)
        if key:
            mapping[command_name] = key
    return mapping


def create_pipeline(config: Config, source_type: str = "emotiv") -> BCIPipeline:
    """Create a complete BCI pipeline from configuration.

    This is the main factory function for creating a fully configured
    pipeline. It creates and wires together:
        - EEG source (based on source_type)
        - Processor chain
        - Publishers

    Args:
        config: Configuration for all components.
        source_type: Type of source to create (default: "emotiv").
            Supported: "emotiv", "simulated"

    Returns:
        A configured BCIPipeline ready to start.

    Raises:
        ConfigurationError: If any component cannot be created.

    Example:
        >>> config = Config.from_yaml("config.yaml")
        >>> pipeline = create_pipeline(config)
        >>>
        >>> with pipeline:
        ...     input("Press Enter to stop...")
    """
    logger.info("Creating BCI pipeline with source type: %s", source_type)

    # Create components
    source = create_source(source_type, config)
    processors = create_processors(config)
    publishers = create_publishers(config)

    # Assemble pipeline
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=publishers,
    )

    logger.info(
        "Pipeline created: source=%s, processors=%d, publishers=%d",
        source.source_id,
        len(processors),
        len(publishers),
    )

    return pipeline


def create_pipeline_from_yaml(yaml_path: str, source_type: str = "emotiv") -> BCIPipeline:
    """Create a pipeline from a YAML configuration file.

    Convenience function that loads config from YAML and creates a pipeline.

    Args:
        yaml_path: Path to the YAML configuration file.
        source_type: Type of source to create.

    Returns:
        A configured BCIPipeline ready to start.

    Raises:
        ConfigurationError: If config cannot be loaded or pipeline cannot be created.

    Example:
        >>> pipeline = create_pipeline_from_yaml("config.yaml")
        >>> pipeline.start()
    """
    config = Config.from_yaml(yaml_path)
    return create_pipeline(config, source_type)


def create_pipeline_from_env(source_type: str = "emotiv") -> BCIPipeline:
    """Create a pipeline from environment variables.

    Convenience function that loads config from environment and creates a pipeline.
    Uses default settings for processors and publishers.

    Args:
        source_type: Type of source to create.

    Returns:
        A configured BCIPipeline ready to start.

    Raises:
        ConfigurationError: If required env vars are missing or pipeline cannot be created.

    Example:
        >>> # Set EMOTIV_CLIENT_ID and EMOTIV_CLIENT_SECRET in environment
        >>> pipeline = create_pipeline_from_env()
        >>> pipeline.start()
    """
    config = Config.from_env()
    return create_pipeline(config, source_type)


# Convenience aliases
def get_available_sources() -> List[str]:
    """Get list of available source types.

    Returns:
        List of registered source type names.
    """
    _ensure_defaults_registered()
    return sorted(set(list(_SOURCE_REGISTRY.keys()) + ["emotiv", "simulated"]))


def get_available_processors() -> List[str]:
    """Get list of available processor types.

    Returns:
        List of registered processor type names.
    """
    _ensure_defaults_registered()
    return sorted(_PROCESSOR_REGISTRY.keys())


def get_available_publishers() -> List[str]:
    """Get list of available publisher types.

    Returns:
        List of registered publisher type names.
    """
    _ensure_defaults_registered()
    return sorted(set(list(_PUBLISHER_REGISTRY.keys()) + ["console", "keyboard"]))
