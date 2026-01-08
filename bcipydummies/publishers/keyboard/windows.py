"""Windows keyboard publisher implementation.

This module provides the Windows-specific keyboard publisher that uses
win32gui and win32con to simulate keyboard input to a target window.
"""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bcipydummies.core.events import EEGEvent

# Virtual key codes for Windows
# Reference: https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
VK_CODES: dict[str, int] = {
    # Letters (A-Z)
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45,
    "F": 0x46, "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A,
    "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E, "O": 0x4F,
    "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54,
    "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59,
    "Z": 0x5A,
    # Numbers (0-9)
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    # Function keys
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    # Arrow keys
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    # Modifier keys
    "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
    "LSHIFT": 0xA0, "RSHIFT": 0xA1,
    "LCTRL": 0xA2, "RCTRL": 0xA3,
    "LALT": 0xA4, "RALT": 0xA5,
    # Special keys
    "SPACE": 0x20, "ENTER": 0x0D, "RETURN": 0x0D,
    "TAB": 0x09, "ESCAPE": 0x1B, "ESC": 0x1B,
    "BACKSPACE": 0x08, "DELETE": 0x2E, "INSERT": 0x2D,
    "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
    # Numpad
    "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62,
    "NUMPAD3": 0x63, "NUMPAD4": 0x64, "NUMPAD5": 0x65,
    "NUMPAD6": 0x66, "NUMPAD7": 0x67, "NUMPAD8": 0x68,
    "NUMPAD9": 0x69,
    "MULTIPLY": 0x6A, "ADD": 0x6B, "SUBTRACT": 0x6D,
    "DECIMAL": 0x6E, "DIVIDE": 0x6F,
    # Additional keys
    "CAPSLOCK": 0x14, "NUMLOCK": 0x90, "SCROLLLOCK": 0x91,
    "PRINTSCREEN": 0x2C, "PAUSE": 0x13,
}


