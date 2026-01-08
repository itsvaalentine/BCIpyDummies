"""
CLI entry point for BCIpyDummies.

Provides the main argument parser and dispatches to command handlers.
"""

import argparse
import signal
import sys
from typing import Optional, List

from .commands import RunCommand, ListWindowsCommand, ListHeadsetsCommand


class CLI:
    """Main CLI application class."""

    def __init__(self):
        self._shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Configure graceful shutdown on SIGINT."""
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._handle_sigint)

    def _handle_sigint(self, signum: int, frame) -> None:
        """Handle interrupt signal for graceful shutdown."""
        if self._shutdown_requested:
            # Second interrupt - force exit
            print("\nForce quitting...", file=sys.stderr)
            sys.exit(130)

        self._shutdown_requested = True
        print("\nShutting down gracefully (press Ctrl+C again to force)...", file=sys.stderr)

    @property
    def shutdown_requested(self) -> bool:
        """Check if shutdown was requested."""
        return self._shutdown_requested

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="bci",
            description="BCIpyDummies - BCI middleware for Emotiv headsets",
            epilog="Use 'bci <command> --help' for more information about a command.",
        )

        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )

        subparsers = parser.add_subparsers(
            title="commands",
            dest="command",
            metavar="<command>",
        )

        # Register all commands
        self._register_run_command(subparsers)
        self._register_list_windows_command(subparsers)
        self._register_list_headsets_command(subparsers)

        return parser

    def _register_run_command(self, subparsers) -> None:
        """Register the 'run' command."""
        run_parser = subparsers.add_parser(
            "run",
            help="Start the BCI pipeline",
            description="Start the BCI pipeline with the specified configuration.",
        )

        run_parser.add_argument(
            "--source",
            choices=["emotiv", "mock", "file"],
            default="emotiv",
            help="Data source type (default: emotiv)",
        )

        run_parser.add_argument(
            "--window",
            metavar="NAME",
            help="Target window name for keyboard output",
        )

        run_parser.add_argument(
            "--config",
            metavar="PATH",
            help="Path to configuration file",
        )

        run_parser.add_argument(
            "--map",
            action="append",
            metavar="COMMAND:KEY",
            dest="mappings",
            help="Command mapping (e.g., 'left:A'). Can be specified multiple times.",
        )

        run_parser.add_argument(
            "--threshold",
            action="append",
            metavar="COMMAND:VALUE",
            dest="thresholds",
            help="Power threshold (e.g., 'left:0.8'). Can be specified multiple times.",
        )

        run_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable debug output",
        )

        run_parser.set_defaults(handler=RunCommand)

    def _register_list_windows_command(self, subparsers) -> None:
        """Register the 'list-windows' command."""
        list_windows_parser = subparsers.add_parser(
            "list-windows",
            help="List available windows",
            description="List all available windows that can be targeted for keyboard output.",
        )

        list_windows_parser.add_argument(
            "--filter",
            metavar="PATTERN",
            help="Filter windows by name pattern",
        )

        list_windows_parser.set_defaults(handler=ListWindowsCommand)

    def _register_list_headsets_command(self, subparsers) -> None:
        """Register the 'list-headsets' command."""
        list_headsets_parser = subparsers.add_parser(
            "list-headsets",
            help="List available Emotiv headsets",
            description="List all available Emotiv headsets that can be used as data sources.",
        )

        list_headsets_parser.set_defaults(handler=ListHeadsetsCommand)

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI application.

        Args:
            args: Command-line arguments. If None, uses sys.argv.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.command is None:
            parser.print_help()
            return 0

        # Instantiate and execute the command handler
        handler_class = parsed_args.handler
        handler = handler_class(self)

        try:
            return handler.execute(parsed_args)
        except KeyboardInterrupt:
            print("\nOperation cancelled.", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if hasattr(parsed_args, "verbose") and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code.
    """
    cli = CLI()
    exit_code = cli.run(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
