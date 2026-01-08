"""Tests for BCIpyDummies publishers module.

This module contains comprehensive tests for:
- ConsolePublisher: Output events to stdout
- KeyboardPublisher (base): Abstract keyboard publishing
- WindowsKeyboardPublisher: Windows-specific keyboard simulation
"""

import io
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, call

from bcipydummies.publishers.console import ConsolePublisher
from bcipydummies.publishers.keyboard.base import (
    KeyboardPublisher,
    get_keyboard_publisher_class,
    create_keyboard_publisher,
)
from bcipydummies.publishers.keyboard.windows import (
    WindowsKeyboardPublisher,
    VK_CODES,
)
from bcipydummies.core.events import MentalCommand, MentalCommandEvent, EEGEvent


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mock_stdout():
    """Provide a StringIO buffer to capture stdout output."""
    return io.StringIO()


@pytest.fixture
def sample_mental_command_event():
    """Create a sample MentalCommandEvent for testing."""
    return MentalCommandEvent(
        timestamp=1234567890.0,
        source_id="test-headset",
        command=MentalCommand.PUSH,
        power=0.75,
    )


@pytest.fixture
def sample_eeg_event():
    """Create a sample base EEGEvent for testing."""
    return EEGEvent(
        timestamp=1234567890.0,
        source_id="test-headset",
    )


@pytest.fixture
def mock_win32gui():
    """Create mock win32gui module."""
    mock = MagicMock()
    mock.FindWindow = MagicMock(return_value=12345)
    mock.IsWindowVisible = MagicMock(return_value=True)
    mock.GetWindowText = MagicMock(side_effect=lambda hwnd: f"Window{hwnd}")
    mock.EnumWindows = MagicMock()
    mock.SetForegroundWindow = MagicMock()
    mock.PostMessage = MagicMock()
    return mock


@pytest.fixture
def mock_win32con():
    """Create mock win32con module."""
    mock = MagicMock()
    mock.WM_KEYDOWN = 0x0100
    mock.WM_KEYUP = 0x0101
    return mock


# ===========================================================================
# ConsolePublisher Tests
# ===========================================================================


