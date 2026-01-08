"""
List windows command implementation.

Lists available windows that can be targeted for keyboard output.
"""

import argparse
import fnmatch
import sys
from typing import List, Optional, Tuple

from .base import BaseCommand


class ListWindowsCommand(BaseCommand):
    """Command to list available windows."""

    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the list-windows command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        filter_pattern = getattr(args, "filter", None)

        try:
            windows = self._get_windows()
        except NotImplementedError as e:
            self.error(str(e))
            return 1
        except Exception as e:
            self.error(f"Failed to enumerate windows: {e}")
            return 1

        # Apply filter if specified
        if filter_pattern:
            windows = self._filter_windows(windows, filter_pattern)

        # Display results
        if not windows:
            if filter_pattern:
                print(f"No windows matching '{filter_pattern}' found.")
            else:
                print("No windows found.")
            return 0

        self._print_windows(windows)
        return 0

    def _get_windows(self) -> List[Tuple[str, str]]:
        """
        Get list of available windows.

        Returns:
            List of (window_id, window_title) tuples.

        Raises:
            NotImplementedError: If platform is not supported.
        """
        platform = sys.platform

        if platform == "win32":
            return self._get_windows_win32()
        elif platform == "darwin":
            return self._get_windows_macos()
        elif platform.startswith("linux"):
            return self._get_windows_linux()
        else:
            raise NotImplementedError(
                f"Window enumeration not supported on platform: {platform}"
            )

    def _get_windows_win32(self) -> List[Tuple[str, str]]:
        """Get windows on Windows platform."""
        try:
            import win32gui
        except ImportError:
            raise NotImplementedError(
                "pywin32 is required for window enumeration on Windows. "
                "Install it with: pip install pywin32"
            )

        windows = []

        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Skip windows without titles
                    results.append((str(hwnd), title))
            return True

        win32gui.EnumWindows(enum_callback, windows)
        return windows

    def _get_windows_macos(self) -> List[Tuple[str, str]]:
        """Get windows on macOS platform."""
        import subprocess

        try:
            # Use AppleScript to get window list
            script = '''
            tell application "System Events"
                set windowList to {}
                repeat with proc in (every process whose background only is false)
                    set procName to name of proc
                    repeat with win in (every window of proc)
                        set winName to name of win
                        set end of windowList to procName & ": " & winName
                    end repeat
                end repeat
                return windowList
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Fall back to listing applications
                return self._get_apps_macos()

            # Parse the output
            windows = []
            output = result.stdout.strip()

            if output:
                # AppleScript returns comma-separated list
                items = output.split(", ")
                for i, item in enumerate(items):
                    windows.append((str(i), item))

            return windows

        except subprocess.TimeoutExpired:
            return self._get_apps_macos()
        except FileNotFoundError:
            raise NotImplementedError(
                "osascript not found. Cannot enumerate windows on this system."
            )

    def _get_apps_macos(self) -> List[Tuple[str, str]]:
        """Get running applications on macOS as fallback."""
        import subprocess

        script = '''
        tell application "System Events"
            set appNames to name of every process whose background only is false
            return appNames
        end tell
        '''

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        apps = []
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                items = output.split(", ")
                for i, item in enumerate(items):
                    apps.append((str(i), item))

        return apps

    def _get_windows_linux(self) -> List[Tuple[str, str]]:
        """Get windows on Linux platform."""
        import subprocess

        try:
            # Try using wmctrl
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                windows = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            window_id = parts[0]
                            title = parts[3]
                            windows.append((window_id, title))
                return windows

        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # Try using xdotool as fallback
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", ""],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                windows = []
                for window_id in result.stdout.strip().split("\n"):
                    if window_id:
                        # Get window title
                        name_result = subprocess.run(
                            ["xdotool", "getwindowname", window_id],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        title = name_result.stdout.strip() if name_result.returncode == 0 else "Unknown"
                        windows.append((window_id, title))
                return windows

        except FileNotFoundError:
            raise NotImplementedError(
                "Neither wmctrl nor xdotool found. "
                "Install one of them to enumerate windows on Linux: "
                "sudo apt install wmctrl or sudo apt install xdotool"
            )
        except subprocess.TimeoutExpired:
            pass

        return []

    def _filter_windows(
        self, windows: List[Tuple[str, str]], pattern: str
    ) -> List[Tuple[str, str]]:
        """
        Filter windows by name pattern.

        Args:
            windows: List of (window_id, window_title) tuples.
            pattern: Glob pattern to match against window titles.

        Returns:
            Filtered list of windows.
        """
        pattern_lower = pattern.lower()

        return [
            (wid, title)
            for wid, title in windows
            if fnmatch.fnmatch(title.lower(), f"*{pattern_lower}*")
        ]

    def _print_windows(self, windows: List[Tuple[str, str]]) -> None:
        """
        Print windows in a formatted table.

        Args:
            windows: List of (window_id, window_title) tuples.
        """
        print(f"Found {len(windows)} window(s):\n")

        # Calculate column widths
        id_width = max(len(wid) for wid, _ in windows)
        id_width = max(id_width, 2)  # Minimum width for "ID" header

        # Print header
        print(f"{'ID':<{id_width}}  Title")
        print(f"{'-' * id_width}  {'-' * 50}")

        # Print windows
        for window_id, title in windows:
            # Truncate long titles
            display_title = title if len(title) <= 60 else title[:57] + "..."
            print(f"{window_id:<{id_width}}  {display_title}")
