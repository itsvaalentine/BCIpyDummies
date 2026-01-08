"""Comprehensive tests for the BCIpyDummies core module.

This module tests:
- Events (events.py): MentalCommand, EEGEvent, MentalCommandEvent, ConnectionEvent
- Exceptions (exceptions.py): All exception types and inheritance hierarchy
- Config (config.py): ThresholdConfig, KeyboardConfig, EmotivConfig, Config
- Engine (engine.py): BCIPipeline lifecycle and event processing
"""

import os
import tempfile
from dataclasses import FrozenInstanceError
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest

from bcipydummies.core.events import (
    MentalCommand,
    EEGEvent,
    MentalCommandEvent,
    ConnectionEvent,
)
from bcipydummies.core.exceptions import (
    BCIError,
    ConnectionError,
    DeviceNotFoundError,
    AuthenticationError,
    SessionError,
    SubscriptionError,
    ConfigurationError,
    WindowNotFoundError,
)
from bcipydummies.core.config import (
    ThresholdConfig,
    KeyboardConfig,
    EmotivConfig,
    Config,
)
from bcipydummies.core.engine import BCIPipeline
from bcipydummies.processors.base import Processor
from bcipydummies.publishers.base import Publisher
from bcipydummies.sources.base import BaseEEGSource


# ===========================================================================
# TEST FIXTURES AND HELPERS
# ===========================================================================


class MockProcessor(Processor):
    """Mock processor for testing pipeline event flow."""

    def __init__(self, return_event: bool = True, raise_exception: bool = False):
        self.events_received = []
        self.return_event = return_event
        self.raise_exception = raise_exception
        self.reset_called = False

    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        self.events_received.append(event)
        if self.raise_exception:
            raise RuntimeError("Test processor exception")
        return event if self.return_event else None

    def reset(self) -> None:
        self.reset_called = True
        self.events_received = []


class MockPublisher(Publisher):
    """Mock publisher for testing pipeline fan-out."""

    def __init__(self, ready: bool = True):
        self.events_published = []
        self._ready = ready
        self._started = False

    def publish(self, event: EEGEvent) -> None:
        self.events_published.append(event)

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False

    @property
    def is_ready(self) -> bool:
        return self._ready and self._started


class MockSource(BaseEEGSource):
    """Mock EEG source for testing pipeline."""

    def __init__(self, source_id: str = "mock-source"):
        super().__init__(source_id)

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def emit_event(self, event: EEGEvent) -> None:
        """Helper to emit test events."""
        self._emit(event)


# ===========================================================================
# EVENTS TESTS (core/events.py)
# ===========================================================================


class TestMentalCommand:
    """Tests for MentalCommand enum."""

    def test_mental_command_enum_values(self):
        """All expected mental commands should be defined."""
        expected_commands = [
            "NEUTRAL", "PUSH", "PULL", "LIFT", "DROP",
            "LEFT", "RIGHT", "ROTATE_LEFT", "ROTATE_RIGHT", "DISAPPEAR"
        ]
        actual_commands = [cmd.name for cmd in MentalCommand]
        assert actual_commands == expected_commands

    def test_mental_command_from_string_valid(self):
        """from_string should convert valid command names."""
        assert MentalCommand.from_string("left") == MentalCommand.LEFT
        assert MentalCommand.from_string("LEFT") == MentalCommand.LEFT
        assert MentalCommand.from_string("Left") == MentalCommand.LEFT

    def test_mental_command_from_string_with_separators(self):
        """from_string should handle dashes and spaces."""
        assert MentalCommand.from_string("rotate-left") == MentalCommand.ROTATE_LEFT
        assert MentalCommand.from_string("rotate left") == MentalCommand.ROTATE_LEFT
        assert MentalCommand.from_string("ROTATE_RIGHT") == MentalCommand.ROTATE_RIGHT

    def test_mental_command_from_string_invalid(self):
        """from_string should raise ValueError for unknown commands."""
        with pytest.raises(ValueError) as exc_info:
            MentalCommand.from_string("invalid_command")
        assert "Unknown mental command" in str(exc_info.value)
        assert "invalid_command" in str(exc_info.value)


