"""Comprehensive tests for BCIpyDummies processors module.

Tests cover:
- ThresholdProcessor: Power-based event filtering
- DebounceProcessor: Cooldown-based command rate limiting
- CommandMapper: Command-to-action string mapping
"""

import pytest
from unittest.mock import MagicMock

from bcipydummies.core.events import (
    EEGEvent,
    MentalCommand,
    MentalCommandEvent,
)
from bcipydummies.processors import (
    ThresholdProcessor,
    ThresholdConfig,
    DebounceProcessor,
    DebounceConfig,
    CommandMapper,
    MapperConfig,
)


# ===========================================================
# FIXTURES
# ===========================================================


@pytest.fixture
def sample_timestamp() -> float:
    """Standard timestamp for test events."""
    return 1000.0


@pytest.fixture
def sample_source_id() -> str:
    """Standard source ID for test events."""
    return "test-headset"


@pytest.fixture
def left_command_event(sample_timestamp, sample_source_id) -> MentalCommandEvent:
    """A LEFT command event with power 0.9."""
    return MentalCommandEvent(
        timestamp=sample_timestamp,
        source_id=sample_source_id,
        command=MentalCommand.LEFT,
        power=0.9,
    )


@pytest.fixture
def right_command_event(sample_timestamp, sample_source_id) -> MentalCommandEvent:
    """A RIGHT command event with power 0.7."""
    return MentalCommandEvent(
        timestamp=sample_timestamp,
        source_id=sample_source_id,
        command=MentalCommand.RIGHT,
        power=0.7,
    )


@pytest.fixture
def weak_left_event(sample_timestamp, sample_source_id) -> MentalCommandEvent:
    """A weak LEFT command event with power 0.3."""
    return MentalCommandEvent(
        timestamp=sample_timestamp,
        source_id=sample_source_id,
        command=MentalCommand.LEFT,
        power=0.3,
    )


@pytest.fixture
def base_eeg_event(sample_timestamp, sample_source_id) -> EEGEvent:
    """A base EEGEvent (not a MentalCommandEvent)."""
    return EEGEvent(
        timestamp=sample_timestamp,
        source_id=sample_source_id,
    )


@pytest.fixture
def mock_time():
    """Factory fixture for creating mock time sources."""
    class MockTime:
        def __init__(self, initial_time: float = 0.0):
            self.current_time = initial_time

        def __call__(self) -> float:
            return self.current_time

        def advance(self, seconds: float) -> None:
            self.current_time += seconds

    return MockTime


# ===========================================================
# THRESHOLD PROCESSOR TESTS
# ===========================================================


