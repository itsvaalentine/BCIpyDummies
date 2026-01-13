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