class TestEEGEvent:
    """Tests for EEGEvent dataclass."""

    def test_eeg_event_creation(self):
        """EEGEvent should be created with required fields."""
        event = EEGEvent(timestamp=1234567890.123, source_id="headset-001")
        assert event.timestamp == 1234567890.123
        assert event.source_id == "headset-001"

    def test_eeg_event_immutability(self):
        """EEGEvent should be frozen (immutable)."""
        event = EEGEvent(timestamp=1234567890.0, source_id="test")
        with pytest.raises(FrozenInstanceError):
            event.timestamp = 9999999999.0

    def test_eeg_event_equality(self):
        """EEGEvents with same values should be equal."""
        event1 = EEGEvent(timestamp=100.0, source_id="src")
        event2 = EEGEvent(timestamp=100.0, source_id="src")
        assert event1 == event2

    def test_eeg_event_hashable(self):
        """EEGEvent should be hashable for use in sets/dicts."""
        event = EEGEvent(timestamp=100.0, source_id="src")
        event_set = {event}
        assert event in event_set


class TestMentalCommandEvent:
    """Tests for MentalCommandEvent dataclass."""

    def test_mental_command_event_creation(self):
        """MentalCommandEvent should be created with all fields."""
        event = MentalCommandEvent(
            timestamp=1000.0,
            source_id="headset-001",
            command=MentalCommand.PUSH,
            power=0.85
        )
        assert event.timestamp == 1000.0
        assert event.source_id == "headset-001"
        assert event.command == MentalCommand.PUSH
        assert event.power == 0.85
        assert event.action is None

    def test_mental_command_event_with_action(self):
        """MentalCommandEvent should accept optional action."""
        event = MentalCommandEvent(
            timestamp=1000.0,
            source_id="test",
            command=MentalCommand.LEFT,
            power=0.9,
            action="a"
        )
        assert event.action == "a"

    def test_mental_command_event_power_validation_min(self):
        """Power must be at least 0.0."""
        with pytest.raises(ValueError) as exc_info:
            MentalCommandEvent(
                timestamp=1000.0,
                source_id="test",
                command=MentalCommand.PUSH,
                power=-0.1
            )
        assert "Power must be between 0.0 and 1.0" in str(exc_info.value)

    def test_mental_command_event_power_validation_max(self):
        """Power must be at most 1.0."""
        with pytest.raises(ValueError) as exc_info:
            MentalCommandEvent(
                timestamp=1000.0,
                source_id="test",
                command=MentalCommand.PUSH,
                power=1.5
            )
        assert "Power must be between 0.0 and 1.0" in str(exc_info.value)

    def test_mental_command_event_power_boundary_values(self):
        """Power boundary values (0.0 and 1.0) should be valid."""
        event_min = MentalCommandEvent(
            timestamp=1000.0,
            source_id="test",
            command=MentalCommand.NEUTRAL,
            power=0.0
        )
        event_max = MentalCommandEvent(
            timestamp=1000.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=1.0
        )
        assert event_min.power == 0.0
        assert event_max.power == 1.0

    def test_mental_command_event_immutability(self):
        """MentalCommandEvent should be frozen (immutable)."""
        event = MentalCommandEvent(
            timestamp=1000.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.5
        )
        with pytest.raises(FrozenInstanceError):
            event.power = 0.9


class TestConnectionEvent:
    """Tests for ConnectionEvent dataclass."""

    def test_connection_event_connected(self):
        """ConnectionEvent should indicate connected state."""
        event = ConnectionEvent(connected=True, message="Device connected")
        assert event.connected is True
        assert event.message == "Device connected"

    def test_connection_event_disconnected(self):
        """ConnectionEvent should indicate disconnected state."""
        event = ConnectionEvent(connected=False, message="Device disconnected")
        assert event.connected is False

    def test_connection_event_optional_message(self):
        """ConnectionEvent message should be optional."""
        event = ConnectionEvent(connected=True)
        assert event.connected is True
        assert event.message is None


# ===========================================================================
# EXCEPTIONS TESTS (core/exceptions.py)
# ===========================================================================


