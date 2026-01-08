"""
Base command class for CLI commands.

Provides common interface and utilities for all commands.
"""

from abc import ABC, abstractmethod
import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import CLI


class BaseCommand(ABC):
    """
    Abstract base class for CLI commands.

    All commands should inherit from this class and implement the execute method.
    """

    def __init__(self, cli: "CLI"):
        """
        Initialize the command.

        Args:
            cli: The parent CLI instance.
        """
        self._cli = cli

    @property
    def cli(self) -> "CLI":
        """Get the parent CLI instance."""
        return self._cli

    @property
    def shutdown_requested(self) -> bool:
        """Check if shutdown was requested."""
        return self._cli.shutdown_requested

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        pass

    def log(self, message: str, verbose_only: bool = False) -> None:
        """
        Log a message to stdout.

        Args:
            message: The message to log.
            verbose_only: If True, only log when verbose mode is enabled.
        """
        if verbose_only:
            # Check if verbose flag exists and is set
            # This is handled by individual commands
            return
        print(message)

    def error(self, message: str) -> None:
        """
        Log an error message to stderr.

        Args:
            message: The error message.
        """
        import sys
        print(f"Error: {message}", file=sys.stderr)
