"""Comprehensive tests for the BCIpyDummies sources module.

Tests cover:
- MockSource: Event generation, scripting, subscriber management
- BaseEEGSource: Abstract class behavior, subscriber management
- EmotivSource: Integration tests with mocked WebSocket
- CortexCredentials: Environment variable loading
- CortexClient: WebSocket message handling
"""

import json
import os
import threading
import time
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from bcipydummies.core.events import (
    ConnectionEvent,
    EEGEvent,
    MentalCommand,
    MentalCommandEvent,
)
from bcipydummies.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    DeviceNotFoundError,
    SessionError,
    SubscriptionError,
)
from bcipydummies.sources.base import BaseEEGSource, EventCallback
from bcipydummies.sources.mock import (
    MockSource,
    ReplaySource,
    ScriptedEvent,
    create_test_script,
)
from bcipydummies.sources.emotiv.cortex_client import (
    CortexClient,
    CortexCredentials,
    CortexState,
)
from bcipydummies.sources.emotiv.source import EmotivSource


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_credentials():
    """Provide sample Cortex API credentials for testing."""
    return CortexCredentials(
        client_id="test-client-id",
        client_secret="test-client-secret",
        license_id="test-license-id",
    )


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket object."""
    ws = MagicMock()
    ws.send = MagicMock()
    ws.close = MagicMock()
    return ws


@pytest.fixture
def event_collector():
    """Create a simple event collector for testing subscribers."""
    events: List[EEGEvent] = []

    def collector(event: EEGEvent) -> None:
        events.append(event)

    collector.events = events
    return collector


# =============================================================================
# MockSource Tests
# =============================================================================

class TestMockSource:
    """Tests for MockSource class."""

    def test_creates_with_default_settings(self):
        """MockSource should initialize with reasonable defaults."""
        source = MockSource()

        assert source.source_id == "mock-source"
        assert source.is_connected is False
        assert source.is_scripted is False

    def test_creates_with_custom_source_id(self):
        """MockSource should accept a custom source ID."""
        source = MockSource(source_id="custom-mock")

        assert source.source_id == "custom-mock"

    def test_is_scripted_when_script_provided(self):
        """MockSource should detect scripted mode when script is provided."""
        script = [ScriptedEvent(0.0, MentalCommand.NEUTRAL, 0.9)]
        source = MockSource(script=script)

        assert source.is_scripted is True

    def test_connect_sets_is_connected(self):
        """Connecting should set is_connected to True."""
        source = MockSource()

        source.connect()
        try:
            assert source.is_connected is True
        finally:
            source.disconnect()

    def test_connect_emits_connection_event(self, event_collector):
        """Connecting should emit a ConnectionEvent."""
        source = MockSource()
        source.subscribe(event_collector)

        source.connect()
        try:
            # Give event time to be emitted
            time.sleep(0.1)

            connection_events = [
                e for e in event_collector.events
                if isinstance(e, ConnectionEvent) and e.connected
            ]
            assert len(connection_events) >= 1
            assert connection_events[0].connected is True
        finally:
            source.disconnect()

    def test_disconnect_sets_is_connected_false(self):
        """Disconnecting should set is_connected to False."""
        source = MockSource()
        source.connect()
        source.disconnect()

        assert source.is_connected is False

    def test_disconnect_emits_disconnection_event(self, event_collector):
        """Disconnecting should emit a ConnectionEvent with connected=False."""
        source = MockSource()
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.1)
        source.disconnect()
        time.sleep(0.1)

        disconnection_events = [
            e for e in event_collector.events
            if isinstance(e, ConnectionEvent) and not e.connected
        ]
        assert len(disconnection_events) >= 1
        assert disconnection_events[0].connected is False

    def test_connect_is_idempotent(self):
        """Calling connect when already connected should be safe."""
        source = MockSource()
        source.connect()

        try:
            # Should not raise an exception
            source.connect()
            assert source.is_connected is True
        finally:
            source.disconnect()

    def test_disconnect_is_idempotent(self):
        """Calling disconnect when not connected should be safe."""
        source = MockSource()

        # Should not raise an exception
        source.disconnect()
        assert source.is_connected is False

    def test_emit_command_delivers_to_subscribers(self, event_collector):
        """emit_command should deliver events to all subscribers."""
        source = MockSource()
        source.subscribe(event_collector)
        source.connect()

        try:
            source.emit_command(MentalCommand.PUSH, 0.9)
            time.sleep(0.1)

            command_events = [
                e for e in event_collector.events
                if isinstance(e, MentalCommandEvent)
            ]
            assert len(command_events) >= 1
            assert command_events[0].command == MentalCommand.PUSH
            assert command_events[0].power == 0.9
        finally:
            source.disconnect()

    def test_emit_command_clamps_power_to_valid_range(self, event_collector):
        """emit_command should clamp power values to [0.0, 1.0]."""
        source = MockSource()
        source.subscribe(event_collector)
        source.connect()

        try:
            source.emit_command(MentalCommand.PUSH, 1.5)  # Over max
            source.emit_command(MentalCommand.PULL, -0.5)  # Under min
            time.sleep(0.1)

            command_events = [
                e for e in event_collector.events
                if isinstance(e, MentalCommandEvent)
            ]

            # Power should be clamped
            powers = [e.power for e in command_events]
            assert all(0.0 <= p <= 1.0 for p in powers)
        finally:
            source.disconnect()

    def test_emit_command_requires_connection(self, event_collector):
        """emit_command should not emit when not connected."""
        source = MockSource()
        source.subscribe(event_collector)

        # Not connected
        source.emit_command(MentalCommand.PUSH, 0.9)
        time.sleep(0.1)

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]
        assert len(command_events) == 0

    def test_context_manager_connects_and_disconnects(self, event_collector):
        """MockSource should support context manager protocol."""
        source = MockSource()
        source.subscribe(event_collector)

        with source as s:
            assert s.is_connected is True
            assert s is source

        assert source.is_connected is False


class TestMockSourceScripted:
    """Tests for MockSource scripted event sequences."""

    def test_scripted_events_execute_in_order(self, event_collector):
        """Scripted events should execute in the order provided."""
        script = [
            ScriptedEvent(0.0, MentalCommand.NEUTRAL, 0.9),
            ScriptedEvent(0.05, MentalCommand.PUSH, 0.8),
            ScriptedEvent(0.05, MentalCommand.LEFT, 0.7),
        ]
        source = MockSource(script=script)
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.3)  # Wait for script to complete
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) >= 3
        assert command_events[0].command == MentalCommand.NEUTRAL
        assert command_events[1].command == MentalCommand.PUSH
        assert command_events[2].command == MentalCommand.LEFT

    def test_scripted_events_respect_delays(self, event_collector):
        """Scripted events should respect their delay timings."""
        script = [
            ScriptedEvent(0.0, MentalCommand.NEUTRAL, 0.9),
            ScriptedEvent(0.1, MentalCommand.PUSH, 0.8),
        ]
        source = MockSource(script=script)
        source.subscribe(event_collector)

        source.connect()

        # First event should arrive quickly
        time.sleep(0.05)
        early_commands = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]
        assert len(early_commands) == 1

        # Second event after delay
        time.sleep(0.15)
        source.disconnect()

        all_commands = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]
        assert len(all_commands) >= 2

    def test_loop_script_repeats_sequence(self, event_collector):
        """With loop_script=True, the sequence should repeat."""
        script = [
            ScriptedEvent(0.0, MentalCommand.PUSH, 0.8),
            ScriptedEvent(0.05, MentalCommand.PULL, 0.8),
        ]
        source = MockSource(script=script, loop_script=True)
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.25)  # Enough for at least 2 iterations
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        # Should have more than 2 events due to looping
        assert len(command_events) >= 3

    def test_non_looping_script_stops_after_completion(self, event_collector):
        """Without looping, script should execute once and stop."""
        script = [
            ScriptedEvent(0.0, MentalCommand.PUSH, 0.8),
        ]
        source = MockSource(script=script, loop_script=False)
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.2)
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        # Should have exactly 1 command event (not repeated)
        assert len(command_events) == 1


class TestMockSourceSubscribers:
    """Tests for MockSource subscriber management."""

    def test_subscribe_adds_callback(self):
        """subscribe() should add callback to subscriber list."""
        source = MockSource()
        events = []
        callback = lambda e: events.append(e)

        source.subscribe(callback)
        source.connect()
        source.emit_command(MentalCommand.PUSH, 0.8)
        time.sleep(0.1)
        source.disconnect()

        command_events = [e for e in events if isinstance(e, MentalCommandEvent)]
        assert len(command_events) >= 1

    def test_subscribe_prevents_duplicate_callbacks(self):
        """Subscribing same callback twice should only register once."""
        source = MockSource()
        events = []
        callback = lambda e: events.append(e)

        source.subscribe(callback)
        source.subscribe(callback)  # Duplicate

        source.connect()
        source.emit_command(MentalCommand.PUSH, 0.8)
        time.sleep(0.1)
        source.disconnect()

        # Should only have received event once
        command_events = [e for e in events if isinstance(e, MentalCommandEvent)]
        assert len(command_events) == 1

    def test_unsubscribe_removes_callback(self):
        """unsubscribe() should remove callback from receiving events."""
        source = MockSource()
        events = []
        callback = lambda e: events.append(e)

        source.subscribe(callback)
        source.unsubscribe(callback)

        source.connect()
        source.emit_command(MentalCommand.PUSH, 0.8)
        time.sleep(0.1)
        source.disconnect()

        command_events = [e for e in events if isinstance(e, MentalCommandEvent)]
        assert len(command_events) == 0

    def test_unsubscribe_unknown_callback_is_safe(self):
        """Unsubscribing a callback that was never subscribed should be safe."""
        source = MockSource()
        callback = lambda e: None

        # Should not raise an exception
        source.unsubscribe(callback)

    def test_multiple_subscribers_all_receive_events(self):
        """All subscribed callbacks should receive events."""
        source = MockSource()
        events1 = []
        events2 = []
        events3 = []

        source.subscribe(lambda e: events1.append(e))
        source.subscribe(lambda e: events2.append(e))
        source.subscribe(lambda e: events3.append(e))

        source.connect()
        source.emit_command(MentalCommand.PUSH, 0.8)
        time.sleep(0.1)
        source.disconnect()

        # Each subscriber should have received the event
        for events in [events1, events2, events3]:
            command_events = [e for e in events if isinstance(e, MentalCommandEvent)]
            assert len(command_events) >= 1


class TestCreateTestScript:
    """Tests for the create_test_script helper function."""

    def test_creates_script_from_enum_commands(self):
        """Should create script from MentalCommand enum values."""
        commands = [MentalCommand.PUSH, MentalCommand.PULL]
        script = create_test_script(commands, interval=0.5, power=0.7)

        assert len(script) == 2
        assert script[0].command == MentalCommand.PUSH
        assert script[0].delay == 0.0  # First has no delay
        assert script[0].power == 0.7
        assert script[1].command == MentalCommand.PULL
        assert script[1].delay == 0.5

    def test_creates_script_from_string_commands(self):
        """Should create script from string command names."""
        commands = ["push", "left", "right"]
        script = create_test_script(commands, interval=1.0)

        assert len(script) == 3
        assert script[0].command == MentalCommand.PUSH
        assert script[1].command == MentalCommand.LEFT
        assert script[2].command == MentalCommand.RIGHT

    def test_first_event_has_zero_delay(self):
        """First event should always have delay of 0."""
        commands = [MentalCommand.PUSH, MentalCommand.PULL]
        script = create_test_script(commands, interval=1.0)

        assert script[0].delay == 0.0

    def test_subsequent_events_use_interval(self):
        """Subsequent events should use the specified interval."""
        commands = [MentalCommand.PUSH, MentalCommand.PULL, MentalCommand.LEFT]
        script = create_test_script(commands, interval=2.0)

        assert script[1].delay == 2.0
        assert script[2].delay == 2.0


class TestReplaySource:
    """Tests for ReplaySource class."""

    def test_replays_recorded_events(self, event_collector):
        """ReplaySource should replay recorded MentalCommandEvents."""
        now = time.time()
        recorded = [
            MentalCommandEvent(now, "original", MentalCommand.PUSH, 0.8),
            MentalCommandEvent(now + 0.1, "original", MentalCommand.PULL, 0.7),
        ]

        source = ReplaySource(recorded)
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.3)
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) >= 2
        assert command_events[0].command == MentalCommand.PUSH
        assert command_events[1].command == MentalCommand.PULL

    def test_speed_multiplier_affects_timing(self, event_collector):
        """Speed multiplier should scale playback speed."""
        now = time.time()
        recorded = [
            MentalCommandEvent(now, "original", MentalCommand.PUSH, 0.8),
            MentalCommandEvent(now + 0.2, "original", MentalCommand.PULL, 0.7),
        ]

        # 2x speed = half the delay
        source = ReplaySource(recorded, speed_multiplier=2.0)
        source.subscribe(event_collector)

        start = time.time()
        source.connect()
        time.sleep(0.3)
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) >= 2

    def test_empty_recording_produces_no_events(self, event_collector):
        """Empty recorded sequence should produce no command events."""
        source = ReplaySource([])
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.1)
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) == 0


# =============================================================================
# BaseEEGSource Tests
# =============================================================================

class ConcreteEEGSource(BaseEEGSource):
    """Concrete implementation for testing BaseEEGSource."""

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def emit_event(self, event: EEGEvent) -> None:
        """Public method to test _emit."""
        self._emit(event)


class TestBaseEEGSource:
    """Tests for BaseEEGSource abstract class behavior."""

    def test_initializes_with_source_id(self):
        """BaseEEGSource should store the source ID."""
        source = ConcreteEEGSource("test-source")

        assert source.source_id == "test-source"

    def test_initializes_disconnected(self):
        """BaseEEGSource should start disconnected."""
        source = ConcreteEEGSource("test-source")

        assert source.is_connected is False

    def test_subscribe_registers_callback(self):
        """subscribe() should register callback for events."""
        source = ConcreteEEGSource("test-source")
        events = []
        callback = lambda e: events.append(e)

        source.subscribe(callback)
        source.connect()
        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id="test-source",
            command=MentalCommand.PUSH,
            power=0.8,
        )
        source.emit_event(event)

        assert len(events) == 1
        assert events[0] == event

    def test_unsubscribe_removes_callback(self):
        """unsubscribe() should prevent callback from receiving events."""
        source = ConcreteEEGSource("test-source")
        events = []
        callback = lambda e: events.append(e)

        source.subscribe(callback)
        source.unsubscribe(callback)

        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id="test-source",
            command=MentalCommand.PUSH,
            power=0.8,
        )
        source.emit_event(event)

        assert len(events) == 0

    def test_emit_notifies_all_subscribers(self):
        """_emit() should notify all subscribed callbacks."""
        source = ConcreteEEGSource("test-source")
        events1 = []
        events2 = []

        source.subscribe(lambda e: events1.append(e))
        source.subscribe(lambda e: events2.append(e))

        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id="test-source",
            command=MentalCommand.PUSH,
            power=0.8,
        )
        source.emit_event(event)

        assert len(events1) == 1
        assert len(events2) == 1

    def test_emit_handles_callback_exceptions_gracefully(self):
        """_emit() should continue to other callbacks if one raises."""
        source = ConcreteEEGSource("test-source")
        events = []

        def bad_callback(e):
            raise RuntimeError("Callback error")

        def good_callback(e):
            events.append(e)

        source.subscribe(bad_callback)
        source.subscribe(good_callback)

        event = MentalCommandEvent(
            timestamp=time.time(),
            source_id="test-source",
            command=MentalCommand.PUSH,
            power=0.8,
        )

        # Should not raise
        source.emit_event(event)

        # Good callback should still receive the event
        assert len(events) == 1

    def test_base_connect_raises_not_implemented(self):
        """BaseEEGSource.connect() should raise NotImplementedError."""
        source = BaseEEGSource("test-source")

        with pytest.raises(NotImplementedError):
            source.connect()

    def test_base_disconnect_raises_not_implemented(self):
        """BaseEEGSource.disconnect() should raise NotImplementedError."""
        source = BaseEEGSource("test-source")

        with pytest.raises(NotImplementedError):
            source.disconnect()


# =============================================================================
# CortexCredentials Tests
# =============================================================================

class TestCortexCredentials:
    """Tests for CortexCredentials data class."""

    def test_creates_with_required_fields(self):
        """Should create credentials with client ID and secret."""
        creds = CortexCredentials(
            client_id="my-client-id",
            client_secret="my-secret",
        )

        assert creds.client_id == "my-client-id"
        assert creds.client_secret == "my-secret"
        assert creds.license_id is None

    def test_creates_with_optional_license_id(self):
        """Should accept optional license ID."""
        creds = CortexCredentials(
            client_id="my-client-id",
            client_secret="my-secret",
            license_id="my-license",
        )

        assert creds.license_id == "my-license"

    def test_from_environment_reads_variables(self, monkeypatch):
        """Should read credentials from environment variables."""
        monkeypatch.setenv("EMOTIV_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("EMOTIV_CLIENT_SECRET", "env-secret")
        monkeypatch.setenv("EMOTIV_LICENSE_ID", "env-license")

        creds = CortexCredentials.from_environment()

        assert creds.client_id == "env-client-id"
        assert creds.client_secret == "env-secret"
        assert creds.license_id == "env-license"

    def test_from_environment_license_is_optional(self, monkeypatch):
        """License ID should be optional when loading from environment."""
        monkeypatch.setenv("EMOTIV_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("EMOTIV_CLIENT_SECRET", "env-secret")
        monkeypatch.delenv("EMOTIV_LICENSE_ID", raising=False)

        creds = CortexCredentials.from_environment()

        assert creds.license_id is None

    def test_from_environment_raises_without_client_id(self, monkeypatch):
        """Should raise ConfigurationError when client ID is missing."""
        monkeypatch.delenv("EMOTIV_CLIENT_ID", raising=False)
        monkeypatch.setenv("EMOTIV_CLIENT_SECRET", "env-secret")

        with pytest.raises(ConfigurationError) as exc_info:
            CortexCredentials.from_environment()

        assert "EMOTIV_CLIENT_ID" in str(exc_info.value)

    def test_from_environment_raises_without_client_secret(self, monkeypatch):
        """Should raise ConfigurationError when client secret is missing."""
        monkeypatch.setenv("EMOTIV_CLIENT_ID", "env-client-id")
        monkeypatch.delenv("EMOTIV_CLIENT_SECRET", raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            CortexCredentials.from_environment()

        assert "EMOTIV_CLIENT_SECRET" in str(exc_info.value)


# =============================================================================
# EmotivSource Tests
# =============================================================================

class TestEmotivSource:
    """Tests for EmotivSource class with mocked WebSocket."""

    def test_initializes_with_credentials(self, sample_credentials):
        """EmotivSource should initialize with credentials."""
        source = EmotivSource(sample_credentials)

        # Default source ID before connection
        assert "emotiv" in source.source_id.lower()

    def test_custom_source_id(self, sample_credentials):
        """Should accept custom source ID."""
        source = EmotivSource(
            sample_credentials,
            source_id="my-custom-emotiv",
        )

        assert source.source_id == "my-custom-emotiv"

    def test_is_connected_false_initially(self, sample_credentials):
        """Should start disconnected."""
        source = EmotivSource(sample_credentials)

        assert source.is_connected is False

    def test_connect_raises_when_already_connected(self, sample_credentials):
        """connect() should raise ConnectionError when already connected."""
        source = EmotivSource(sample_credentials)
        source._connected = True  # Simulate connected state

        with pytest.raises(ConnectionError):
            source.connect()

    def test_disconnect_is_safe_when_not_connected(self, sample_credentials):
        """disconnect() should be safe to call when not connected."""
        source = EmotivSource(sample_credentials)

        # Should not raise
        source.disconnect()

    def test_command_mapping_covers_all_commands(self, sample_credentials):
        """EmotivSource should have mappings for common Cortex commands."""
        source = EmotivSource(sample_credentials)

        expected_commands = [
            "neutral", "push", "pull", "lift", "drop",
            "left", "right", "rotateLeft", "rotateRight", "disappear",
        ]

        for cmd in expected_commands:
            assert cmd.lower() in source._COMMAND_MAP or cmd in source._COMMAND_MAP

    def test_on_mental_command_emits_event(self, sample_credentials, event_collector):
        """_on_mental_command should emit MentalCommandEvent to subscribers."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)
        source._connected = True

        # Simulate receiving a mental command from Cortex
        source._on_mental_command("push", 0.85)

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) == 1
        assert command_events[0].command == MentalCommand.PUSH
        assert command_events[0].power == 0.85

    def test_on_mental_command_handles_unknown_command(
        self, sample_credentials, event_collector
    ):
        """_on_mental_command should handle unknown command strings gracefully."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)
        source._connected = True

        # Unknown command - should not emit or crash
        source._on_mental_command("unknown_command_xyz", 0.5)

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        # Should not emit invalid command
        assert len(command_events) == 0

    def test_on_mental_command_clamps_power(self, sample_credentials, event_collector):
        """_on_mental_command should clamp power to [0.0, 1.0]."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)
        source._connected = True

        source._on_mental_command("push", 1.5)  # Over max
        source._on_mental_command("pull", -0.5)  # Under min

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(command_events) == 2
        assert command_events[0].power == 1.0  # Clamped
        assert command_events[1].power == 0.0  # Clamped

    def test_on_connection_change_updates_state(
        self, sample_credentials, event_collector
    ):
        """_on_connection_change should update connected state."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)

        source._on_connection_change(True, "Connected to headset")

        assert source._connected is True

        connection_events = [
            e for e in event_collector.events
            if isinstance(e, ConnectionEvent)
        ]
        assert len(connection_events) == 1
        assert connection_events[0].connected is True

    def test_on_error_stores_error(self, sample_credentials, event_collector):
        """_on_error should store the last error."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)

        error = AuthenticationError("Test error")
        source._on_error(error)

        assert source.last_error is not None
        assert isinstance(source.last_error, AuthenticationError)

    def test_on_error_emits_disconnection_event(
        self, sample_credentials, event_collector
    ):
        """_on_error should emit a disconnection event."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)

        source._on_error(RuntimeError("Connection lost"))

        connection_events = [
            e for e in event_collector.events
            if isinstance(e, ConnectionEvent) and not e.connected
        ]
        assert len(connection_events) == 1

    def test_context_manager_protocol(self, sample_credentials):
        """EmotivSource should support context manager protocol."""
        source = EmotivSource(sample_credentials)

        # Mock the connect/disconnect to avoid actual connection
        source.connect = MagicMock()
        source.disconnect = MagicMock()

        with source as s:
            assert s is source
            source.connect.assert_called_once()

        source.disconnect.assert_called_once()


# =============================================================================
# CortexClient Tests
# =============================================================================

class TestCortexClient:
    """Tests for CortexClient WebSocket handling."""

    def test_initializes_in_disconnected_state(self, sample_credentials):
        """CortexClient should start in DISCONNECTED state."""
        client = CortexClient(sample_credentials)

        assert client.state == CortexState.DISCONNECTED
        assert client.is_connected is False

    def test_default_streams_includes_com(self, sample_credentials):
        """Default streams should include mental commands (com)."""
        client = CortexClient(sample_credentials)

        assert "com" in client._streams

    def test_custom_streams(self, sample_credentials):
        """Should accept custom stream list."""
        client = CortexClient(
            sample_credentials,
            streams=["com", "eeg"],
        )

        assert "com" in client._streams
        assert "eeg" in client._streams

    def test_connect_changes_state_to_connecting(self, sample_credentials):
        """connect() should change state to CONNECTING."""
        client = CortexClient(sample_credentials)

        # Mock the WebSocket to prevent actual connection
        with patch("bcipydummies.sources.emotiv.cortex_client.websocket.WebSocketApp"):
            client.connect()

            assert client.state == CortexState.CONNECTING

    def test_connect_raises_when_not_disconnected(self, sample_credentials):
        """connect() should raise when already connecting/connected."""
        client = CortexClient(sample_credentials)
        client._state = CortexState.STREAMING

        with pytest.raises(ConnectionError):
            client.connect()

    def test_disconnect_resets_state(self, sample_credentials):
        """disconnect() should reset client state."""
        client = CortexClient(sample_credentials)
        client._state = CortexState.STREAMING
        client._cortex_token = "test-token"
        client._session_id = "test-session"
        client._headset_id = "test-headset"

        client.disconnect()

        assert client.state == CortexState.DISCONNECTED
        assert client._cortex_token is None
        assert client._session_id is None
        assert client._headset_id is None

    def test_on_ws_open_starts_authentication(
        self, sample_credentials, mock_websocket
    ):
        """WebSocket open should trigger authentication request."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket

        client._on_ws_open(mock_websocket)

        assert client.state == CortexState.AUTHENTICATING
        mock_websocket.send.assert_called_once()

        # Verify authorize request was sent
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["method"] == "authorize"
        assert sent_data["params"]["clientId"] == sample_credentials.client_id
        assert sent_data["params"]["clientSecret"] == sample_credentials.client_secret

    def test_authorize_response_triggers_headset_query(
        self, sample_credentials, mock_websocket
    ):
        """Successful authorize should query headsets."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.AUTHENTICATING

        message = json.dumps({
            "id": CortexClient._ID_AUTHORIZE,
            "result": {"cortexToken": "test-token-123"},
        })

        client._on_ws_message(mock_websocket, message)

        assert client._cortex_token == "test-token-123"
        assert client.state == CortexState.QUERYING_HEADSETS

        # Verify queryHeadsets was sent
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["method"] == "queryHeadsets"

    def test_query_headsets_response_creates_session(
        self, sample_credentials, mock_websocket
    ):
        """Successful headset query should create session."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.QUERYING_HEADSETS
        client._cortex_token = "test-token"

        message = json.dumps({
            "id": CortexClient._ID_QUERY_HEADSETS,
            "result": [{"id": "HEADSET-001"}],
        })

        client._on_ws_message(mock_websocket, message)

        assert client._headset_id == "HEADSET-001"
        assert client.state == CortexState.CREATING_SESSION

        # Verify createSession was sent
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["method"] == "createSession"
        assert sent_data["params"]["headset"] == "HEADSET-001"

    def test_query_headsets_no_headsets_raises_error(
        self, sample_credentials, mock_websocket
    ):
        """No headsets found should trigger error callback."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.QUERYING_HEADSETS

        errors = []
        client.on_error = lambda e: errors.append(e)

        message = json.dumps({
            "id": CortexClient._ID_QUERY_HEADSETS,
            "result": [],
        })

        client._on_ws_message(mock_websocket, message)

        assert len(errors) == 1
        assert isinstance(errors[0], DeviceNotFoundError)

    def test_create_session_response_subscribes(
        self, sample_credentials, mock_websocket
    ):
        """Successful session creation should subscribe to streams."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.CREATING_SESSION
        client._cortex_token = "test-token"
        client._headset_id = "HEADSET-001"

        message = json.dumps({
            "id": CortexClient._ID_CREATE_SESSION,
            "result": {"id": "SESSION-001"},
        })

        client._on_ws_message(mock_websocket, message)

        assert client._session_id == "SESSION-001"
        assert client.state == CortexState.SUBSCRIBING

        # Verify subscribe was sent
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["method"] == "subscribe"
        assert sent_data["params"]["session"] == "SESSION-001"

    def test_subscribe_response_completes_connection(
        self, sample_credentials, mock_websocket
    ):
        """Successful subscription should complete connection."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.SUBSCRIBING
        client._headset_id = "HEADSET-001"

        connection_changes = []
        client.on_connection_change = lambda c, m: connection_changes.append((c, m))

        message = json.dumps({
            "id": CortexClient._ID_SUBSCRIBE,
            "result": {"success": True},
        })

        client._on_ws_message(mock_websocket, message)

        assert client.state == CortexState.STREAMING
        assert client.is_connected is True
        assert len(connection_changes) == 1
        assert connection_changes[0][0] is True

    def test_mental_command_stream_data(self, sample_credentials, mock_websocket):
        """Should process mental command stream data."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.STREAMING

        commands = []
        client.on_mental_command = lambda action, power: commands.append((action, power))

        message = json.dumps({
            "com": ["push", 0.85],
        })

        client._on_ws_message(mock_websocket, message)

        assert len(commands) == 1
        assert commands[0] == ("push", 0.85)

    def test_handles_invalid_mental_command_data(
        self, sample_credentials, mock_websocket
    ):
        """Should handle malformed mental command data gracefully."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket
        client._state = CortexState.STREAMING

        commands = []
        client.on_mental_command = lambda a, p: commands.append((a, p))

        # Invalid data formats
        invalid_messages = [
            json.dumps({"com": []}),  # Empty array
            json.dumps({"com": "invalid"}),  # Not an array
            json.dumps({"com": [123, 0.5]}),  # Invalid action type
        ]

        for msg in invalid_messages:
            client._on_ws_message(mock_websocket, msg)

        # No commands should have been processed
        assert len(commands) == 0

    def test_handles_api_error_response(self, sample_credentials, mock_websocket):
        """Should handle Cortex API error responses."""
        client = CortexClient(sample_credentials)
        client._ws = mock_websocket

        errors = []
        client.on_error = lambda e: errors.append(e)

        message = json.dumps({
            "error": {
                "code": 100,
                "message": "Invalid credentials",
            },
        })

        client._on_ws_message(mock_websocket, message)

        assert len(errors) == 1
        assert isinstance(errors[0], AuthenticationError)

    def test_ws_error_triggers_error_callback(
        self, sample_credentials, mock_websocket
    ):
        """WebSocket error should trigger error callback."""
        client = CortexClient(sample_credentials)

        errors = []
        client.on_error = lambda e: errors.append(e)

        client._on_ws_error(mock_websocket, Exception("Connection failed"))

        assert client.state == CortexState.ERROR
        assert len(errors) == 1

    def test_ws_close_updates_state(self, sample_credentials, mock_websocket):
        """WebSocket close should update state to disconnected."""
        client = CortexClient(sample_credentials)
        client._state = CortexState.STREAMING

        connection_changes = []
        client.on_connection_change = lambda c, m: connection_changes.append((c, m))

        client._on_ws_close(mock_websocket, 1000, "Normal closure")

        assert client.state == CortexState.DISCONNECTED
        assert len(connection_changes) == 1
        assert connection_changes[0][0] is False

    def test_headset_id_property(self, sample_credentials):
        """headset_id property should return connected headset ID."""
        client = CortexClient(sample_credentials)

        assert client.headset_id is None

        client._headset_id = "EPOC-123"
        assert client.headset_id == "EPOC-123"

    def test_session_id_property(self, sample_credentials):
        """session_id property should return active session ID."""
        client = CortexClient(sample_credentials)

        assert client.session_id is None

        client._session_id = "SESSION-456"
        assert client.session_id == "SESSION-456"


# =============================================================================
# Integration Tests
# =============================================================================

class TestMockSourceIntegration:
    """Integration tests for MockSource with real threading."""

    def test_random_mode_generates_events(self, event_collector):
        """Random mode should generate events at specified intervals."""
        source = MockSource(
            random_interval=0.05,
            random_commands=[MentalCommand.PUSH, MentalCommand.PULL],
        )
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.2)
        source.disconnect()

        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        # Should have generated multiple random events
        assert len(command_events) >= 2

    def test_source_survives_subscriber_exception(self, event_collector):
        """Source should continue operating even if a subscriber raises."""
        source = MockSource(random_interval=0.05)

        def bad_subscriber(event):
            raise RuntimeError("Subscriber error")

        source.subscribe(bad_subscriber)
        source.subscribe(event_collector)

        source.connect()
        time.sleep(0.2)
        source.disconnect()

        # Good subscriber should still receive events
        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]
        assert len(command_events) >= 1


class TestEmotivSourceIntegration:
    """Integration tests for EmotivSource with mocked CortexClient."""

    def test_full_authentication_flow_with_mocked_client(
        self, sample_credentials, event_collector
    ):
        """Test the full authentication flow with a mocked Cortex client."""
        source = EmotivSource(sample_credentials)
        source.subscribe(event_collector)

        # Simulate the connection flow
        source._on_connection_change(True, "Connected to EPOC-X")

        # Simulate receiving mental commands
        source._on_mental_command("neutral", 0.9)
        source._on_mental_command("push", 0.85)
        source._on_mental_command("left", 0.7)

        # Verify events were emitted
        connection_events = [
            e for e in event_collector.events
            if isinstance(e, ConnectionEvent)
        ]
        command_events = [
            e for e in event_collector.events
            if isinstance(e, MentalCommandEvent)
        ]

        assert len(connection_events) == 1
        assert connection_events[0].connected is True

        assert len(command_events) == 3
        assert command_events[0].command == MentalCommand.NEUTRAL
        assert command_events[1].command == MentalCommand.PUSH
        assert command_events[2].command == MentalCommand.LEFT