class TestBCIError:
    """Tests for base BCIError exception."""

    def test_bci_error_can_be_raised_and_caught(self):
        """BCIError should be raisable and catchable."""
        with pytest.raises(BCIError):
            raise BCIError("Test error")

    def test_bci_error_message_attribute(self):
        """BCIError should store message attribute."""
        error = BCIError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_bci_error_with_source_id(self):
        """BCIError should format message with source_id."""
        error = BCIError("Test error", source_id="device-001")
        assert error.source_id == "device-001"
        assert "[device-001]" in str(error)

    def test_bci_error_inherits_from_exception(self):
        """BCIError should inherit from Exception."""
        error = BCIError("test")
        assert isinstance(error, Exception)


class TestConnectionError:
    """Tests for ConnectionError exception."""

    def test_connection_error_inherits_from_bci_error(self):
        """ConnectionError should inherit from BCIError."""
        error = ConnectionError("Connection failed")
        assert isinstance(error, BCIError)

    def test_connection_error_with_cause(self):
        """ConnectionError should include cause in message."""
        cause = OSError("Network unreachable")
        error = ConnectionError("Failed to connect", cause=cause)
        assert error.cause is cause
        assert "OSError" in str(error)
        assert "Network unreachable" in str(error)

    def test_connection_error_can_be_caught_as_bci_error(self):
        """ConnectionError should be catchable as BCIError."""
        with pytest.raises(BCIError):
            raise ConnectionError("Test connection error")


class TestDeviceNotFoundError:
    """Tests for DeviceNotFoundError exception."""

    def test_device_not_found_inherits_from_connection_error(self):
        """DeviceNotFoundError should inherit from ConnectionError."""
        error = DeviceNotFoundError()
        assert isinstance(error, ConnectionError)
        assert isinstance(error, BCIError)

    def test_device_not_found_default_message(self):
        """DeviceNotFoundError should have default message."""
        error = DeviceNotFoundError()
        assert "No EEG device found" in str(error)

    def test_device_not_found_with_device_type(self):
        """DeviceNotFoundError should include device type in message."""
        error = DeviceNotFoundError(
            message="Unable to locate",
            device_type="Emotiv EPOC"
        )
        assert error.device_type == "Emotiv EPOC"
        assert "Emotiv EPOC" in str(error)


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_authentication_error_inherits_from_bci_error(self):
        """AuthenticationError should inherit from BCIError."""
        error = AuthenticationError("Invalid credentials")
        assert isinstance(error, BCIError)

    def test_authentication_error_attributes(self):
        """AuthenticationError should store message and source_id."""
        error = AuthenticationError("API key invalid", source_id="emotiv")
        assert error.message == "API key invalid"
        assert error.source_id == "emotiv"


class TestSessionError:
    """Tests for SessionError exception."""

    def test_session_error_inherits_from_bci_error(self):
        """SessionError should inherit from BCIError."""
        error = SessionError("Session creation failed")
        assert isinstance(error, BCIError)

    def test_session_error_with_session_id(self):
        """SessionError should include session_id in message."""
        error = SessionError(
            message="Session expired",
            session_id="sess-12345"
        )
        assert error.session_id == "sess-12345"
        assert "sess-12345" in str(error)


