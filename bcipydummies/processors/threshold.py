"""Threshold-based filtering processor.

This module provides a processor that filters out mental command events
that don't meet configurable power thresholds. Different commands can
have different threshold requirements.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from bcipydummies.core.events import EEGEvent, MentalCommand, MentalCommandEvent
from bcipydummies.processors.base import Processor


@dataclass
class ThresholdConfig:
    """Configuration for the ThresholdProcessor.

    Attributes:
        thresholds: Mapping of command names (lowercase) to minimum power
                    thresholds (0.0 to 1.0). Commands not in this mapping
                    use the default_threshold.
        default_threshold: Threshold for commands not explicitly configured.
                          Defaults to 0.0 (pass all).

    Example:
        >>> config = ThresholdConfig(
        ...     thresholds={"left": 0.8, "right": 0.5, "lift": 0.7},
        ...     default_threshold=0.3
        ... )
    """
    thresholds: Dict[str, float] = field(default_factory=dict)
    default_threshold: float = 0.0

    def __post_init__(self) -> None:
        """Validate threshold values are within valid range."""
        for command, threshold in self.thresholds.items():
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(
                    f"Threshold for '{command}' must be between 0.0 and 1.0, "
                    f"got {threshold}"
                )
        if not 0.0 <= self.default_threshold <= 1.0:
            raise ValueError(
                f"Default threshold must be between 0.0 and 1.0, "
                f"got {self.default_threshold}"
            )


class ThresholdProcessor(Processor):
    """Filters events below configurable power thresholds.

    This processor examines the power level of incoming MentalCommandEvents
    and filters out those that don't meet the configured threshold for
    their command type.

    Non-MentalCommandEvent events pass through unchanged.

    Attributes:
        config: The threshold configuration.

    Example:
        >>> processor = ThresholdProcessor(thresholds={"left": 0.8})
        >>>
        >>> # This event passes (power >= threshold)
        >>> event1 = MentalCommandEvent(command=MentalCommand.LEFT, power=0.85)
        >>> processor.process(event1)  # Returns event1
        >>>
        >>> # This event is filtered (power < threshold)
        >>> event2 = MentalCommandEvent(command=MentalCommand.LEFT, power=0.5)
        >>> processor.process(event2)  # Returns None
    """

    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        default_threshold: float = 0.0,
        config: Optional[ThresholdConfig] = None,
    ) -> None:
        """Initialize the threshold processor.

        Args:
            thresholds: Mapping of command names to thresholds.
                       Ignored if config is provided.
            default_threshold: Default threshold for unconfigured commands.
                              Ignored if config is provided.
            config: Complete configuration object. If provided, thresholds
                   and default_threshold parameters are ignored.
        """
        if config is not None:
            self.config = config
        else:
            self.config = ThresholdConfig(
                thresholds=thresholds or {},
                default_threshold=default_threshold,
            )

    def _get_threshold(self, command: MentalCommand) -> float:
        """Get the threshold for a specific command.

        Args:
            command: The mental command to look up.

        Returns:
            The configured threshold, or default if not configured.
        """
        command_name = command.name.lower()
        return self.config.thresholds.get(
            command_name,
            self.config.default_threshold
        )

    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        """Filter events below their command's power threshold.

        Args:
            event: The event to process.

        Returns:
            The event if it meets the threshold, None otherwise.
            Non-MentalCommandEvent events always pass through.
        """
        # Pass through non-mental-command events
        if not isinstance(event, MentalCommandEvent):
            return event

        threshold = self._get_threshold(event.command)

        if event.power >= threshold:
            return event

        return None

    def reset(self) -> None:
        """Reset processor state.

        ThresholdProcessor is stateless, so this is a no-op.
        """
        pass
