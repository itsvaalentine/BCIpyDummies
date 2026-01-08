"""Mock EEG source for testing and development.

This module provides a MockSource that generates synthetic EEG events
without requiring actual hardware. It's useful for:
- Unit and integration testing
- UI development without hardware
- Demos and documentation examples
- Simulating specific event sequences
"""

import logging
import random
import threading
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence, Union

from bcipydummies.core.events import (
    ConnectionEvent,
    EEGEvent,
    MentalCommand,
    MentalCommandEvent,
)
from bcipydummies.sources.base import BaseEEGSource


logger = logging.getLogger(__name__)


@dataclass
class ScriptedEvent:
    """A scripted event to emit at a specific time.

    Attributes:
        delay: Seconds to wait before emitting this event.
        command: The mental command to emit.
        power: The power level (0.0 to 1.0).
    """

    delay: float
    command: MentalCommand
    power: float = 0.8


class MockSource(BaseEEGSource):
    """Mock EEG source for testing and development.

    This source generates synthetic mental command events without
    requiring actual EEG hardware. It supports two modes:

    1. Random mode: Generates random commands at regular intervals
    2. Scripted mode: Plays back a predefined sequence of events

    Example - Random mode:
        >>> source = MockSource()
        >>> source.subscribe(lambda e: print(e))
        >>> source.connect()
        >>> time.sleep(5)  # Receive random events for 5 seconds
        >>> source.disconnect()

    Example - Scripted mode:
        >>> script = [
        ...     ScriptedEvent(0.0, MentalCommand.NEUTRAL, 0.9),
        ...     ScriptedEvent(1.0, MentalCommand.PUSH, 0.8),
        ...     ScriptedEvent(0.5, MentalCommand.LEFT, 0.7),
        ...     ScriptedEvent(2.0, MentalCommand.NEUTRAL, 0.9),
        ... ]
        >>> source = MockSource(script=script)
        >>> source.subscribe(lambda e: print(e))
        >>> source.connect()
        >>> # Events will be emitted according to the script
    """

    def __init__(
        self,
        source_id: str = "mock-source",
        script: Optional[Sequence[ScriptedEvent]] = None,
        random_commands: Optional[List[MentalCommand]] = None,
        random_interval: float = 1.0,
        random_power_range: tuple[float, float] = (0.5, 1.0),
        loop_script: bool = False,
    ) -> None:
        """Initialize the mock source.

        Args:
            source_id: Identifier for this source instance.
            script: Optional sequence of scripted events to play.
                   If None, random mode is used.
            random_commands: Commands to choose from in random mode.
                            Defaults to common commands (push, pull, left, right).
            random_interval: Seconds between random events.
            random_power_range: Min and max power for random events.
            loop_script: Whether to loop the script or stop after one pass.
        """
        super().__init__(source_id)

        self._script = list(script) if script else None
        self._random_commands = random_commands or [
            MentalCommand.NEUTRAL,
            MentalCommand.PUSH,
            MentalCommand.PULL,
            MentalCommand.LEFT,
            MentalCommand.RIGHT,
            MentalCommand.LIFT,
        ]
        self._random_interval = random_interval
        self._random_power_range = random_power_range
        self._loop_script = loop_script

        # Threading control
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_scripted(self) -> bool:
        """Whether this source is in scripted mode."""
        return self._script is not None

    def connect(self) -> None:
        """Start generating mock events.

        Emits a ConnectionEvent and begins the event generation thread.
        """
        if self._connected:
            logger.warning("MockSource already connected")
            return

        logger.info(f"MockSource connecting (mode: {'scripted' if self._script else 'random'})")

        self._connected = True
        self._stop_event.clear()

        # Emit connection event
        self._emit(ConnectionEvent(connected=True, message="Mock source connected"))

        # Start event generation thread
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f"MockSource-{self._source_id}",
        )
        self._thread.start()

    def disconnect(self) -> None:
        """Stop generating mock events.

        Stops the event generation thread and emits a disconnection event.
        """
        if not self._connected:
            return

        logger.info("MockSource disconnecting")

        self._stop_event.set()
        self._connected = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._emit(ConnectionEvent(connected=False, message="Mock source disconnected"))

    def emit_command(self, command: MentalCommand, power: float = 0.8) -> None:
        """Manually emit a mental command event.

        Useful for testing specific scenarios programmatically.

        Args:
            command: The mental command to emit.
            power: The power level (0.0 to 1.0).
        """
        if not self._connected:
            logger.warning("Cannot emit: MockSource not connected")
            return

        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id=self._source_id,
            command=command,
            power=max(0.0, min(1.0, power)),
        )
        self._emit(event)

    def _run(self) -> None:
        """Main loop for generating events."""
        if self._script:
            self._run_scripted()
        else:
            self._run_random()

    def _run_scripted(self) -> None:
        """Run scripted event sequence."""
        if not self._script:
            return

        while not self._stop_event.is_set():
            for scripted_event in self._script:
                if self._stop_event.wait(timeout=scripted_event.delay):
                    return  # Stop signal received

                if not self._connected:
                    return

                self.emit_command(scripted_event.command, scripted_event.power)

            if not self._loop_script:
                logger.info("Script completed")
                return

    def _run_random(self) -> None:
        """Generate random events."""
        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=self._random_interval):
                return  # Stop signal received

            if not self._connected:
                return

            command = random.choice(self._random_commands)
            power = random.uniform(*self._random_power_range)

            self.emit_command(command, power)

    def __enter__(self) -> "MockSource":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()