class TestSubscriptionError:
    """Tests for SubscriptionError exception."""

    def test_subscription_error_inherits_from_bci_error(self):
        """SubscriptionError should inherit from BCIError."""
        error = SubscriptionError("Failed to subscribe")
        assert isinstance(error, BCIError)

    def test_subscription_error_with_streams(self):
        """SubscriptionError should store stream information."""
        error = SubscriptionError(
            message="Stream unavailable",
            streams=["com", "eeg"]
        )
        assert error.streams == ["com", "eeg"]


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_inherits_from_bci_error(self):
        """ConfigurationError should inherit from BCIError."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, BCIError)

    def test_configuration_error_with_parameter(self):
        """ConfigurationError should include parameter in message."""
        error = ConfigurationError(
            message="Value out of range",
            parameter="threshold"
        )
        assert error.parameter == "threshold"
        assert "threshold" in str(error)


class TestWindowNotFoundError:
    """Tests for WindowNotFoundError exception."""

    def test_window_not_found_inherits_from_bci_error(self):
        """WindowNotFoundError should inherit from BCIError."""
        error = WindowNotFoundError("Window not found")
        assert isinstance(error, BCIError)


class TestExceptionHierarchy:
    """Tests for exception inheritance chain."""

    def test_all_exceptions_caught_by_bci_error(self):
        """All custom exceptions should be catchable as BCIError."""
        exceptions = [
            BCIError("test"),
            ConnectionError("test"),
            DeviceNotFoundError(),
            AuthenticationError("test"),
            SessionError("test"),
            SubscriptionError("test"),
            ConfigurationError("test"),
            WindowNotFoundError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, BCIError), f"{type(exc).__name__} not instance of BCIError"


# ===========================================================================
# CONFIG TESTS (core/config.py)
# ===========================================================================


class TestThresholdConfig:
    """Tests for ThresholdConfig dataclass."""

    def test_threshold_config_default_values(self):
        """ThresholdConfig should have sensible defaults."""
        config = ThresholdConfig()
        assert config.default == 0.5
        assert config.push is None
        assert config.left is None

    def test_threshold_config_custom_values(self):
        """ThresholdConfig should accept custom values."""
        config = ThresholdConfig(default=0.7, left=0.8, right=0.6)
        assert config.default == 0.7
        assert config.left == 0.8
        assert config.right == 0.6

    def test_threshold_config_validation_invalid_default(self):
        """ThresholdConfig should reject invalid default threshold."""
        with pytest.raises(ValueError) as exc_info:
            ThresholdConfig(default=1.5)
        assert "default" in str(exc_info.value)

    def test_threshold_config_validation_invalid_command(self):
        """ThresholdConfig should reject invalid command threshold."""
        with pytest.raises(ValueError) as exc_info:
            ThresholdConfig(left=-0.1)
        assert "left" in str(exc_info.value)

    def test_get_threshold_returns_specific(self):
        """get_threshold should return command-specific value when set."""
        config = ThresholdConfig(default=0.5, left=0.8)
        assert config.get_threshold("left") == 0.8
        assert config.get_threshold("LEFT") == 0.8

    def test_get_threshold_returns_default(self):
        """get_threshold should return default when command not set."""
        config = ThresholdConfig(default=0.6)
        assert config.get_threshold("push") == 0.6
        assert config.get_threshold("unknown") == 0.6

    def test_threshold_config_immutability(self):
        """ThresholdConfig should be frozen."""
        config = ThresholdConfig()
        with pytest.raises(FrozenInstanceError):
            config.default = 0.9


class TestKeyboardConfig:
    """Tests for KeyboardConfig dataclass."""

    def test_keyboard_config_default_values(self):
        """KeyboardConfig should have None defaults."""
        config = KeyboardConfig()
        assert config.push is None
        assert config.left is None

    def test_keyboard_config_custom_mappings(self):
        """KeyboardConfig should accept key mappings."""
        config = KeyboardConfig(left="a", right="d", lift="space")
        assert config.left == "a"
        assert config.right == "d"
        assert config.lift == "space"

    def test_get_key_returns_mapped_key(self):
        """get_key should return mapped key for command."""
        config = KeyboardConfig(left="a", right="d")
        assert config.get_key("left") == "a"
        assert config.get_key("LEFT") == "a"

    def test_get_key_returns_none_when_not_mapped(self):
        """get_key should return None for unmapped commands."""
        config = KeyboardConfig(left="a")
        assert config.get_key("push") is None
        assert config.get_key("unknown") is None

    def test_keyboard_config_immutability(self):
        """KeyboardConfig should be frozen."""
        config = KeyboardConfig()
        with pytest.raises(FrozenInstanceError):
            config.left = "x"


class TestEmotivConfig:
    """Tests for EmotivConfig dataclass."""

    def test_emotiv_config_required_fields(self):
        """EmotivConfig should require client_id and client_secret."""
        config = EmotivConfig(
            client_id="test-client-id",
            client_secret="test-secret"
        )
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-secret"

    def test_emotiv_config_optional_fields(self):
        """EmotivConfig should accept optional headset_id and profile."""
        config = EmotivConfig(
            client_id="id",
            client_secret="secret",
            headset_id="EPOC-12345",
            profile="my_profile"
        )
        assert config.headset_id == "EPOC-12345"
        assert config.profile == "my_profile"

    def test_emotiv_config_validation_missing_client_id(self):
        """EmotivConfig should raise error if client_id is empty."""
        with pytest.raises(ConfigurationError) as exc_info:
            EmotivConfig(client_id="", client_secret="secret")
        assert "client_id" in str(exc_info.value)

    def test_emotiv_config_validation_missing_client_secret(self):
        """EmotivConfig should raise error if client_secret is empty."""
        with pytest.raises(ConfigurationError) as exc_info:
            EmotivConfig(client_id="id", client_secret="")
        assert "client_secret" in str(exc_info.value)

    def test_emotiv_config_from_env_success(self):
        """EmotivConfig.from_env should load from environment variables."""
        with patch.dict(os.environ, {
            "EMOTIV_CLIENT_ID": "env-client-id",
            "EMOTIV_CLIENT_SECRET": "env-secret",
            "EMOTIV_HEADSET_ID": "env-headset",
            "EMOTIV_PROFILE": "env-profile"
        }):
            config = EmotivConfig.from_env()
            assert config.client_id == "env-client-id"
            assert config.client_secret == "env-secret"
            assert config.headset_id == "env-headset"
            assert config.profile == "env-profile"

    def test_emotiv_config_from_env_missing_client_id(self):
        """EmotivConfig.from_env should raise error if client_id missing."""
        with patch.dict(os.environ, {
            "EMOTIV_CLIENT_SECRET": "secret"
        }, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                EmotivConfig.from_env()
            assert "EMOTIV_CLIENT_ID" in str(exc_info.value)

    def test_emotiv_config_from_env_missing_client_secret(self):
        """EmotivConfig.from_env should raise error if client_secret missing."""
        with patch.dict(os.environ, {
            "EMOTIV_CLIENT_ID": "id"
        }, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                EmotivConfig.from_env()
            assert "EMOTIV_CLIENT_SECRET" in str(exc_info.value)


class TestConfig:
    """Tests for main Config dataclass."""

    def test_config_creation_with_emotiv(self):
        """Config should require EmotivConfig."""
        emotiv = EmotivConfig(client_id="id", client_secret="secret")
        config = Config(emotiv=emotiv)
        assert config.emotiv is emotiv
        assert isinstance(config.thresholds, ThresholdConfig)
        assert isinstance(config.keyboard, KeyboardConfig)

    def test_config_with_all_sections(self):
        """Config should accept all configuration sections."""
        emotiv = EmotivConfig(client_id="id", client_secret="secret")
        thresholds = ThresholdConfig(default=0.7)
        keyboard = KeyboardConfig(left="a")
        config = Config(
            emotiv=emotiv,
            thresholds=thresholds,
            keyboard=keyboard,
            target_window="Game Window"
        )
        assert config.thresholds.default == 0.7
        assert config.keyboard.left == "a"
        assert config.target_window == "Game Window"

    def test_config_from_yaml_valid(self):
        """Config.from_yaml should load from YAML file."""
        yaml_content = """