class TestThresholdProcessor:
    """Tests for ThresholdProcessor filtering behavior."""

    def test_filters_events_below_threshold(
        self, weak_left_event, sample_timestamp, sample_source_id
    ):
        """Events with power below threshold should be filtered out."""
        processor = ThresholdProcessor(thresholds={"left": 0.5})

        result = processor.process(weak_left_event)

        assert result is None

    def test_passes_events_at_threshold(self, sample_timestamp, sample_source_id):
        """Events with power exactly at threshold should pass."""
        processor = ThresholdProcessor(thresholds={"left": 0.5})
        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.5,
        )

        result = processor.process(event)

        assert result is event

    def test_passes_events_above_threshold(self, left_command_event):
        """Events with power above threshold should pass."""
        processor = ThresholdProcessor(thresholds={"left": 0.5})

        result = processor.process(left_command_event)

        assert result is left_command_event

    def test_per_command_thresholds(
        self, left_command_event, right_command_event, sample_timestamp, sample_source_id
    ):
        """Different commands can have different thresholds."""
        processor = ThresholdProcessor(
            thresholds={"left": 0.95, "right": 0.5}
        )

        # LEFT at 0.9 should be filtered (threshold 0.95)
        left_result = processor.process(left_command_event)
        assert left_result is None

        # RIGHT at 0.7 should pass (threshold 0.5)
        right_result = processor.process(right_command_event)
        assert right_result is right_command_event

    def test_default_threshold_fallback(self, sample_timestamp, sample_source_id):
        """Commands not in thresholds dict use default_threshold."""
        processor = ThresholdProcessor(
            thresholds={"left": 0.8},
            default_threshold=0.3,
        )

        # LIFT not configured, should use default 0.3
        lift_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LIFT,
            power=0.4,
        )

        result = processor.process(lift_event)

        assert result is lift_event

    def test_default_threshold_filters_when_below(
        self, sample_timestamp, sample_source_id
    ):
        """Default threshold also filters when power is below it."""
        processor = ThresholdProcessor(
            thresholds={},
            default_threshold=0.5,
        )

        low_power_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.PUSH,
            power=0.3,
        )

        result = processor.process(low_power_event)

        assert result is None

    def test_non_mental_command_events_pass_through(self, base_eeg_event):
        """Non-MentalCommandEvent events should pass through unchanged."""
        processor = ThresholdProcessor(thresholds={"left": 0.9})

        result = processor.process(base_eeg_event)

        assert result is base_eeg_event

    def test_config_object_initialization(self, left_command_event):
        """ThresholdProcessor can be initialized with ThresholdConfig."""
        config = ThresholdConfig(
            thresholds={"left": 0.5},
            default_threshold=0.2,
        )
        processor = ThresholdProcessor(config=config)

        result = processor.process(left_command_event)

        assert result is left_command_event

    def test_reset_is_noop(self, left_command_event):
        """Reset should not affect stateless processor behavior."""
        processor = ThresholdProcessor(thresholds={"left": 0.5})

        processor.reset()

        result = processor.process(left_command_event)
        assert result is left_command_event

    def test_threshold_validation_rejects_negative(self):
        """ThresholdConfig should reject negative threshold values."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            ThresholdConfig(thresholds={"left": -0.1})

    def test_threshold_validation_rejects_above_one(self):
        """ThresholdConfig should reject threshold values above 1.0."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            ThresholdConfig(thresholds={"left": 1.5})

    def test_default_threshold_validation(self):
        """ThresholdConfig should reject invalid default_threshold."""
        with pytest.raises(ValueError, match="Default threshold"):
            ThresholdConfig(default_threshold=-0.5)


# ===========================================================
# DEBOUNCE PROCESSOR TESTS
# ===========================================================


