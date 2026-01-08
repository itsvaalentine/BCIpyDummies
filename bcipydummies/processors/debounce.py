"""Debounce processor to prevent rapid repeated commands.

This module provides a processor that enforces cooldown periods between
commands, preventing the same command from being processed too rapidly.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from bcipydummies.core.events import EEGEvent, MentalCommand, MentalCommandEvent
from bcipydummies.processors.base import Processor


@dataclass
class DebounceConfig:
    """Configuration for the DebounceProcessor.

    Attributes:
        cooldown: Default cooldown period in seconds between repeated
                  commands. Defaults to 0.3 seconds.
        per_command_cooldown: Optional mapping of command names (lowercase)
                             to specific cooldown periods. Commands not in
                             this mapping use the default cooldown.

    Example:
        >>> config = DebounceConfig(
        ...     cooldown=0.3,
        ...     per_command_cooldown={"lift": 0.5, "left": 0.2}
        ... )
    """
    cooldown: float = 0.3
    per_command_cooldown: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate cooldown values are non-negative."""
        if self.cooldown < 0:
            raise ValueError(
                f"Cooldown must be non-negative, got {self.cooldown}"
            )
        for command, cd in self.per_command_cooldown.items():
            if cd < 0:
                raise ValueError(
                    f"Cooldown for '{command}' must be non-negative, got {cd}"
                )


class DebounceProcessor(Processor):
    """Prevents rapid repeated commands by enforcing cooldown periods.

    This processor tracks the last time each command was processed and
    filters out commands that arrive before the cooldown period has elapsed.

    Non-MentalCommandEvent events pass through unchanged.

    Attributes:
        config: The debounce configuration.

    Example:
        >>> processor = DebounceProcessor(cooldown=0.3)
        >>>
        >>> event1 = MentalCommandEvent(command=MentalCommand.LEFT, power=0.9)
        >>> processor.process(event1)  # Returns event1 (first occurrence)
        >>>
        >>> # Immediately after...
        >>> event2 = MentalCommandEvent(command=MentalCommand.LEFT, power=0.9)
        >>> processor.process(event2)  # Returns None (within cooldown)
        >>>
        >>> # After waiting 0.3 seconds...
        >>> event3 = MentalCommandEvent(command=MentalCommand.LEFT, power=0.9)
        >>> processor.process(event3)  # Returns event3 (cooldown elapsed)
    """

    def __init__(
        self,
        cooldown: float = 0.3,
        per_command_cooldown: Optional[Dict[str, float]] = None,
        config: Optional[DebounceConfig] = None,
        time_source: Optional[callable] = None,
    ) -> None:
        """Initialize the debounce processor.

        Args:
            cooldown: Default cooldown period in seconds.
                     Ignored if config is provided.
            per_command_cooldown: Per-command cooldown overrides.
                                 Ignored if config is provided.
            config: Complete configuration object. If provided, cooldown
                   and per_command_cooldown parameters are ignored.
            time_source: Optional callable returning current time (for testing).
                        Defaults to time.time.
        """
        if config is not None:
            self.config = config
        else:
            self.config = DebounceConfig(
                cooldown=cooldown,
                per_command_cooldown=per_command_cooldown or {},
            )

        self._time_source = time_source or time.time
        self._last_command_times: Dict[MentalCommand, float] = {}

    def _get_cooldown(self, command: MentalCommand) -> float:
        """Get the cooldown period for a specific command.

        Args:
            command: The mental command to look up.

        Returns:
            The configured cooldown, or default if not configured.
        """
        command_name = command.name.lower()
        return self.config.per_command_cooldown.get(
            command_name,
            self.config.cooldown
        )

    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        """Filter events that arrive within the cooldown period.

        Args:
            event: The event to process.

        Returns:
            The event if cooldown has elapsed, None otherwise.
            Non-MentalCommandEvent events always pass through.
        """
        # Pass through non-mental-command events
        if not isinstance(event, MentalCommandEvent):
            return event

        current_time = self._time_source()
        command = event.command
        cooldown = self._get_cooldown(command)

        last_time = self._last_command_times.get(command)

        if last_time is not None:
            elapsed = current_time - last_time
            if elapsed < cooldown:
                return None

        # Update the last command time and pass through
        self._last_command_times[command] = current_time
        return event

    def reset(self) -> None:
        """Reset the debounce state, clearing all command timing history."""
        self._last_command_times.clear()