emotiv:
  client_id: yaml-client-id
  client_secret: yaml-secret
  headset_id: yaml-headset
thresholds:
  default: 0.6
  left: 0.8
keyboard:
  left: a
  right: d
target_window: Test Game
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.emotiv.client_id == "yaml-client-id"
            assert config.emotiv.headset_id == "yaml-headset"
            assert config.thresholds.default == 0.6
            assert config.thresholds.left == 0.8
            assert config.keyboard.left == "a"
            assert config.target_window == "Test Game"
        finally:
            os.unlink(temp_path)

    def test_config_from_yaml_file_not_found(self):
        """Config.from_yaml should raise error if file not found."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config.from_yaml("/nonexistent/path/config.yaml")
        assert "not found" in str(exc_info.value)

    def test_config_from_yaml_empty_file(self):
        """Config.from_yaml should raise error for empty file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                Config.from_yaml(temp_path)
            assert "empty" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_config_from_yaml_with_env_fallback(self):
        """Config.from_yaml should fall back to env vars for credentials."""
        yaml_content = """
emotiv:
  headset_id: yaml-headset
thresholds:
  default: 0.7
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {
                "EMOTIV_CLIENT_ID": "env-id",
                "EMOTIV_CLIENT_SECRET": "env-secret"
            }):
                config = Config.from_yaml(temp_path)
                assert config.emotiv.client_id == "env-id"
                assert config.emotiv.client_secret == "env-secret"
                assert config.emotiv.headset_id == "yaml-headset"
        finally:
            os.unlink(temp_path)

    def test_config_from_env(self):
        """Config.from_env should create config from environment."""
        with patch.dict(os.environ, {
            "EMOTIV_CLIENT_ID": "env-id",
            "EMOTIV_CLIENT_SECRET": "env-secret"
        }):
            config = Config.from_env()
            assert config.emotiv.client_id == "env-id"
            assert config.emotiv.client_secret == "env-secret"
            # Should use default thresholds and keyboard
            assert config.thresholds.default == 0.5


# ===========================================================================
# ENGINE TESTS (core/engine.py)
# ===========================================================================


class TestBCIPipelineInitialization:
    """Tests for BCIPipeline initialization."""

    def test_pipeline_initialization_minimal(self):
        """Pipeline should initialize with just a source."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        assert pipeline.source is source
        assert pipeline.processors == []
        assert pipeline.publishers == []
        assert pipeline.is_running is False

    def test_pipeline_initialization_with_processors(self):
        """Pipeline should accept list of processors."""
        source = MockSource()
        processors = [MockProcessor(), MockProcessor()]
        pipeline = BCIPipeline(source=source, processors=processors)
        assert len(pipeline.processors) == 2

    def test_pipeline_initialization_with_publishers(self):
        """Pipeline should accept list of publishers."""
        source = MockSource()
        publishers = [MockPublisher(), MockPublisher()]
        pipeline = BCIPipeline(source=source, publishers=publishers)
        assert len(pipeline.publishers) == 2

    def test_pipeline_processors_property_returns_copy(self):
        """processors property should return a copy."""
        source = MockSource()
        processor = MockProcessor()
        pipeline = BCIPipeline(source=source, processors=[processor])
        processors_copy = pipeline.processors
        processors_copy.append(MockProcessor())
        assert len(pipeline.processors) == 1

    def test_pipeline_statistics_initial(self):
        """Pipeline should have zero statistics initially."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        stats = pipeline.statistics
        assert stats["events_received"] == 0
        assert stats["events_processed"] == 0
        assert stats["events_dropped"] == 0


class TestBCIPipelineLifecycle:
    """Tests for BCIPipeline start/stop lifecycle."""

    def test_pipeline_start_connects_source(self):
        """start() should connect the source."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()
        assert source.is_connected is True
        assert pipeline.is_running is True
        pipeline.stop()

    def test_pipeline_start_starts_publishers(self):
        """start() should start all publishers."""
        source = MockSource()
        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])
        pipeline.start()
        assert publisher._started is True
        pipeline.stop()

    def test_pipeline_start_subscribes_to_source(self):
        """start() should subscribe to source events."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()
        # Source should have at least one subscriber
        assert len(source._subscribers) > 0
        pipeline.stop()

    def test_pipeline_stop_disconnects_source(self):
        """stop() should disconnect the source."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()
        pipeline.stop()
        assert source.is_connected is False
        assert pipeline.is_running is False

    def test_pipeline_stop_stops_publishers(self):
        """stop() should stop all publishers."""
        source = MockSource()
        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])
        pipeline.start()
        pipeline.stop()
        assert publisher._started is False

    def test_pipeline_stop_resets_processors(self):
        """stop() should reset all processors."""
        source = MockSource()
        processor = MockProcessor()
        pipeline = BCIPipeline(source=source, processors=[processor])
        pipeline.start()
        pipeline.stop()
        assert processor.reset_called is True

    def test_pipeline_stop_idempotent(self):
        """stop() should be safe to call multiple times."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()
        pipeline.stop()
        pipeline.stop()  # Should not raise
        assert pipeline.is_running is False

    def test_pipeline_start_already_running(self):
        """start() on running pipeline should be ignored."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()
        pipeline.start()  # Should not raise, just log warning
        assert pipeline.is_running is True
        pipeline.stop()

    def test_pipeline_context_manager(self):
        """Pipeline should work as context manager."""
        source = MockSource()
        with BCIPipeline(source=source) as pipeline:
            assert pipeline.is_running is True
            assert source.is_connected is True
        assert pipeline.is_running is False
        assert source.is_connected is False


