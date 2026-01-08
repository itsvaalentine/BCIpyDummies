"""Configuration management for BCIpyDummies.

This module provides configuration dataclasses and utilities for loading
configuration from YAML files and environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .exceptions import ConfigurationError


@dataclass(frozen=True)
class ThresholdConfig:
    """Configuration for mental command thresholds.

    Thresholds determine the minimum power level required for a
    mental command to trigger an action.

    Attributes:
        default: Default threshold for all commands (0.0 to 1.0).
        push: Optional override threshold for PUSH command.
        pull: Optional override threshold for PULL command.
        lift: Optional override threshold for LIFT command.
        drop: Optional override threshold for DROP command.
        left: Optional override threshold for LEFT command.
        right: Optional override threshold for RIGHT command.
        rotate_left: Optional override threshold for ROTATE_LEFT command.
        rotate_right: Optional override threshold for ROTATE_RIGHT command.
        disappear: Optional override threshold for DISAPPEAR command.
    """

    default: float = 0.5
    push: Optional[float] = None
    pull: Optional[float] = None
    lift: Optional[float] = None
    drop: Optional[float] = None
    left: Optional[float] = None
    right: Optional[float] = None
    rotate_left: Optional[float] = None
    rotate_right: Optional[float] = None
    disappear: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate all threshold values are within acceptable range."""
        for attr_name in [
            "default",
            "push",
            "pull",
            "lift",
            "drop",
            "left",
            "right",
            "rotate_left",
            "rotate_right",
            "disappear",
        ]:
            value = getattr(self, attr_name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Threshold '{attr_name}' must be between 0.0 and 1.0, got {value}"
                )

    def get_threshold(self, command_name: str) -> float:
        """Get the threshold for a specific command.

        Args:
            command_name: Name of the command (case-insensitive).

        Returns:
            The command-specific threshold if set, otherwise the default.
        """
        attr_name = command_name.lower()
        specific_threshold = getattr(self, attr_name, None)
        return specific_threshold if specific_threshold is not None else self.default


@dataclass(frozen=True)
class KeyboardConfig:
    """Configuration for keyboard input simulation.

    Maps mental commands to keyboard keys for input simulation.

    Attributes:
        push: Key to press for PUSH command.
        pull: Key to press for PULL command.
        lift: Key to press for LIFT command.
        drop: Key to press for DROP command.
        left: Key to press for LEFT command.
        right: Key to press for RIGHT command.
        rotate_left: Key to press for ROTATE_LEFT command.
        rotate_right: Key to press for ROTATE_RIGHT command.
        disappear: Key to press for DISAPPEAR command.
    """

    push: Optional[str] = None
    pull: Optional[str] = None
    lift: Optional[str] = None
    drop: Optional[str] = None
    left: Optional[str] = None
    right: Optional[str] = None
    rotate_left: Optional[str] = None
    rotate_right: Optional[str] = None
    disappear: Optional[str] = None

    def get_key(self, command_name: str) -> Optional[str]:
        """Get the mapped key for a specific command.

        Args:
            command_name: Name of the command (case-insensitive).

        Returns:
            The mapped key if configured, otherwise None.
        """
        attr_name = command_name.lower()
        return getattr(self, attr_name, None)