class WindowsKeyboardPublisher:
    """Windows-specific keyboard publisher using win32 API.

    This publisher sends keyboard events to a specific window using
    the Windows API. It requires the pywin32 package.

    Note:
        This class imports win32gui and win32con at runtime to avoid
        import errors on non-Windows platforms.

    Attributes:
        window_name: The title of the target window.
        hwnd: The window handle (set after start()).

    Example:
        publisher = WindowsKeyboardPublisher(window_name="My Game")
        with publisher:
            publisher.press_key("SPACE", hold=0.1)
    """

    def __init__(
        self,
        window_name: str | None = None,
        command_mapping: dict | None = None,
        power_threshold: float = 0.0,
        default_hold_time: float = 0.05,
        auto_focus: bool = True,
    ) -> None:
        """Initialize the Windows keyboard publisher.

        Args:
            window_name: Title of the target window. Can be set later.
            command_mapping: Optional dict mapping MentalCommand to key strings.
            power_threshold: Minimum power (0.0-1.0) to trigger key press.
            default_hold_time: Default key hold duration in seconds.
            auto_focus: Whether to automatically focus the window on start().

        Raises:
            ValueError: If power_threshold is not in range [0.0, 1.0].
        """
        if not 0.0 <= power_threshold <= 1.0:
            raise ValueError(f"power_threshold must be between 0.0 and 1.0, got {power_threshold}")

        self._window_name = window_name
        self._command_mapping: dict = command_mapping or {}
        self._power_threshold = power_threshold
        self._default_hold_time = default_hold_time
        self._auto_focus = auto_focus
        self._hwnd: int | None = None
        self._is_ready = False
        self._win32gui = None
        self._win32con = None

    @property
    def window_name(self) -> str | None:
        """Get the target window name."""
        return self._window_name

    @window_name.setter
    def window_name(self, name: str) -> None:
        """Set the target window name.

        Setting this while the publisher is running will update
        the target window on the next key press.
        """
        self._window_name = name
        if self._is_ready:
            self._hwnd = self._find_window(name)

    @property
    def hwnd(self) -> int | None:
        """Get the current window handle."""
        return self._hwnd

    @property
    def command_mapping(self) -> dict:
        """Get the current command-to-key mapping."""
        return self._command_mapping

    @command_mapping.setter
    def command_mapping(self, mapping: dict) -> None:
        """Set the command-to-key mapping."""
        self._command_mapping = mapping

    @property
    def power_threshold(self) -> float:
        """Get the current power threshold."""
        return self._power_threshold

    @power_threshold.setter
    def power_threshold(self, threshold: float) -> None:
        """Set the power threshold."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"power_threshold must be between 0.0 and 1.0, got {threshold}")
        self._power_threshold = threshold

    @property
    def default_hold_time(self) -> float:
        """Get the default key hold time in seconds."""
        return self._default_hold_time

    @default_hold_time.setter
    def default_hold_time(self, hold_time: float) -> None:
        """Set the default key hold time."""
        if hold_time <= 0:
            raise ValueError(f"default_hold_time must be positive, got {hold_time}")
        self._default_hold_time = hold_time

    @property
    def is_ready(self) -> bool:
        """Check if the publisher is ready."""
        return self._is_ready

    @staticmethod
    def list_windows() -> list[str]:
        """List all visible windows.

        Returns:
            List of window titles for all visible windows.

        Note:
            This method imports win32gui dynamically.
        """
        import win32gui

        windows: list[str] = []

        def callback(hwnd: int, _) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append(title)
            return True

        win32gui.EnumWindows(callback, None)
        return windows

    @staticmethod
    def find_windows_matching(pattern: str) -> list[tuple[int, str]]:
        """Find windows whose titles contain the given pattern.

        Args:
            pattern: Substring to search for in window titles (case-insensitive).

        Returns:
            List of (hwnd, title) tuples for matching windows.
        """
        import win32gui

        matches: list[tuple[int, str]] = []
        pattern_lower = pattern.lower()

        def callback(hwnd: int, _) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and pattern_lower in title.lower():
                    matches.append((hwnd, title))
            return True

        win32gui.EnumWindows(callback, None)
        return matches

    def _find_window(self, title: str) -> int:
        """Find a window by exact title.

        Args:
            title: Exact window title to find.

        Returns:
            Window handle (hwnd).

        Raises:
            WindowNotFoundError: If the window is not found.
        """
        hwnd = self._win32gui.FindWindow(None, title)
        if not hwnd:
            from bcipydummies.core.exceptions import WindowNotFoundError
            raise WindowNotFoundError(f"Window not found: '{title}'")
        return hwnd

    def find_window(self, name: str) -> int:
        """Find a window by name and update the target.

        Args:
            name: Window title to search for.

        Returns:
            Window handle (hwnd).

        Raises:
            WindowNotFoundError: If the window is not found.
            RuntimeError: If the publisher is not started.
        """
        if not self._is_ready:
            raise RuntimeError("Publisher not started. Call start() first.")

        self._window_name = name
        self._hwnd = self._find_window(name)
        return self._hwnd

    def start(self) -> None:
        """Initialize the Windows keyboard publisher.

        Imports win32 modules, finds the target window, and optionally
        brings it to the foreground.

        Raises:
            ImportError: If pywin32 is not installed.
            WindowNotFoundError: If the target window is not found.
        """
        try:
            import win32gui
            import win32con
            self._win32gui = win32gui
            self._win32con = win32con
        except ImportError as e:
            raise ImportError(
                "pywin32 is required for WindowsKeyboardPublisher. "
                "Install it with: pip install pywin32"
            ) from e

        if self._window_name:
            self._hwnd = self._find_window(self._window_name)

            if self._auto_focus:
                self._focus_window()

        self._is_ready = True

    def stop(self) -> None:
        """Stop the Windows keyboard publisher.

        Cleans up resources and marks as not ready.
        Safe to call multiple times.
        """
        self._is_ready = False
        self._hwnd = None

    def _focus_window(self) -> None:
        """Bring the target window to the foreground."""
        if self._hwnd and self._win32gui:
            try:
                self._win32gui.SetForegroundWindow(self._hwnd)
                time.sleep(0.1)  # Brief pause for window focus
            except Exception:
                # Window may have been closed or cannot be focused
                pass

    def press_key(self, key: str, hold: float | None = None) -> None:
        """Simulate a key press and release.

        Args:
            key: The key to press (e.g., "A", "SPACE", "ENTER").
                 Case-insensitive.
            hold: Duration to hold the key in seconds. Uses default_hold_time if None.

        Raises:
            ValueError: If the key is not recognized.
            RuntimeError: If the publisher is not ready or no window is targeted.
        """
        if not self._is_ready:
            raise RuntimeError("Publisher not started. Call start() first.")

        if self._hwnd is None:
            raise RuntimeError("No target window. Set window_name or call find_window().")

        key_upper = key.upper()
        if key_upper not in VK_CODES:
            raise ValueError(
                f"Unrecognized key: '{key}'. "
                f"Valid keys: {', '.join(sorted(VK_CODES.keys()))}"
            )

        hold_time = hold if hold is not None else self._default_hold_time
        vk_code = VK_CODES[key_upper]

        # Send key down
        self._win32gui.PostMessage(
            self._hwnd,
            self._win32con.WM_KEYDOWN,
            vk_code,
            0
        )

        # Hold
        if hold_time > 0:
            time.sleep(hold_time)

        # Send key up
        self._win32gui.PostMessage(
            self._hwnd,
            self._win32con.WM_KEYUP,
            vk_code,
            0
        )

    def press_keys(self, keys: list[str], hold: float | None = None) -> None:
        """Press multiple keys in sequence.

        Args:
            keys: List of keys to press in order.
            hold: Hold time for each key. Uses default_hold_time if None.
        """
        for key in keys:
            self.press_key(key, hold)

    def publish(self, event: "EEGEvent") -> None:
        """Publish an EEG event as keyboard input.

        For MentalCommandEvent, looks up the command in command_mapping
        and presses the corresponding key if power exceeds threshold.

        Args:
            event: The EEG event to publish.

        Raises:
            RuntimeError: If the publisher is not ready.
        """
        if not self._is_ready:
            raise RuntimeError("Keyboard publisher not started. Call start() first.")

        # Import here to avoid circular imports at module level
        from bcipydummies.core.events import MentalCommandEvent

        if isinstance(event, MentalCommandEvent):
            self._handle_mental_command(event)

    def _handle_mental_command(self, event) -> None:
        """Handle a mental command event.

        Args:
            event: The mental command event to process.
        """
        if event.power < self._power_threshold:
            return

        key = self._command_mapping.get(event.command)
        if key is None:
            return

        self.press_key(key, self._default_hold_time)

    def __enter__(self) -> "WindowsKeyboardPublisher":
        """Context manager entry - starts the publisher."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the publisher."""
        self.stop()