class TestBCIPipelineEventFlow:
    """Tests for event flow through the pipeline."""

    def test_event_passes_through_processors(self):
        """Events should pass through all processors in order."""
        source = MockSource()
        processor1 = MockProcessor()
        processor2 = MockProcessor()
        pipeline = BCIPipeline(
            source=source,
            processors=[processor1, processor2]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.LEFT,
            power=0.8
        )
        source.emit_event(event)

        assert len(processor1.events_received) == 1
        assert len(processor2.events_received) == 1
        assert processor1.events_received[0] is event
        pipeline.stop()

    def test_event_reaches_publishers(self):
        """Processed events should reach all publishers."""
        source = MockSource()
        publisher1 = MockPublisher()
        publisher2 = MockPublisher()
        pipeline = BCIPipeline(
            source=source,
            publishers=[publisher1, publisher2]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.9
        )
        source.emit_event(event)

        assert len(publisher1.events_published) == 1
        assert len(publisher2.events_published) == 1
        pipeline.stop()

    def test_event_filtering_by_processor(self):
        """Events filtered (None) by processor should be dropped."""
        source = MockSource()
        filtering_processor = MockProcessor(return_event=False)
        publisher = MockPublisher()
        pipeline = BCIPipeline(
            source=source,
            processors=[filtering_processor],
            publishers=[publisher]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.NEUTRAL,
            power=0.1
        )
        source.emit_event(event)

        # Processor received it, but publisher should not
        assert len(filtering_processor.events_received) == 1
        assert len(publisher.events_published) == 0
        pipeline.stop()

    def test_chain_stops_on_filter(self):
        """Processor chain should stop when event is filtered."""
        source = MockSource()
        processor1 = MockProcessor(return_event=False)
        processor2 = MockProcessor()
        pipeline = BCIPipeline(
            source=source,
            processors=[processor1, processor2]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.LEFT,
            power=0.5
        )
        source.emit_event(event)

        # First processor saw it, second should not
        assert len(processor1.events_received) == 1
        assert len(processor2.events_received) == 0
        pipeline.stop()

    def test_publisher_not_ready_skipped(self):
        """Publishers not ready should be skipped."""
        source = MockSource()
        ready_publisher = MockPublisher(ready=True)
        not_ready_publisher = MockPublisher(ready=False)
        pipeline = BCIPipeline(
            source=source,
            publishers=[ready_publisher, not_ready_publisher]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.8
        )
        source.emit_event(event)

        assert len(ready_publisher.events_published) == 1
        assert len(not_ready_publisher.events_published) == 0
        pipeline.stop()


