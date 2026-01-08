"""
Run command implementation.

Starts the BCI pipeline with the specified configuration.
"""

import argparse
import sys
import time
from typing import Dict, List, Optional, Tuple

from .base import BaseCommand


class RunCommand(BaseCommand):
    """Command to start the BCI pipeline."""

    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the run command.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code.
        """
        verbose = args.verbose

        if verbose:
            print("Starting BCI pipeline...")
            print(f"  Source: {args.source}")
            if args.window:
                print(f"  Target window: {args.window}")
            if args.config:
                print(f"  Config file: {args.config}")

        # Parse and validate configuration
        try:
            config = self._build_config(args)
        except ValueError as e:
            self.error(str(e))
            return 1

        if verbose:
            self._print_config(config)

        # Initialize and run the pipeline
        return self._run_pipeline(config, verbose)

    def _build_config(self, args: argparse.Namespace) -> Dict:
        """
        Build configuration dictionary from command-line arguments.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Configuration dictionary.

        Raises:
            ValueError: If configuration is invalid.
        """
        config = {
            "source": {
                "type": args.source,
            },
            "processors": {
                "thresholds": {},
                "mappings": {},
            },
            "publishers": [],
        }

        # Load config file if specified
        if args.config:
            file_config = self._load_config_file(args.config)
            config = self._merge_configs(config, file_config)

        # Parse command mappings
        if args.mappings:
            mappings = self._parse_key_value_pairs(args.mappings, "mapping")
            config["processors"]["mappings"].update(mappings)

        # Parse thresholds
        if args.thresholds:
            thresholds = self._parse_thresholds(args.thresholds)
            config["processors"]["thresholds"].update(thresholds)

        # Configure publishers based on window argument
        if args.window:
            config["publishers"].append({
                "type": "keyboard",
                "window": args.window,
            })
        else:
            # Default to console publisher if no window specified
            config["publishers"].append({
                "type": "console",
            })

        return config

    def _load_config_file(self, path: str) -> Dict:
        """
        Load configuration from a file.

        Args:
            path: Path to the configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            ValueError: If file cannot be loaded or parsed.
        """
        import json
        from pathlib import Path

        config_path = Path(path)

        if not config_path.exists():
            raise ValueError(f"Configuration file not found: {path}")

        try:
            with open(config_path, "r") as f:
                if config_path.suffix in (".yaml", ".yml"):
                    try:
                        import yaml
                        return yaml.safe_load(f)
                    except ImportError:
                        raise ValueError(
                            "PyYAML is required to load YAML config files. "
                            "Install it with: pip install pyyaml"
                        )
                else:
                    return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration file: {e}")

    def _merge_configs(self, base: Dict, overlay: Dict) -> Dict:
        """
        Recursively merge two configuration dictionaries.

        Args:
            base: Base configuration.
            overlay: Configuration to overlay on base.

        Returns:
            Merged configuration.
        """
        result = base.copy()

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _parse_key_value_pairs(
        self, pairs: List[str], name: str
    ) -> Dict[str, str]:
        """
        Parse key:value pairs from command line.

        Args:
            pairs: List of "key:value" strings.
            name: Name of the parameter for error messages.

        Returns:
            Dictionary of parsed pairs.

        Raises:
            ValueError: If a pair is malformed.
        """
        result = {}

        for pair in pairs:
            key, value = self._split_pair(pair, name)
            result[key] = value

        return result

    def _parse_thresholds(self, pairs: List[str]) -> Dict[str, float]:
        """
        Parse threshold pairs from command line.

        Args:
            pairs: List of "command:value" strings.

        Returns:
            Dictionary of command to threshold value.

        Raises:
            ValueError: If a pair is malformed or value is not a valid float.
        """
        result = {}

        for pair in pairs:
            key, value_str = self._split_pair(pair, "threshold")

            try:
                value = float(value_str)
            except ValueError:
                raise ValueError(
                    f"Invalid threshold value '{value_str}' for '{key}'. "
                    "Must be a number."
                )

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Threshold value {value} for '{key}' must be between 0.0 and 1.0."
                )

            result[key] = value

        return result

    def _split_pair(self, pair: str, name: str) -> Tuple[str, str]:
        """
        Split a key:value pair string.

        Args:
            pair: String in "key:value" format.
            name: Name of the parameter for error messages.

        Returns:
            Tuple of (key, value).

        Raises:
            ValueError: If the pair is malformed.
        """
        if ":" not in pair:
            raise ValueError(
                f"Invalid {name} format '{pair}'. Expected 'key:value'."
            )

        parts = pair.split(":", 1)
        key = parts[0].strip()
        value = parts[1].strip()

        if not key:
            raise ValueError(f"Empty key in {name}: '{pair}'")
        if not value:
            raise ValueError(f"Empty value in {name}: '{pair}'")

        return key, value

    def _print_config(self, config: Dict) -> None:
        """Print configuration summary."""
        print("\nConfiguration:")
        print(f"  Source type: {config['source']['type']}")

        thresholds = config["processors"]["thresholds"]
        if thresholds:
            print("  Thresholds:")
            for cmd, value in thresholds.items():
                print(f"    {cmd}: {value}")

        mappings = config["processors"]["mappings"]
        if mappings:
            print("  Mappings:")
            for cmd, key in mappings.items():
                print(f"    {cmd} -> {key}")

        print("  Publishers:")
        for pub in config["publishers"]:
            pub_type = pub.get("type", "unknown")
            if pub_type == "keyboard":
                print(f"    Keyboard (window: {pub.get('window', 'N/A')})")
            else:
                print(f"    {pub_type.capitalize()}")

        print()

    def _run_pipeline(self, config: Dict, verbose: bool) -> int:
        """
        Initialize and run the BCI pipeline.

        Args:
            config: Pipeline configuration.
            verbose: Whether to enable verbose output.

        Returns:
            Exit code.
        """
        try:
            # Attempt to import and initialize pipeline components
            pipeline = self._create_pipeline(config, verbose)
        except ImportError as e:
            self.error(f"Failed to import pipeline components: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return 1
        except Exception as e:
            self.error(f"Failed to initialize pipeline: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return 1

        # Run the pipeline
        print("Pipeline running. Press Ctrl+C to stop.")

        try:
            if pipeline is not None:
                pipeline.start()

                # Main loop - check for shutdown
                while not self.shutdown_requested:
                    time.sleep(0.1)

                pipeline.stop()
            else:
                # Placeholder behavior when pipeline is not yet implemented
                print("[Placeholder] Pipeline components not yet implemented.")
                print("[Placeholder] Would run with configuration:")
                print(f"  Source: {config['source']['type']}")
                while not self.shutdown_requested:
                    time.sleep(0.1)

        except Exception as e:
            self.error(f"Pipeline error: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return 1

        print("Pipeline stopped.")
        return 0

    def _create_pipeline(self, config: Dict, verbose: bool) -> Optional[object]:
        """
        Create the BCI pipeline from configuration.

        Args:
            config: Pipeline configuration.
            verbose: Whether to enable verbose output.

        Returns:
            Configured BCIPipeline instance, or None if components not available.
        """
        try:
            from ...core.engine import BCIPipeline
        except ImportError:
            # BCIPipeline not yet implemented
            return None

        # Build the pipeline from CLI config dictionary
        try:
            pipeline = BCIPipeline.from_cli_config(config, verbose=verbose)
        except AttributeError:
            # from_cli_config not yet implemented, try direct instantiation
            try:
                pipeline = BCIPipeline(config, verbose=verbose)
            except TypeError:
                # Pipeline constructor signature doesn't match
                return None

        return pipeline
