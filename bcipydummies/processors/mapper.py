"""Command-to-action mapping processor.

This module provides a processor that maps mental commands to action
strings (such as key names), transforming MentalCommandEvents to include
the mapped action.
"""

from dataclasses import dataclass, field, replace
from typing import Dict, Optional

from bcipydummies.core.events import EEGEvent, MentalCommand, MentalCommandEvent
from bcipydummies.processors.base import Processor


@dataclass
class MapperConfig:
    """Configuration for the CommandMapper.

    Attributes:
        mapping: Mapping of command names (lowercase) to action strings.
                Actions are typically key names like "A", "D", "SPACE".
        pass_unmapped: If True, unmapped commands pass through with
                      action=None. If False, unmapped commands are
                      filtered out. Defaults to True.

    Example:
        >>> config = MapperConfig(
        ...     mapping={
        ...         "left": "A",
        ...         "right": "D",
        ...         "lift": "SPACE",
        ...     },
        ...     pass_unmapped=False
        ... )
    """
    mapping: Dict[str, str] = field(default_factory=dict)
    pass_unmapped: bool = True


class CommandMapper(Processor):
    """Maps mental commands to action strings.

    This processor transforms MentalCommandEvents by adding an action
    field based on a configurable mapping dictionary. The action string
    typically represents a key name or other output action.

    Since MentalCommandEvent is frozen (immutable), this processor creates
    a new event instance with the action field populated.

    Non-MentalCommandEvent events pass through unchanged.

    Attributes:
        config: The mapper configuration.

    Example:
        >>> mapper = CommandMapper(mapping={"left": "A", "right": "D"})
        >>>
        >>> event = MentalCommandEvent(command=MentalCommand.LEFT, power=0.9)
        >>> mapped = mapper.process(event)
        >>> mapped.action
        'A'
    """

    def __init__(
        self,
        mapping: Optional[Dict[str, str]] = None,
        pass_unmapped: bool = True,
        config: Optional[MapperConfig] = None,
    ) -> None:
        """Initialize the command mapper.

        Args:
            mapping: Mapping of command names to action strings.
                    Ignored if config is provided.
            pass_unmapped: Whether to pass through unmapped commands.
                          Ignored if config is provided.
            config: Complete configuration object. If provided, mapping
                   and pass_unmapped parameters are ignored.
        """
        if config is not None:
            self.config = config
        else:
            self.config = MapperConfig(
                mapping=mapping or {},
                pass_unmapped=pass_unmapped,
            )

    def _get_action(self, command: MentalCommand) -> Optional[str]:
        """Get the action string for a specific command.

        Args:
            command: The mental command to look up.

        Returns:
            The mapped action string, or None if not mapped.
        """
        command_name = command.name.lower()
        return self.config.mapping.get(command_name)

    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        """Map command to action and create a new event with the action set.

        Args:
            event: The event to process.

        Returns:
            A new MentalCommandEvent with the action field populated,
            or None if the command is unmapped and pass_unmapped is False.
            Non-MentalCommandEvent events pass through unchanged.
        """
        # Pass through non-mental-command events
        if not isinstance(event, MentalCommandEvent):
            return event

        action = self._get_action(event.command)

        if action is None and not self.config.pass_unmapped:
            return None

        # Create a new event with the action field set
        # Using dataclasses.replace since MentalCommandEvent is frozen
        return replace(event, action=action)

    def reset(self) -> None:
        """Reset processor state.

        CommandMapper is stateless, so this is a no-op.
        """
        pass