class TestBCIPipelineStatistics:
    """Tests for pipeline statistics tracking."""

    def test_statistics_events_received(self):
        """events_received should count all incoming events."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()

        for i in range(5):
            event = MentalCommandEvent(
                timestamp=100.0 + i,
                source_id="test",
                command=MentalCommand.NEUTRAL,
                power=0.5
            )
            source.emit_event(event)

        stats = pipeline.statistics
        assert stats["events_received"] == 5
        pipeline.stop()

    def test_statistics_events_processed(self):
        """events_processed should count events that pass through."""
        source = MockSource()
        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])
        pipeline.start()

        for i in range(3):
            event = MentalCommandEvent(
                timestamp=100.0 + i,
                source_id="test",
                command=MentalCommand.PUSH,
                power=0.9
            )
            source.emit_event(event)

        stats = pipeline.statistics
        assert stats["events_processed"] == 3
        pipeline.stop()

    def test_statistics_events_dropped(self):
        """events_dropped should count filtered events."""
        source = MockSource()
        filtering_processor = MockProcessor(return_event=False)
        pipeline = BCIPipeline(
            source=source,
            processors=[filtering_processor]
        )
        pipeline.start()

        for i in range(4):
            event = MentalCommandEvent(
                timestamp=100.0 + i,
                source_id="test",
                command=MentalCommand.NEUTRAL,
                power=0.1
            )
            source.emit_event(event)

        stats = pipeline.statistics
        assert stats["events_received"] == 4
        assert stats["events_dropped"] == 4
        assert stats["events_processed"] == 0
        pipeline.stop()

    def test_statistics_reset_on_start(self):
        """Statistics should reset when pipeline starts."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.8
        )
        source.emit_event(event)
        pipeline.stop()

        # Restart and verify stats reset
        pipeline.start()
        stats = pipeline.statistics
        assert stats["events_received"] == 0
        pipeline.stop()