@dataclass(frozen=True)
class EmotivConfig:
    """Configuration for Emotiv Cortex API connection.

    Credentials can be provided directly or loaded from environment variables.
    Environment variables take precedence when from_env() is used.

    Attributes:
        client_id: Emotiv Cortex API client ID.
        client_secret: Emotiv Cortex API client secret.
        headset_id: Optional specific headset ID to connect to.
        profile: Optional trained profile name to load.
    """

    client_id: str
    client_secret: str
    headset_id: Optional[str] = None
    profile: Optional[str] = None

    # Environment variable names
    ENV_CLIENT_ID: str = field(default="EMOTIV_CLIENT_ID", repr=False, compare=False)
    ENV_CLIENT_SECRET: str = field(
        default="EMOTIV_CLIENT_SECRET", repr=False, compare=False
    )
    ENV_HEADSET_ID: str = field(default="EMOTIV_HEADSET_ID", repr=False, compare=False)
    ENV_PROFILE: str = field(default="EMOTIV_PROFILE", repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate required credentials are provided."""
        if not self.client_id:
            raise ConfigurationError("Emotiv client_id is required")
        if not self.client_secret:
            raise ConfigurationError("Emotiv client_secret is required")

    @classmethod
    def from_env(cls) -> EmotivConfig:
        """Create EmotivConfig from environment variables.

        Reads credentials from the following environment variables:
        - EMOTIV_CLIENT_ID (required)
        - EMOTIV_CLIENT_SECRET (required)
        - EMOTIV_HEADSET_ID (optional)
        - EMOTIV_PROFILE (optional)

        Returns:
            EmotivConfig instance populated from environment.

        Raises:
            ConfigurationError: If required environment variables are not set.
        """
        client_id = os.environ.get("EMOTIV_CLIENT_ID", "")
        client_secret = os.environ.get("EMOTIV_CLIENT_SECRET", "")
        headset_id = os.environ.get("EMOTIV_HEADSET_ID")
        profile = os.environ.get("EMOTIV_PROFILE")

        if not client_id:
            raise ConfigurationError(
                "Environment variable EMOTIV_CLIENT_ID is required"
            )
        if not client_secret:
            raise ConfigurationError(
                "Environment variable EMOTIV_CLIENT_SECRET is required"
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            headset_id=headset_id,
            profile=profile,
        )


@dataclass
class Config:
    """Main configuration container for BCIpyDummies.

    Aggregates all configuration sections and provides factory methods
    for loading configuration from various sources.

    Attributes:
        emotiv: Emotiv device and API configuration.
        thresholds: Mental command threshold configuration.
        keyboard: Keyboard mapping configuration.
        target_window: Optional window title to send inputs to.
    """

    emotiv: EmotivConfig
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    target_window: Optional[str] = None

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            Config instance populated from the YAML file.

        Raises:
            ConfigurationError: If the file cannot be read or parsed.
        """
        try:
            import yaml
        except ImportError as e:
            raise ConfigurationError(
                "PyYAML is required for YAML configuration. "
                "Install it with: pip install pyyaml"
            ) from e

        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML file: {e}") from e

        if data is None:
            raise ConfigurationError("Configuration file is empty")

        return cls._from_dict(data)

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables.

        Loads Emotiv credentials from environment variables and uses
        default values for other configuration sections.

        Returns:
            Config instance with Emotiv config from environment.
        """
        return cls(emotiv=EmotivConfig.from_env())

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Config:
        """Create Config from a dictionary.

        Args:
            data: Configuration dictionary, typically from YAML or JSON.

        Returns:
            Config instance populated from the dictionary.

        Raises:
            ConfigurationError: If required fields are missing or invalid.
        """
        emotiv_data = data.get("emotiv", {})

        # Support environment variable fallback for credentials
        client_id = emotiv_data.get("client_id") or os.environ.get(
            "EMOTIV_CLIENT_ID", ""
        )
        client_secret = emotiv_data.get("client_secret") or os.environ.get(
            "EMOTIV_CLIENT_SECRET", ""
        )

        try:
            emotiv = EmotivConfig(
                client_id=client_id,
                client_secret=client_secret,
                headset_id=emotiv_data.get("headset_id"),
                profile=emotiv_data.get("profile"),
            )
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Invalid emotiv configuration: {e}") from e

        thresholds_data = data.get("thresholds", {})
        thresholds = ThresholdConfig(**thresholds_data) if thresholds_data else ThresholdConfig()

        keyboard_data = data.get("keyboard", {})
        keyboard = KeyboardConfig(**keyboard_data) if keyboard_data else KeyboardConfig()

        return cls(
            emotiv=emotiv,
            thresholds=thresholds,
            keyboard=keyboard,
            target_window=data.get("target_window"),
        )