class TestDebounceProcessor:
    """Tests for DebounceProcessor cooldown behavior."""

    def test_first_command_passes_through(
        self, left_command_event, mock_time
    ):
        """The first occurrence of a command should always pass."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        result = processor.process(left_command_event)

        assert result is left_command_event

    def test_rapid_repeat_within_cooldown_filtered(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Commands within cooldown period should be filtered."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        event1 = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )
        event2 = MentalCommandEvent(
            timestamp=sample_timestamp + 0.1,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.85,
        )

        # First event passes
        result1 = processor.process(event1)
        assert result1 is event1

        # Advance time by 0.1 seconds (less than 0.3 cooldown)
        time_source.advance(0.1)

        # Second event should be filtered
        result2 = processor.process(event2)
        assert result2 is None

    def test_command_after_cooldown_passes(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Commands after cooldown period should pass through."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        event1 = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )
        event2 = MentalCommandEvent(
            timestamp=sample_timestamp + 0.5,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.85,
        )

        # First event passes
        result1 = processor.process(event1)
        assert result1 is event1

        # Advance time by 0.5 seconds (more than 0.3 cooldown)
        time_source.advance(0.5)

        # Second event should pass (cooldown elapsed)
        result2 = processor.process(event2)
        assert result2 is event2

    def test_different_commands_dont_interfere(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Different commands should have independent cooldowns."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        left_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )
        right_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.RIGHT,
            power=0.8,
        )

        # LEFT passes
        result1 = processor.process(left_event)
        assert result1 is left_event

        # RIGHT should also pass (different command, independent cooldown)
        result2 = processor.process(right_event)
        assert result2 is right_event

    def test_reset_clears_timing_state(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Reset should clear all timing state, allowing immediate commands."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        # Process first event
        result1 = processor.process(event)
        assert result1 is event

        # Without advancing time, next event would be filtered
        time_source.advance(0.1)  # Only 0.1s elapsed

        # Reset clears timing state
        processor.reset()

        # Now the same command should pass immediately
        result2 = processor.process(event)
        assert result2 is event

    def test_per_command_cooldown_overrides(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Per-command cooldowns should override the default."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(
            cooldown=0.3,
            per_command_cooldown={"left": 0.1, "right": 0.5},
            time_source=time_source,
        )

        left_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )
        right_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.RIGHT,
            power=0.8,
        )

        # Process first events
        processor.process(left_event)
        processor.process(right_event)

        # Advance 0.2 seconds
        time_source.advance(0.2)

        # LEFT should pass (0.2 > 0.1 cooldown)
        left_result = processor.process(left_event)
        assert left_result is left_event

        # RIGHT should be filtered (0.2 < 0.5 cooldown)
        right_result = processor.process(right_event)
        assert right_result is None

    def test_non_mental_command_events_pass_through(self, base_eeg_event, mock_time):
        """Non-MentalCommandEvent events should pass through unchanged."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        result = processor.process(base_eeg_event)

        assert result is base_eeg_event

    def test_config_object_initialization(
        self, left_command_event, mock_time
    ):
        """DebounceProcessor can be initialized with DebounceConfig."""
        time_source = mock_time(initial_time=100.0)
        config = DebounceConfig(
            cooldown=0.5,
            per_command_cooldown={"left": 0.2},
        )
        processor = DebounceProcessor(config=config, time_source=time_source)

        result = processor.process(left_command_event)

        assert result is left_command_event

    def test_cooldown_validation_rejects_negative(self):
        """DebounceConfig should reject negative cooldown values."""
        with pytest.raises(ValueError, match="must be non-negative"):
            DebounceConfig(cooldown=-0.1)

    def test_per_command_cooldown_validation(self):
        """DebounceConfig should reject negative per-command cooldowns."""
        with pytest.raises(ValueError, match="must be non-negative"):
            DebounceConfig(per_command_cooldown={"left": -0.5})

    def test_exactly_at_cooldown_boundary_filtered(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Command exactly at cooldown boundary should still be filtered."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        processor.process(event)

        # Advance exactly to cooldown boundary (elapsed == cooldown, not >)
        time_source.advance(0.29999)

        result = processor.process(event)
        assert result is None

    def test_just_past_cooldown_boundary_passes(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Command just past cooldown boundary should pass."""
        time_source = mock_time(initial_time=100.0)
        processor = DebounceProcessor(cooldown=0.3, time_source=time_source)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        processor.process(event)

        # Advance past cooldown boundary (elapsed >= cooldown)
        time_source.advance(0.31)

        result = processor.process(event)
        assert result is event


# ===========================================================
# COMMAND MAPPER TESTS
# ===========================================================


class TestCommandMapper:
    """Tests for CommandMapper action mapping behavior."""

    def test_maps_commands_to_action_strings(
        self, sample_timestamp, sample_source_id
    ):
        """Mapped commands should have their action field set."""
        mapper = CommandMapper(mapping={"left": "A", "right": "D"})

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is not None
        assert result.action == "A"
        assert result.command == MentalCommand.LEFT
        assert result.power == 0.9

    def test_unmapped_commands_filtered_when_configured(
        self, sample_timestamp, sample_source_id
    ):
        """Unmapped commands should be filtered when pass_unmapped=False."""
        mapper = CommandMapper(
            mapping={"left": "A"},
            pass_unmapped=False,
        )

        # LIFT is not in the mapping
        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LIFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is None

    def test_unmapped_commands_pass_through_when_configured(
        self, sample_timestamp, sample_source_id
    ):
        """Unmapped commands should pass through when pass_unmapped=True."""
        mapper = CommandMapper(
            mapping={"left": "A"},
            pass_unmapped=True,  # Default behavior
        )

        # LIFT is not in the mapping
        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LIFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is not None
        assert result.action is None  # No action mapped
        assert result.command == MentalCommand.LIFT

    def test_mapping_updates_action_field(
        self, sample_timestamp, sample_source_id
    ):
        """The mapped action should be set in a new event instance."""
        mapper = CommandMapper(mapping={"right": "D"})

        original_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.RIGHT,
            power=0.8,
        )

        # Original event should have no action
        assert original_event.action is None

        result = mapper.process(original_event)

        # Mapped event should have action set
        assert result is not None
        assert result.action == "D"

        # Original event should be unchanged (immutability)
        assert original_event.action is None

        # Other fields should be preserved
        assert result.timestamp == original_event.timestamp
        assert result.source_id == original_event.source_id
        assert result.command == original_event.command
        assert result.power == original_event.power

    def test_non_mental_command_events_pass_through(self, base_eeg_event):
        """Non-MentalCommandEvent events should pass through unchanged."""
        mapper = CommandMapper(mapping={"left": "A"})

        result = mapper.process(base_eeg_event)

        assert result is base_eeg_event

    def test_config_object_initialization(
        self, sample_timestamp, sample_source_id
    ):
        """CommandMapper can be initialized with MapperConfig."""
        config = MapperConfig(
            mapping={"lift": "SPACE"},
            pass_unmapped=False,
        )
        mapper = CommandMapper(config=config)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LIFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is not None
        assert result.action == "SPACE"

    def test_reset_is_noop(self, left_command_event):
        """Reset should not affect stateless mapper behavior."""
        mapper = CommandMapper(mapping={"left": "A"})

        mapper.reset()

        result = mapper.process(left_command_event)
        assert result is not None
        assert result.action == "A"

    def test_case_insensitive_command_lookup(
        self, sample_timestamp, sample_source_id
    ):
        """Command lookup should work regardless of case in mapping keys."""
        # Mapping keys are lowercase by convention
        mapper = CommandMapper(mapping={"left": "A", "rotate_left": "Q"})

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,  # Enum name is uppercase internally
            power=0.9,
        )

        result = mapper.process(event)

        assert result is not None
        assert result.action == "A"

    def test_multiple_commands_mapped_independently(
        self, sample_timestamp, sample_source_id
    ):
        """Multiple commands can be mapped to different actions."""
        mapper = CommandMapper(
            mapping={
                "left": "A",
                "right": "D",
                "lift": "SPACE",
                "push": "W",
            }
        )

        commands_and_actions = [
            (MentalCommand.LEFT, "A"),
            (MentalCommand.RIGHT, "D"),
            (MentalCommand.LIFT, "SPACE"),
            (MentalCommand.PUSH, "W"),
        ]

        for command, expected_action in commands_and_actions:
            event = MentalCommandEvent(
                timestamp=sample_timestamp,
                source_id=sample_source_id,
                command=command,
                power=0.9,
            )
            result = mapper.process(event)
            assert result is not None
            assert result.action == expected_action

    def test_empty_mapping_with_pass_unmapped_true(
        self, sample_timestamp, sample_source_id
    ):
        """Empty mapping with pass_unmapped=True should pass events with no action."""
        mapper = CommandMapper(mapping={}, pass_unmapped=True)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is not None
        assert result.action is None

    def test_empty_mapping_with_pass_unmapped_false(
        self, sample_timestamp, sample_source_id
    ):
        """Empty mapping with pass_unmapped=False should filter all events."""
        mapper = CommandMapper(mapping={}, pass_unmapped=False)

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        result = mapper.process(event)

        assert result is None


# ===========================================================
# PROCESSOR PIPELINE INTEGRATION TESTS
# ===========================================================


class TestProcessorPipeline:
    """Integration tests for processor pipelines."""

    def test_threshold_then_debounce_pipeline(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Test a pipeline: Threshold -> Debounce."""
        time_source = mock_time(initial_time=100.0)

        threshold = ThresholdProcessor(thresholds={"left": 0.5})
        debounce = DebounceProcessor(cooldown=0.3, time_source=time_source)

        # Strong event passes threshold
        strong_event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        result = threshold.process(strong_event)
        assert result is not None

        result = debounce.process(result)
        assert result is not None

        # Weak event is filtered by threshold
        weak_event = MentalCommandEvent(
            timestamp=sample_timestamp + 0.1,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.3,
        )

        result = threshold.process(weak_event)
        assert result is None

    def test_full_pipeline_threshold_debounce_mapper(
        self, sample_timestamp, sample_source_id, mock_time
    ):
        """Test full pipeline: Threshold -> Debounce -> Mapper."""
        time_source = mock_time(initial_time=100.0)

        threshold = ThresholdProcessor(thresholds={"left": 0.5})
        debounce = DebounceProcessor(cooldown=0.3, time_source=time_source)
        mapper = CommandMapper(mapping={"left": "A"})

        event = MentalCommandEvent(
            timestamp=sample_timestamp,
            source_id=sample_source_id,
            command=MentalCommand.LEFT,
            power=0.9,
        )

        # Process through pipeline
        result = threshold.process(event)
        assert result is not None

        result = debounce.process(result)
        assert result is not None

        result = mapper.process(result)
        assert result is not None
        assert result.action == "A"