class TestBCIPipelineDynamicModification:
    """Tests for adding/removing processors and publishers at runtime."""

    def test_add_processor(self):
        """add_processor should add to the chain."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        processor = MockProcessor()
        pipeline.add_processor(processor)
        assert processor in pipeline.processors

    def test_add_publisher(self):
        """add_publisher should add to publishers."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        publisher = MockPublisher()
        pipeline.add_publisher(publisher)
        assert publisher in pipeline.publishers

    def test_add_publisher_while_running(self):
        """add_publisher while running should start the publisher."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        pipeline.start()

        publisher = MockPublisher()
        pipeline.add_publisher(publisher)
        assert publisher._started is True
        pipeline.stop()

    def test_remove_processor(self):
        """remove_processor should remove from the chain."""
        source = MockSource()
        processor = MockProcessor()
        pipeline = BCIPipeline(source=source, processors=[processor])
        result = pipeline.remove_processor(processor)
        assert result is True
        assert processor not in pipeline.processors

    def test_remove_processor_not_found(self):
        """remove_processor returns False if not found."""
        source = MockSource()
        pipeline = BCIPipeline(source=source)
        processor = MockProcessor()
        result = pipeline.remove_processor(processor)
        assert result is False

    def test_remove_publisher(self):
        """remove_publisher should remove from publishers."""
        source = MockSource()
        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])
        result = pipeline.remove_publisher(publisher)
        assert result is True
        assert publisher not in pipeline.publishers

    def test_remove_publisher_while_running(self):
        """remove_publisher while running should stop the publisher."""
        source = MockSource()
        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])
        pipeline.start()

        pipeline.remove_publisher(publisher)
        assert publisher._started is False
        pipeline.stop()


class TestBCIPipelineErrorHandling:
    """Tests for error handling in the pipeline."""

    def test_processor_exception_drops_event(self):
        """Processor exception should drop the event."""
        source = MockSource()
        error_processor = MockProcessor(raise_exception=True)
        publisher = MockPublisher()
        pipeline = BCIPipeline(
            source=source,
            processors=[error_processor],
            publishers=[publisher]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.8
        )
        source.emit_event(event)

        # Event should be dropped, publisher should not receive it
        assert len(publisher.events_published) == 0
        stats = pipeline.statistics
        assert stats["events_dropped"] == 1
        pipeline.stop()

    def test_publisher_exception_does_not_affect_others(self):
        """Publisher exception should not affect other publishers."""
        source = MockSource()
        failing_publisher = MockPublisher()
        working_publisher = MockPublisher()

        # Make publish raise an exception
        failing_publisher.publish = MagicMock(side_effect=RuntimeError("Test error"))

        pipeline = BCIPipeline(
            source=source,
            publishers=[failing_publisher, working_publisher]
        )
        pipeline.start()

        event = MentalCommandEvent(
            timestamp=100.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.8
        )
        source.emit_event(event)

        # Working publisher should still receive the event
        assert len(working_publisher.events_published) == 1
        pipeline.stop()

    def test_source_connect_failure_rolls_back(self):
        """Source connect failure should stop already-started publishers."""
        source = MockSource()
        source.connect = MagicMock(side_effect=RuntimeError("Connection failed"))

        publisher = MockPublisher()
        pipeline = BCIPipeline(source=source, publishers=[publisher])

        with pytest.raises(RuntimeError):
            pipeline.start()

        # Publisher should be stopped after rollback
        assert publisher._started is False


class TestBCIPipelineRepr:
    """Tests for pipeline string representation."""

    def test_repr_format(self):
        """__repr__ should show source, counts, and running state."""
        source = MockSource(source_id="my-source")
        processor = MockProcessor()
        publisher = MockPublisher()
        pipeline = BCIPipeline(
            source=source,
            processors=[processor],
            publishers=[publisher]
        )

        repr_str = repr(pipeline)
        assert "BCIPipeline" in repr_str
        assert "my-source" in repr_str
        assert "processors=1" in repr_str
        assert "publishers=1" in repr_str
        assert "running=False" in repr_str
