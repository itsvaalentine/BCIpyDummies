"""BCI Pipeline Engine - Central orchestrator for the BCI middleware.

This module provides the BCIPipeline class, which connects EEG sources
to publishers through a chain of processors. It implements the Pipeline
pattern with fan-out capabilities.

Architecture:
    Source -> [Processor Chain] -> [Publishers]

    - One EEG source provides input events
    - Processors transform/filter events in sequence
    - Multiple publishers receive the final output (fan-out)

Thread Safety:
    The pipeline uses locks to ensure thread-safe state management,
    as EEG sources typically emit events from background threads.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, List, Optional

from bcipydummies.core.events import EEGEvent
from bcipydummies.processors.base import Processor
from bcipydummies.publishers.base import Publisher
from bcipydummies.sources.base import EEGSource

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class BCIPipeline:
    """Central orchestrator connecting sources to publishers through processors.

    Implements the Pipeline pattern:
    - One EEG source (input)
    - Chain of processors (transform/filter)
    - Multiple publishers (fan-out output)

    The pipeline manages the lifecycle of all components and ensures
    proper startup/shutdown ordering:
        1. Start: publishers -> subscribe to source -> connect source
        2. Stop: disconnect source -> reset processors -> stop publishers

    Events flow through the pipeline as follows:
        1. Source emits an EEGEvent
        2. Event passes through each processor in order
        3. If any processor returns None, the event is dropped
        4. Surviving events are fanned out to all ready publishers

    Example:
        >>> from bcipydummies.sources.emotiv import EmotivSource
        >>> from bcipydummies.processors import ThresholdProcessor
        >>> from bcipydummies.publishers import ConsolePublisher
        >>>
        >>> source = EmotivSource(config)
        >>> pipeline = BCIPipeline(
        ...     source=source,
        ...     processors=[ThresholdProcessor(thresholds={"left": 0.8})],
        ...     publishers=[ConsolePublisher()],
        ... )
        >>>
        >>> pipeline.start()
        >>> # ... events flow automatically ...
        >>> pipeline.stop()

    Thread Safety:
        All state modifications are protected by a lock. The pipeline
        is safe to use from multiple threads.
    """

    def __init__(
        self,
        source: EEGSource,
        processors: Optional[List[Processor]] = None,
        publishers: Optional[List[Publisher]] = None,
    ) -> None:
        """Initialize the BCI pipeline.

        Args:
            source: The EEG source to receive events from. Must implement
                   the EEGSource protocol.
            processors: Optional list of processors to transform/filter events.
                       Processed in order. If None, events pass through unchanged.
            publishers: Optional list of publishers to receive processed events.
                       All ready publishers receive each event (fan-out).
        """
        self._source = source
        self._processors: List[Processor] = list(processors) if processors else []
        self._publishers: List[Publisher] = list(publishers) if publishers else []

        # Thread-safe state management
        self._lock = threading.RLock()
        self._running = False

        # Statistics for monitoring
        self._events_received = 0
        self._events_processed = 0
        self._events_dropped = 0

        logger.debug(
            "BCIPipeline initialized with source=%s, %d processors, %d publishers",
            source.source_id,
            len(self._processors),
            len(self._publishers),
        )

    @property
    def is_running(self) -> bool:
        """Whether the pipeline is currently active.

        Returns:
            True if start() has been called and stop() has not.
        """
        with self._lock:
            return self._running

    @property
    def source(self) -> EEGSource:
        """The EEG source for this pipeline."""
        return self._source

    @property
    def processors(self) -> List[Processor]:
        """Copy of the processor chain.

        Returns:
            A copy of the processors list (modifications don't affect pipeline).
        """
        with self._lock:
            return list(self._processors)

    @property
    def publishers(self) -> List[Publisher]:
        """Copy of the publishers list.

        Returns:
            A copy of the publishers list (modifications don't affect pipeline).
        """
        with self._lock:
            return list(self._publishers)

    @property
    def statistics(self) -> dict:
        """Pipeline statistics for monitoring.

        Returns:
            Dict with keys: events_received, events_processed, events_dropped
        """
        with self._lock:
            return {
                "events_received": self._events_received,
                "events_processed": self._events_processed,
                "events_dropped": self._events_dropped,
            }

    def start(self) -> None:
        """Start all publishers, subscribe to source, and connect source.

        The startup sequence ensures dependencies are ready before
        events begin flowing:
            1. Start all publishers (prepare for receiving events)
            2. Subscribe our handler to the source
            3. Connect the source (events begin flowing)

        Raises:
            RuntimeError: If the pipeline is already running.
            Exception: If any publisher fails to start or source fails to connect.
        """
        with self._lock:
            if self._running:
                logger.warning("Pipeline already running, ignoring start() call")
                return

            logger.info("Starting BCI pipeline...")

            # Phase 1: Start publishers
            started_publishers: List[Publisher] = []
            try:
                for publisher in self._publishers:
                    logger.debug("Starting publisher: %s", type(publisher).__name__)
                    publisher.start()
                    started_publishers.append(publisher)
            except Exception as e:
                # Rollback: stop any publishers we already started
                logger.error("Failed to start publisher: %s", e)
                for pub in started_publishers:
                    try:
                        pub.stop()
                    except Exception as stop_error:
                        logger.warning("Error stopping publisher during rollback: %s", stop_error)
                raise

            # Phase 2: Subscribe to source events
            logger.debug("Subscribing to source events")
            self._source.subscribe(self._on_event)

            # Phase 3: Connect the source
            try:
                logger.debug("Connecting to source: %s", self._source.source_id)
                self._source.connect()
            except Exception as e:
                # Rollback: unsubscribe and stop publishers
                logger.error("Failed to connect source: %s", e)
                self._source.unsubscribe(self._on_event)
                for pub in self._publishers:
                    try:
                        pub.stop()
                    except Exception as stop_error:
                        logger.warning("Error stopping publisher during rollback: %s", stop_error)
                raise

            # Reset statistics
            self._events_received = 0
            self._events_processed = 0
            self._events_dropped = 0

            self._running = True
            logger.info("BCI pipeline started successfully")

    def stop(self) -> None:
        """Stop gracefully: disconnect source, reset processors, stop publishers.

        The shutdown sequence ensures clean resource release:
            1. Disconnect the source (stop new events)
            2. Unsubscribe from source events
            3. Reset all processors (clear any accumulated state)
            4. Stop all publishers (release resources)

        This method is idempotent - calling it when not running is safe.
        Errors during shutdown are logged but don't prevent other
        components from being stopped.
        """
        with self._lock:
            if not self._running:
                logger.debug("Pipeline not running, ignoring stop() call")
                return

            logger.info("Stopping BCI pipeline...")

            # Phase 1: Disconnect source
            try:
                logger.debug("Disconnecting source: %s", self._source.source_id)
                self._source.disconnect()
            except Exception as e:
                logger.warning("Error disconnecting source: %s", e)

            # Phase 2: Unsubscribe from events
            try:
                self._source.unsubscribe(self._on_event)
            except Exception as e:
                logger.warning("Error unsubscribing from source: %s", e)

            # Phase 3: Reset processors
            for processor in self._processors:
                try:
                    logger.debug("Resetting processor: %s", type(processor).__name__)
                    processor.reset()
                except Exception as e:
                    logger.warning("Error resetting processor %s: %s",
                                 type(processor).__name__, e)

            # Phase 4: Stop publishers
            for publisher in self._publishers:
                try:
                    logger.debug("Stopping publisher: %s", type(publisher).__name__)
                    publisher.stop()
                except Exception as e:
                    logger.warning("Error stopping publisher %s: %s",
                                 type(publisher).__name__, e)

            self._running = False
            logger.info(
                "BCI pipeline stopped. Stats: received=%d, processed=%d, dropped=%d",
                self._events_received,
                self._events_processed,
                self._events_dropped,
            )

    def _on_event(self, event: EEGEvent) -> None:
        """Internal handler: process event through chain and fan out to publishers.

        This method is called by the source for each emitted event.
        It processes the event through all processors and then sends
        the result to all ready publishers.

        Args:
            event: The EEG event from the source.

        Note:
            This method is typically called from a background thread
            owned by the source. The implementation is thread-safe.
        """
        with self._lock:
            if not self._running:
                return

            self._events_received += 1

        # Process through the processor chain
        current_event: Optional[EEGEvent] = event

        for processor in self._processors:
            if current_event is None:
                break

            try:
                current_event = processor.process(current_event)
            except Exception as e:
                logger.error(
                    "Processor %s raised exception: %s",
                    type(processor).__name__,
                    e,
                    exc_info=True,
                )
                # Drop the event on processor error
                current_event = None
                break

        # Update statistics
        with self._lock:
            if current_event is None:
                self._events_dropped += 1
                return

            self._events_processed += 1

        # Fan out to all ready publishers
        for publisher in self._publishers:
            if not publisher.is_ready:
                logger.debug(
                    "Skipping publisher %s (not ready)",
                    type(publisher).__name__,
                )
                continue

            try:
                publisher.publish(current_event)
            except Exception as e:
                logger.error(
                    "Publisher %s raised exception: %s",
                    type(publisher).__name__,
                    e,
                    exc_info=True,
                )

    def add_processor(self, processor: Processor) -> None:
        """Add a processor to the end of the chain.

        The processor will receive events after all existing processors.
        Can be called while the pipeline is running - new events will
        flow through the updated chain.

        Args:
            processor: The processor to add.
        """
        with self._lock:
            self._processors.append(processor)
            logger.debug("Added processor: %s", type(processor).__name__)

    def add_publisher(self, publisher: Publisher) -> None:
        """Add a publisher to receive events.

        If the pipeline is running, the publisher is started immediately.
        Otherwise it will be started when the pipeline starts.

        Args:
            publisher: The publisher to add.

        Raises:
            RuntimeError: If starting the publisher fails while pipeline is running.
        """
        with self._lock:
            if self._running:
                # Start the publisher immediately if we're running
                try:
                    publisher.start()
                except Exception as e:
                    logger.error("Failed to start new publisher: %s", e)
                    raise RuntimeError(f"Failed to start publisher: {e}") from e

            self._publishers.append(publisher)
            logger.debug("Added publisher: %s", type(publisher).__name__)

    def remove_processor(self, processor: Processor) -> bool:
        """Remove a processor from the chain.

        Args:
            processor: The processor to remove.

        Returns:
            True if the processor was found and removed, False otherwise.
        """
        with self._lock:
            try:
                self._processors.remove(processor)
                logger.debug("Removed processor: %s", type(processor).__name__)
                return True
            except ValueError:
                return False

    def remove_publisher(self, publisher: Publisher) -> bool:
        """Remove a publisher from the pipeline.

        If the pipeline is running, the publisher is stopped before removal.

        Args:
            publisher: The publisher to remove.

        Returns:
            True if the publisher was found and removed, False otherwise.
        """
        with self._lock:
            try:
                self._publishers.remove(publisher)
                if self._running:
                    try:
                        publisher.stop()
                    except Exception as e:
                        logger.warning("Error stopping removed publisher: %s", e)
                logger.debug("Removed publisher: %s", type(publisher).__name__)
                return True
            except ValueError:
                return False

    def __enter__(self) -> BCIPipeline:
        """Context manager entry - starts the pipeline."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the pipeline."""
        self.stop()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"BCIPipeline("
            f"source={self._source.source_id!r}, "
            f"processors={len(self._processors)}, "
            f"publishers={len(self._publishers)}, "
            f"running={self._running})"
        )