class TestConsolePublisher:
    """Tests for ConsolePublisher class."""

    def test_publish_event_to_stdout(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should publish events to stdout."""
        publisher = ConsolePublisher(stream=mock_stdout)
        publisher.start()

        publisher.publish(sample_mental_command_event)

        output = mock_stdout.getvalue()
        assert "MentalCommandEvent" in output
        publisher.stop()

    def test_custom_format_string(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should support custom format strings."""
        custom_format = "EVENT: {event_type} - {event}"
        publisher = ConsolePublisher(
            format_string=custom_format,
            stream=mock_stdout,
            include_timestamp=False,
        )
        publisher.start()

        publisher.publish(sample_mental_command_event)

        output = mock_stdout.getvalue()
        assert "EVENT: MentalCommandEvent" in output
        publisher.stop()

    def test_prefix_is_added(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should add prefix to all messages."""
        prefix = "[DEBUG]"
        publisher = ConsolePublisher(prefix=prefix, stream=mock_stdout)
        publisher.start()

        publisher.publish(sample_mental_command_event)

        output = mock_stdout.getvalue()
        # Prefix should appear in both start message and event output
        lines = output.strip().split("\n")
        for line in lines:
            assert line.startswith(prefix)
        publisher.stop()

    def test_event_counter_increments(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should increment event counter on each publish."""
        publisher = ConsolePublisher(stream=mock_stdout)
        publisher.start()

        assert publisher.event_count == 0

        publisher.publish(sample_mental_command_event)
        assert publisher.event_count == 1

        publisher.publish(sample_mental_command_event)
        assert publisher.event_count == 2

        publisher.publish(sample_mental_command_event)
        assert publisher.event_count == 3

        publisher.stop()

    def test_event_counter_resets_on_start(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher event counter should reset when start() is called."""
        publisher = ConsolePublisher(stream=mock_stdout)
        publisher.start()

        publisher.publish(sample_mental_command_event)
        publisher.publish(sample_mental_command_event)
        assert publisher.event_count == 2

        publisher.stop()
        publisher.start()
        assert publisher.event_count == 0

        publisher.stop()

    def test_start_stop_lifecycle(self, mock_stdout):
        """ConsolePublisher should follow proper start/stop lifecycle."""
        publisher = ConsolePublisher(stream=mock_stdout)

        # Should not be ready before start
        assert publisher.is_ready is False

        # Start should mark as ready
        publisher.start()
        assert publisher.is_ready is True

        output = mock_stdout.getvalue()
        assert "started" in output.lower()

        # Stop should mark as not ready
        publisher.stop()
        assert publisher.is_ready is False

        output = mock_stdout.getvalue()
        assert "stopped" in output.lower()

    def test_is_ready_property(self, mock_stdout):
        """ConsolePublisher is_ready property should reflect internal state."""
        publisher = ConsolePublisher(stream=mock_stdout)

        assert publisher.is_ready is False
        publisher.start()
        assert publisher.is_ready is True
        publisher.stop()
        assert publisher.is_ready is False

    def test_publish_raises_if_not_started(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should raise RuntimeError if publish called before start."""
        publisher = ConsolePublisher(stream=mock_stdout)

        with pytest.raises(RuntimeError, match="not started"):
            publisher.publish(sample_mental_command_event)

    def test_context_manager_protocol(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should work as context manager."""
        publisher = ConsolePublisher(stream=mock_stdout)

        assert publisher.is_ready is False

        with publisher:
            assert publisher.is_ready is True
            publisher.publish(sample_mental_command_event)

        assert publisher.is_ready is False

    def test_stop_is_idempotent(self, mock_stdout):
        """ConsolePublisher stop() should be safe to call multiple times."""
        publisher = ConsolePublisher(stream=mock_stdout)
        publisher.start()

        # Should not raise on multiple stops
        publisher.stop()
        publisher.stop()
        publisher.stop()

        assert publisher.is_ready is False

    def test_default_format_includes_timestamp(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher default format should include timestamp."""
        publisher = ConsolePublisher(stream=mock_stdout)
        publisher.start()

        publisher.publish(sample_mental_command_event)

        output = mock_stdout.getvalue()
        # ISO timestamp format contains 'T' between date and time
        # Check for timestamp bracket pattern
        assert "[" in output and "]" in output
        publisher.stop()

    def test_timestamp_can_be_disabled(self, mock_stdout, sample_mental_command_event):
        """ConsolePublisher should allow disabling timestamps."""
        publisher = ConsolePublisher(
            stream=mock_stdout,
            format_string="{event_type}",
            include_timestamp=False,
        )
        publisher.start()

        publisher.publish(sample_mental_command_event)

        output = mock_stdout.getvalue()
        # Just the event type, no timestamp
        assert "MentalCommandEvent" in output
        publisher.stop()


# ===========================================================================
# KeyboardPublisher Base Tests
# ===========================================================================


class TestKeyboardPublisherBase:
    """Tests for KeyboardPublisher abstract base class."""

    def test_command_to_key_mapping(self):
        """KeyboardPublisher should store command-to-key mappings."""
        mapping = {
            MentalCommand.LEFT: "A",
            MentalCommand.RIGHT: "D",
            MentalCommand.PUSH: "SPACE",
        }

        publisher = WindowsKeyboardPublisher(command_mapping=mapping)

        assert publisher.command_mapping[MentalCommand.LEFT] == "A"
        assert publisher.command_mapping[MentalCommand.RIGHT] == "D"
        assert publisher.command_mapping[MentalCommand.PUSH] == "SPACE"

    def test_command_mapping_can_be_updated(self):
        """KeyboardPublisher command mapping should be updateable."""
        publisher = WindowsKeyboardPublisher()

        assert publisher.command_mapping == {}

        new_mapping = {MentalCommand.PUSH: "ENTER"}
        publisher.command_mapping = new_mapping

        assert publisher.command_mapping[MentalCommand.PUSH] == "ENTER"

    def test_power_threshold_filtering(self):
        """KeyboardPublisher should filter events below power threshold."""
        mapping = {MentalCommand.PUSH: "SPACE"}

        # Create publisher with high threshold
        publisher = WindowsKeyboardPublisher(
            window_name="TestWindow",
            command_mapping=mapping,
            power_threshold=0.8,
        )

        # Track key presses
        pressed_keys = []

        def mock_press_key(key, hold=None):
            pressed_keys.append(key)

        # Patch start to avoid win32gui import
        with patch.object(publisher, '_win32gui', MagicMock()):
            with patch.object(publisher, '_win32con', MagicMock()):
                publisher._is_ready = True
                publisher._hwnd = 12345
                publisher.press_key = mock_press_key

                # Low power event - should be filtered
                low_power_event = MentalCommandEvent(
                    timestamp=1234567890.0,
                    source_id="test",
                    command=MentalCommand.PUSH,
                    power=0.5,
                )
                publisher.publish(low_power_event)
                assert len(pressed_keys) == 0

                # High power event - should trigger key press
                high_power_event = MentalCommandEvent(
                    timestamp=1234567890.0,
                    source_id="test",
                    command=MentalCommand.PUSH,
                    power=0.9,
                )
                publisher.publish(high_power_event)
                assert len(pressed_keys) == 1
                assert pressed_keys[0] == "SPACE"

    def test_power_threshold_validation(self):
        """KeyboardPublisher should validate power threshold range."""
        # Valid thresholds
        WindowsKeyboardPublisher(power_threshold=0.0)
        WindowsKeyboardPublisher(power_threshold=0.5)
        WindowsKeyboardPublisher(power_threshold=1.0)

        # Invalid thresholds
        with pytest.raises(ValueError, match="power_threshold"):
            WindowsKeyboardPublisher(power_threshold=-0.1)

        with pytest.raises(ValueError, match="power_threshold"):
            WindowsKeyboardPublisher(power_threshold=1.1)

    def test_power_threshold_setter_validation(self):
        """KeyboardPublisher power_threshold setter should validate range."""
        publisher = WindowsKeyboardPublisher()

        publisher.power_threshold = 0.5
        assert publisher.power_threshold == 0.5

        with pytest.raises(ValueError):
            publisher.power_threshold = 1.5

    def test_action_field_used_for_key_lookup(self):
        """KeyboardPublisher should use command mapping for key lookup."""
        mapping = {
            MentalCommand.LEFT: "A",
            MentalCommand.RIGHT: "D",
        }
        publisher = WindowsKeyboardPublisher(command_mapping=mapping)

        pressed_keys = []

        def mock_press_key(key, hold=None):
            pressed_keys.append(key)

        with patch.object(publisher, '_win32gui', MagicMock()):
            with patch.object(publisher, '_win32con', MagicMock()):
                publisher._is_ready = True
                publisher._hwnd = 12345
                publisher.press_key = mock_press_key

                event = MentalCommandEvent(
                    timestamp=1234567890.0,
                    source_id="test",
                    command=MentalCommand.LEFT,
                    power=0.8,
                )
                publisher.publish(event)

                assert pressed_keys == ["A"]

    def test_is_ready_false_before_start(self):
        """KeyboardPublisher is_ready should be False before start() is called."""
        publisher = WindowsKeyboardPublisher()
        assert publisher.is_ready is False

    def test_default_hold_time(self):
        """KeyboardPublisher should have configurable default hold time."""
        publisher = WindowsKeyboardPublisher(default_hold_time=0.1)
        assert publisher.default_hold_time == 0.1

        publisher.default_hold_time = 0.2
        assert publisher.default_hold_time == 0.2

    def test_default_hold_time_validation(self):
        """KeyboardPublisher should validate default_hold_time is positive."""
        publisher = WindowsKeyboardPublisher()

        with pytest.raises(ValueError, match="positive"):
            publisher.default_hold_time = 0

        with pytest.raises(ValueError, match="positive"):
            publisher.default_hold_time = -0.1

    def test_unmapped_command_is_ignored(self):
        """KeyboardPublisher should ignore commands not in mapping."""
        mapping = {MentalCommand.LEFT: "A"}  # Only LEFT is mapped

        publisher = WindowsKeyboardPublisher(command_mapping=mapping)

        pressed_keys = []

        def mock_press_key(key, hold=None):
            pressed_keys.append(key)

        with patch.object(publisher, '_win32gui', MagicMock()):
            with patch.object(publisher, '_win32con', MagicMock()):
                publisher._is_ready = True
                publisher._hwnd = 12345
                publisher.press_key = mock_press_key

                # RIGHT is not mapped, should be ignored
                event = MentalCommandEvent(
                    timestamp=1234567890.0,
                    source_id="test",
                    command=MentalCommand.RIGHT,
                    power=0.8,
                )
                publisher.publish(event)

                assert len(pressed_keys) == 0

    def test_non_mental_command_event_is_ignored(self):
        """KeyboardPublisher should ignore non-MentalCommandEvent events."""
        publisher = WindowsKeyboardPublisher(
            command_mapping={MentalCommand.PUSH: "SPACE"}
        )

        pressed_keys = []

        def mock_press_key(key, hold=None):
            pressed_keys.append(key)

        with patch.object(publisher, '_win32gui', MagicMock()):
            with patch.object(publisher, '_win32con', MagicMock()):
                publisher._is_ready = True
                publisher._hwnd = 12345
                publisher.press_key = mock_press_key

                # Base EEGEvent should be ignored
                event = EEGEvent(
                    timestamp=1234567890.0,
                    source_id="test",
                )
                publisher.publish(event)

                assert len(pressed_keys) == 0


# ===========================================================================
# WindowsKeyboardPublisher Tests
# ===========================================================================


class TestWindowsKeyboardPublisher:
    """Tests for WindowsKeyboardPublisher class."""

    def test_list_windows_returns_list(self, mock_win32gui):
        """list_windows() should return a list of window titles."""
        fake_windows = ["Notepad", "Chrome", "Game"]

        def fake_enum(callback, _):
            for i, _ in enumerate(fake_windows):
                callback(i, None)

        mock_win32gui.EnumWindows = fake_enum
        mock_win32gui.GetWindowText = lambda hwnd: fake_windows[hwnd]
        mock_win32gui.IsWindowVisible = lambda hwnd: True

        with patch.dict(sys.modules, {"win32gui": mock_win32gui}):
            windows = WindowsKeyboardPublisher.list_windows()

        assert isinstance(windows, list)
        assert "Notepad" in windows
        assert "Chrome" in windows
        assert "Game" in windows

    def test_list_windows_excludes_invisible(self, mock_win32gui):
        """list_windows() should exclude invisible windows."""
        fake_windows = ["Visible", "Hidden"]

        def fake_enum(callback, _):
            for i, _ in enumerate(fake_windows):
                callback(i, None)

        mock_win32gui.EnumWindows = fake_enum
        mock_win32gui.GetWindowText = lambda hwnd: fake_windows[hwnd]
        mock_win32gui.IsWindowVisible = lambda hwnd: hwnd == 0  # Only first is visible

        with patch.dict(sys.modules, {"win32gui": mock_win32gui}):
            windows = WindowsKeyboardPublisher.list_windows()

        assert "Visible" in windows
        assert "Hidden" not in windows

    def test_list_windows_excludes_empty_titles(self, mock_win32gui):
        """list_windows() should exclude windows with empty titles."""

        def fake_enum(callback, _):
            callback(0, None)
            callback(1, None)

        mock_win32gui.EnumWindows = fake_enum
        mock_win32gui.GetWindowText = lambda hwnd: "Window" if hwnd == 0 else ""
        mock_win32gui.IsWindowVisible = lambda hwnd: True

        with patch.dict(sys.modules, {"win32gui": mock_win32gui}):
            windows = WindowsKeyboardPublisher.list_windows()

        assert windows == ["Window"]

    def test_find_window_finds_by_name(self, mock_win32gui, mock_win32con):
        """find_window() should find window by exact name."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        publisher = WindowsKeyboardPublisher(window_name="TestGame")

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()

            assert publisher.hwnd == 12345
            mock_win32gui.FindWindow.assert_called_with(None, "TestGame")

            publisher.stop()

    def test_find_window_raises_if_not_found(self, mock_win32gui, mock_win32con):
        """find_window() should raise WindowNotFoundError if window not found."""
        mock_win32gui.FindWindow = MagicMock(return_value=0)

        publisher = WindowsKeyboardPublisher(window_name="NonExistent")

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            from bcipydummies.core.exceptions import WindowNotFoundError

            with pytest.raises(WindowNotFoundError):
                publisher.start()

    def test_find_window_requires_start(self, mock_win32gui):
        """find_window() should require publisher to be started."""
        publisher = WindowsKeyboardPublisher()

        with pytest.raises(RuntimeError, match="not started"):
            publisher.find_window("SomeWindow")

    def test_press_key_sends_correct_messages(self, mock_win32gui, mock_win32con):
        """press_key() should send WM_KEYDOWN and WM_KEYUP messages."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        publisher = WindowsKeyboardPublisher(
            window_name="TestWindow",
            default_hold_time=0.001,  # Minimal hold for fast tests
        )

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()
            publisher.press_key("A")

            # Should have called PostMessage for keydown and keyup
            assert mock_win32gui.PostMessage.call_count == 2

            calls = mock_win32gui.PostMessage.call_args_list

            # First call: keydown
            assert calls[0] == call(
                12345,
                mock_win32con.WM_KEYDOWN,
                VK_CODES["A"],
                0
            )

            # Second call: keyup
            assert calls[1] == call(
                12345,
                mock_win32con.WM_KEYUP,
                VK_CODES["A"],
                0
            )

            publisher.stop()

    def test_press_key_case_insensitive(self, mock_win32gui, mock_win32con):
        """press_key() should be case-insensitive."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        publisher = WindowsKeyboardPublisher(
            window_name="TestWindow",
            default_hold_time=0.001,
        )

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()

            # Both should work and use same VK code
            publisher.press_key("a")
            publisher.press_key("A")
            publisher.press_key("space")
            publisher.press_key("SPACE")

            # All should have succeeded (4 keys * 2 messages each = 8)
            assert mock_win32gui.PostMessage.call_count == 8

            publisher.stop()

    def test_press_key_raises_for_unknown_key(self, mock_win32gui, mock_win32con):
        """press_key() should raise ValueError for unknown keys."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        publisher = WindowsKeyboardPublisher(window_name="TestWindow")

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()

            with pytest.raises(ValueError, match="Unrecognized key"):
                publisher.press_key("INVALID_KEY")

            publisher.stop()

    def test_press_key_requires_start(self):
        """press_key() should require publisher to be started."""
        publisher = WindowsKeyboardPublisher()

        with pytest.raises(RuntimeError, match="not started"):
            publisher.press_key("A")

    def test_press_key_requires_target_window(self, mock_win32gui, mock_win32con):
        """press_key() should require a target window."""
        publisher = WindowsKeyboardPublisher()  # No window_name

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()  # No window set

            with pytest.raises(RuntimeError, match="No target window"):
                publisher.press_key("A")

            publisher.stop()

    def test_vk_codes_contains_expected_keys(self):
        """VK_CODES dictionary should contain expected key mappings."""
        # Letters
        assert "A" in VK_CODES
        assert "Z" in VK_CODES

        # Numbers
        assert "0" in VK_CODES
        assert "9" in VK_CODES

        # Arrow keys
        assert "LEFT" in VK_CODES
        assert "RIGHT" in VK_CODES
        assert "UP" in VK_CODES
        assert "DOWN" in VK_CODES

        # Function keys
        assert "F1" in VK_CODES
        assert "F12" in VK_CODES

        # Special keys
        assert "SPACE" in VK_CODES
        assert "ENTER" in VK_CODES
        assert "ESCAPE" in VK_CODES
        assert "TAB" in VK_CODES
        assert "BACKSPACE" in VK_CODES

        # Modifiers
        assert "SHIFT" in VK_CODES
        assert "CTRL" in VK_CODES
        assert "ALT" in VK_CODES

    def test_vk_codes_values_are_integers(self):
        """VK_CODES values should all be integers."""
        for key, code in VK_CODES.items():
            assert isinstance(code, int), f"VK_CODE for '{key}' is not int: {type(code)}"

    def test_vk_codes_letters_are_correct(self):
        """VK_CODES letter mappings should use correct values (0x41-0x5A)."""
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            expected = 0x41 + i
            assert VK_CODES[letter] == expected, f"VK_CODE for '{letter}' is wrong"

    def test_vk_codes_numbers_are_correct(self):
        """VK_CODES number mappings should use correct values (0x30-0x39)."""
        for i, digit in enumerate("0123456789"):
            expected = 0x30 + i
            assert VK_CODES[digit] == expected, f"VK_CODE for '{digit}' is wrong"

    def test_press_keys_multiple(self, mock_win32gui, mock_win32con):
        """press_keys() should press multiple keys in sequence."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        publisher = WindowsKeyboardPublisher(
            window_name="TestWindow",
            default_hold_time=0.001,
        )

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()
            publisher.press_keys(["A", "B", "C"])

            # 3 keys * 2 messages each = 6 calls
            assert mock_win32gui.PostMessage.call_count == 6

            publisher.stop()

    def test_context_manager_protocol(self, mock_win32gui, mock_win32con):
        """WindowsKeyboardPublisher should work as context manager."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher = WindowsKeyboardPublisher(window_name="TestWindow")

            assert publisher.is_ready is False

            with publisher:
                assert publisher.is_ready is True
                assert publisher.hwnd == 12345

            assert publisher.is_ready is False
            assert publisher.hwnd is None

    def test_window_name_can_be_changed_while_running(self, mock_win32gui, mock_win32con):
        """window_name setter should update target window when running."""
        mock_win32gui.FindWindow = MagicMock(side_effect=[12345, 67890])

        publisher = WindowsKeyboardPublisher(window_name="Window1")

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher.start()
            assert publisher.hwnd == 12345

            publisher.window_name = "Window2"
            assert publisher.hwnd == 67890

            publisher.stop()

    def test_auto_focus_setting(self, mock_win32gui, mock_win32con):
        """WindowsKeyboardPublisher should respect auto_focus setting."""
        mock_win32gui.FindWindow = MagicMock(return_value=12345)

        # With auto_focus=True (default)
        publisher1 = WindowsKeyboardPublisher(
            window_name="TestWindow",
            auto_focus=True,
        )

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher1.start()
            mock_win32gui.SetForegroundWindow.assert_called()
            publisher1.stop()

        mock_win32gui.reset_mock()

        # With auto_focus=False
        publisher2 = WindowsKeyboardPublisher(
            window_name="TestWindow",
            auto_focus=False,
        )

        with patch.dict(sys.modules, {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }):
            publisher2.start()
            mock_win32gui.SetForegroundWindow.assert_not_called()
            publisher2.stop()

    def test_publish_raises_if_not_started(self):
        """publish() should raise RuntimeError if called before start()."""
        publisher = WindowsKeyboardPublisher()

        event = MentalCommandEvent(
            timestamp=1234567890.0,
            source_id="test",
            command=MentalCommand.PUSH,
            power=0.8,
        )

        with pytest.raises(RuntimeError, match="not started"):
            publisher.publish(event)

    def test_find_windows_matching(self, mock_win32gui):
        """find_windows_matching() should find windows by pattern."""
        fake_windows = {
            0: "Game - Level 1",
            1: "Chrome Browser",
            2: "Game - Level 2",
            3: "Notepad",
        }

        def fake_enum(callback, _):
            for hwnd in fake_windows:
                callback(hwnd, None)

        mock_win32gui.EnumWindows = fake_enum
        mock_win32gui.GetWindowText = lambda hwnd: fake_windows.get(hwnd, "")
        mock_win32gui.IsWindowVisible = lambda hwnd: True

        with patch.dict(sys.modules, {"win32gui": mock_win32gui}):
            matches = WindowsKeyboardPublisher.find_windows_matching("game")

        assert len(matches) == 2
        hwnds = [m[0] for m in matches]
        titles = [m[1] for m in matches]
        assert 0 in hwnds
        assert 2 in hwnds
        assert "Game - Level 1" in titles
        assert "Game - Level 2" in titles


# ===========================================================================
# Platform Factory Function Tests
# ===========================================================================


class TestPlatformFactory:
    """Tests for platform-specific factory functions."""

    def test_get_keyboard_publisher_class_on_windows(self):
        """get_keyboard_publisher_class() should return WindowsKeyboardPublisher on Windows."""
        with patch.object(sys, "platform", "win32"):
            cls = get_keyboard_publisher_class()
            assert cls is WindowsKeyboardPublisher

    def test_get_keyboard_publisher_class_raises_on_macos(self):
        """get_keyboard_publisher_class() should raise NotImplementedError on macOS."""
        with patch.object(sys, "platform", "darwin"):
            with pytest.raises(NotImplementedError, match="macOS"):
                get_keyboard_publisher_class()

    def test_get_keyboard_publisher_class_raises_on_linux(self):
        """get_keyboard_publisher_class() should raise NotImplementedError on Linux."""
        with patch.object(sys, "platform", "linux"):
            with pytest.raises(NotImplementedError, match="Linux"):
                get_keyboard_publisher_class()

    def test_get_keyboard_publisher_class_raises_on_unknown(self):
        """get_keyboard_publisher_class() should raise NotImplementedError on unknown platforms."""
        with patch.object(sys, "platform", "unknown"):
            with pytest.raises(NotImplementedError, match="Unsupported platform"):
                get_keyboard_publisher_class()

    def test_create_keyboard_publisher_on_windows(self):
        """create_keyboard_publisher() should create WindowsKeyboardPublisher on Windows."""
        with patch.object(sys, "platform", "win32"):
            publisher = create_keyboard_publisher(power_threshold=0.5)

            assert isinstance(publisher, WindowsKeyboardPublisher)
            assert publisher.power_threshold == 0.5
