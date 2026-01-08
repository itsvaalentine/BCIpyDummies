"""Exception hierarchy for BCI middleware.

This module defines a structured exception hierarchy for handling
errors that occur during BCI operations. All exceptions inherit from
BCIError, enabling catch-all handlers while preserving specific
error information.
"""

from typing import Optional


class BCIError(Exception):
    """Base exception for all BCI-related errors.

    All exceptions in the bcipydummies library inherit from this class,
    making it easy to catch any BCI-related error with a single handler.

    Attributes:
        message: Human-readable error description.
        source_id: Optional identifier of the source that raised the error.
    """

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None
    ) -> None:
        self.message = message
        self.source_id = source_id
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with optional source context."""
        if self.source_id:
            return f"[{self.source_id}] {self.message}"
        return self.message


class ConnectionError(BCIError):
    """Error raised when connection to an EEG device fails.

    This exception is raised when the middleware cannot establish
    or maintain a connection to the EEG hardware or its control software.

    Attributes:
        message: Description of the connection failure.
        source_id: Identifier of the source that failed to connect.
        cause: Optional underlying exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ) -> None:
        self.cause = cause
        super().__init__(message, source_id)

    def _format_message(self) -> str:
        """Format message including cause information."""
        base_msg = super()._format_message()
        if self.cause:
            return f"{base_msg} (caused by: {type(self.cause).__name__}: {self.cause})"
        return base_msg


class DeviceNotFoundError(ConnectionError):
    """Error raised when no EEG device is detected.

    This exception is raised when the middleware attempts to connect
    to an EEG device but none is found or available.

    Attributes:
        message: Description of the error.
        source_id: Identifier of the source.
        device_type: Optional type/model of device being searched for.
    """

    def __init__(
        self,
        message: str = "No EEG device found",
        source_id: Optional[str] = None,
        device_type: Optional[str] = None
    ) -> None:
        self.device_type = device_type
        if device_type and "device" not in message.lower():
            message = f"{device_type} device not found: {message}"
        super().__init__(message, source_id)


class AuthenticationError(BCIError):
    """Error raised when authentication with the device API fails.

    This exception is raised when credentials are invalid or missing
    for APIs that require authentication (e.g., Emotiv Cortex API).

    Attributes:
        message: Description of the authentication failure.
        source_id: Identifier of the source.
    """

    pass


class SessionError(BCIError):
    """Error raised when session management fails.

    This exception is raised for errors related to creating, managing,
    or destroying sessions with the EEG device or its API.

    Attributes:
        message: Description of the session error.
        source_id: Identifier of the source.
        session_id: Optional identifier of the affected session.
    """

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        self.session_id = session_id
        super().__init__(message, source_id)

    def _format_message(self) -> str:
        """Format message including session information."""
        base_msg = super()._format_message()
        if self.session_id:
            return f"{base_msg} (session: {self.session_id})"
        return base_msg


class SubscriptionError(BCIError):
    """Error raised when subscribing to data streams fails.

    This exception is raised when the middleware cannot subscribe
    to the requested data streams from the EEG device.

    Attributes:
        message: Description of the subscription error.
        source_id: Identifier of the source.
        streams: Optional list of streams that failed to subscribe.
    """

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        streams: Optional[list[str]] = None
    ) -> None:
        self.streams = streams or []
        super().__init__(message, source_id)


class ConfigurationError(BCIError):
    """Error raised when configuration is invalid or missing.

    This exception is raised when required configuration parameters
    are missing or have invalid values.

    Attributes:
        message: Description of the configuration error.
        source_id: Identifier of the source.
        parameter: Optional name of the invalid parameter.
    """

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        parameter: Optional[str] = None
    ) -> None:
        self.parameter = parameter
        super().__init__(message, source_id)

    def _format_message(self) -> str:
        """Format message including parameter information."""
        base_msg = super()._format_message()
        if self.parameter:
            return f"{base_msg} (parameter: {self.parameter})"
        return base_msg


class WindowNotFoundError(BCIError):
    """Raised when a target application window cannot be found.

    This may occur when:
    - The target application is not running
    - The window title does not match any open windows
    - The window is minimized or hidden (on some platforms)
    """

    pass