def create_test_script(
    commands: Sequence[Union[MentalCommand, str]],
    interval: float = 1.0,
    power: float = 0.8,
) -> List[ScriptedEvent]:
    """Helper function to create a scripted event sequence.

    Args:
        commands: Sequence of commands (enum values or strings).
        interval: Delay between each command.
        power: Power level for all commands.

    Returns:
        List of ScriptedEvent objects ready for MockSource.

    Example:
        >>> script = create_test_script(
        ...     ["neutral", "push", "left", "right", "neutral"],
        ...     interval=0.5,
        ... )
        >>> source = MockSource(script=script)
    """
    events = []
    for i, cmd in enumerate(commands):
        if isinstance(cmd, str):
            cmd = MentalCommand.from_string(cmd)

        events.append(ScriptedEvent(
            delay=0.0 if i == 0 else interval,
            command=cmd,
            power=power,
        ))

    return events


class ReplaySource(MockSource):
    """Mock source that replays recorded event sequences.

    This is useful for replaying actual recorded sessions for testing
    or for creating reproducible test scenarios.

    Example:
        >>> # Record events from a real source
        >>> recorded = []
        >>> real_source.subscribe(lambda e: recorded.append(e))
        >>>
        >>> # Later, replay them
        >>> replay = ReplaySource(recorded)
        >>> replay.subscribe(my_handler)
        >>> replay.connect()
    """

    def __init__(
        self,
        events: Sequence[MentalCommandEvent],
        source_id: str = "replay-source",
        speed_multiplier: float = 1.0,
    ) -> None:
        """Initialize the replay source.

        Args:
            events: Sequence of recorded MentalCommandEvent objects.
            source_id: Identifier for this source.
            speed_multiplier: Speed up (>1) or slow down (<1) playback.
        """
        self._recorded_events = list(events)
        self._speed_multiplier = speed_multiplier

        # Convert recorded events to scripted events with timing
        script = self._convert_to_script()
        super().__init__(source_id=source_id, script=script, loop_script=False)

    def _convert_to_script(self) -> List[ScriptedEvent]:
        """Convert recorded events to scripted events with timing."""
        if not self._recorded_events:
            return []

        script = []
        prev_timestamp = self._recorded_events[0].timestamp

        for event in self._recorded_events:
            delay = (event.timestamp - prev_timestamp) / self._speed_multiplier
            prev_timestamp = event.timestamp

            script.append(ScriptedEvent(
                delay=max(0.0, delay),
                command=event.command,
                power=event.power,
            ))

        return script
