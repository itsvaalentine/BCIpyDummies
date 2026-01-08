"""WebSocket client for the Emotiv Cortex API.

This module provides a low-level client for communicating with the Emotiv
Cortex API via WebSocket. It handles the authentication flow, session
management, and data stream subscription.

The Cortex API uses JSON-RPC 2.0 over WebSocket for communication.
See: https://emotiv.gitbook.io/cortex-api/
"""

import json
import logging
import os
import ssl
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional

import websocket

from bcipydummies.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    DeviceNotFoundError,
    SessionError,
    SubscriptionError,
)


logger = logging.getLogger(__name__)


class CortexState(Enum):
    """States for the Cortex API connection flow."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    AUTHENTICATING = auto()
    QUERYING_HEADSETS = auto()
    CREATING_SESSION = auto()
    SUBSCRIBING = auto()
    STREAMING = auto()
    ERROR = auto()


@dataclass
class CortexCredentials:
    """Credentials for Emotiv Cortex API authentication.

    Attributes:
        client_id: Your Cortex API client ID from Emotiv.
        client_secret: Your Cortex API client secret from Emotiv.
        license_id: Optional license ID for advanced features.
    """

    client_id: str
    client_secret: str
    license_id: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "CortexCredentials":
        """Create credentials from environment variables.

        Expected environment variables:
            EMOTIV_CLIENT_ID: The client ID
            EMOTIV_CLIENT_SECRET: The client secret
            EMOTIV_LICENSE_ID: Optional license ID

        Returns:
            CortexCredentials instance with values from environment.

        Raises:
            ConfigurationError: If required environment variables are missing.
        """
        client_id = os.environ.get("EMOTIV_CLIENT_ID")
        client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
        license_id = os.environ.get("EMOTIV_LICENSE_ID")

        if not client_id:
            raise ConfigurationError(
                "EMOTIV_CLIENT_ID environment variable is required",
                parameter="EMOTIV_CLIENT_ID",
            )
        if not client_secret:
            raise ConfigurationError(
                "EMOTIV_CLIENT_SECRET environment variable is required",
                parameter="EMOTIV_CLIENT_SECRET",
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            license_id=license_id,
        )


# Type alias for mental command callback
MentalCommandCallback = Callable[[str, float], None]
ConnectionCallback = Callable[[bool, str], None]
ErrorCallback = Callable[[Exception], None]


class CortexClient:
    """WebSocket client for Emotiv Cortex API.

    This client handles the complete authentication and subscription flow:
    1. Connect to WebSocket
    2. Authorize with credentials
    3. Query available headsets
    4. Create a session with a headset
    5. Subscribe to data streams

    Events are delivered via callbacks registered by the consumer.

    Example usage:
        >>> credentials = CortexCredentials.from_environment()
        >>> client = CortexClient(credentials)
        >>> client.on_mental_command = lambda cmd, power: print(f"{cmd}: {power}")
        >>> client.connect()
        >>> # ... events flow via callback ...
        >>> client.disconnect()
    """

    CORTEX_URL = "wss://localhost:6868"

    # Request IDs for tracking responses
    _ID_AUTHORIZE = 1
    _ID_QUERY_HEADSETS = 2
    _ID_CREATE_SESSION = 3
    _ID_SUBSCRIBE = 4

    def __init__(
        self,
        credentials: CortexCredentials,
        headset_id: Optional[str] = None,
        streams: Optional[list[str]] = None,
    ) -> None:
        """Initialize the Cortex client.

        Args:
            credentials: Authentication credentials for the API.
            headset_id: Optional specific headset ID to connect to.
                       If None, connects to the first available headset.
            streams: List of data streams to subscribe to.
                    Defaults to ["com"] for mental commands.
        """
        self._credentials = credentials
        self._target_headset_id = headset_id
        self._streams = streams or ["com"]

        # Connection state
        self._state = CortexState.DISCONNECTED
        self._ws: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Session state
        self._cortex_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._headset_id: Optional[str] = None

        # Callbacks
        self.on_mental_command: Optional[MentalCommandCallback] = None
        self.on_connection_change: Optional[ConnectionCallback] = None
        self.on_error: Optional[ErrorCallback] = None

    @property
    def state(self) -> CortexState:
        """Current state of the Cortex connection."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected and streaming."""
        return self._state == CortexState.STREAMING

    @property
    def headset_id(self) -> Optional[str]:
        """ID of the connected headset, if any."""
        return self._headset_id

    @property
    def session_id(self) -> Optional[str]:
        """ID of the active session, if any."""
        return self._session_id

    def connect(self) -> None:
        """Connect to the Cortex API and start streaming.

        This method initiates the connection flow. The actual connection
        and authentication happen asynchronously via WebSocket callbacks.

        Raises:
            ConnectionError: If already connected or connection fails.
        """
        with self._lock:
            if self._state != CortexState.DISCONNECTED:
                raise ConnectionError(
                    f"Cannot connect: client is in state {self._state.name}"
                )
            self._state = CortexState.CONNECTING

        logger.info("Connecting to Emotiv Cortex API...")

        # Create WebSocket with SSL (Cortex uses self-signed cert)
        self._ws = websocket.WebSocketApp(
            self.CORTEX_URL,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close,
        )

        # Run WebSocket in background thread
        self._ws_thread = threading.Thread(
            target=self._run_websocket,
            daemon=True,
            name="CortexWebSocket",
        )
        self._ws_thread.start()

    def _run_websocket(self) -> None:
        """Run the WebSocket event loop with SSL configured."""
        if self._ws is None:
            return

        # Cortex uses a self-signed certificate
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self._ws.run_forever(sslopt={"context": ssl_context})

    def disconnect(self) -> None:
        """Disconnect from the Cortex API.

        Safe to call even if not connected.
        """
        with self._lock:
            if self._state == CortexState.DISCONNECTED:
                return
            self._state = CortexState.DISCONNECTED

        logger.info("Disconnecting from Emotiv Cortex API...")

        if self._ws is not None:
            self._ws.close()
            self._ws = None

        # Reset session state
        self._cortex_token = None
        self._session_id = None
        self._headset_id = None

        if self.on_connection_change:
            self.on_connection_change(False, "Disconnected")

    def _send_request(
        self,
        method: str,
        params: Dict[str, Any],
        request_id: int,
    ) -> None:
        """Send a JSON-RPC request to the Cortex API.

        Args:
            method: The API method name.
            params: Parameters for the method.
            request_id: ID to track the response.
        """
        if self._ws is None:
            logger.warning("Cannot send request: WebSocket not connected")
            return

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }

        logger.debug(f"Sending request: {method}")
        self._ws.send(json.dumps(request))

    # -------------------------------------------------------------------------
    # WebSocket Event Handlers
    # -------------------------------------------------------------------------

    def _on_ws_open(self, ws: websocket.WebSocket) -> None:
        """Handle WebSocket connection opened."""
        logger.info("WebSocket connected, starting authentication...")
        self._state = CortexState.AUTHENTICATING
        self._send_authorize()

    def _on_ws_message(self, ws: websocket.WebSocket, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            self._handle_error(ConnectionError(f"Invalid JSON from Cortex: {e}"))
            return

        # Check for error response
        if "error" in data:
            self._handle_api_error(data)
            return

        # Handle response based on request ID
        request_id = data.get("id")
        if request_id is not None:
            self._handle_response(request_id, data)
        elif "com" in data:
            # Mental command stream data
            self._handle_mental_command(data)
        else:
            logger.debug(f"Unhandled message: {data}")

    def _on_ws_error(self, ws: websocket.WebSocket, error: Exception) -> None:
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {error}")
        self._state = CortexState.ERROR
        self._handle_error(ConnectionError(str(error), cause=error))

    def _on_ws_close(
        self,
        ws: websocket.WebSocket,
        close_status_code: Optional[int],
        close_msg: Optional[str],
    ) -> None:
        """Handle WebSocket connection closed."""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")

        with self._lock:
            was_connected = self._state == CortexState.STREAMING
            self._state = CortexState.DISCONNECTED

        if was_connected and self.on_connection_change:
            self.on_connection_change(False, close_msg or "Connection closed")

    # -------------------------------------------------------------------------
    # API Request Methods
    # -------------------------------------------------------------------------

    def _send_authorize(self) -> None:
        """Send the authorize request."""
        params: Dict[str, Any] = {
            "clientId": self._credentials.client_id,
            "clientSecret": self._credentials.client_secret,
        }

        if self._credentials.license_id:
            params["license"] = self._credentials.license_id

        self._send_request("authorize", params, self._ID_AUTHORIZE)

    def _send_query_headsets(self) -> None:
        """Query available headsets."""
        self._state = CortexState.QUERYING_HEADSETS
        self._send_request("queryHeadsets", {}, self._ID_QUERY_HEADSETS)

    def _send_create_session(self, headset_id: str) -> None:
        """Create a session with the specified headset."""
        self._state = CortexState.CREATING_SESSION
        self._send_request(
            "createSession",
            {
                "cortexToken": self._cortex_token,
                "headset": headset_id,
                "status": "active",
            },
            self._ID_CREATE_SESSION,
        )

    def _send_subscribe(self) -> None:
        """Subscribe to data streams."""
        self._state = CortexState.SUBSCRIBING
        self._send_request(
            "subscribe",
            {
                "cortexToken": self._cortex_token,
                "session": self._session_id,
                "streams": self._streams,
            },
            self._ID_SUBSCRIBE,
        )

    # -------------------------------------------------------------------------
    # Response Handlers
    # -------------------------------------------------------------------------

    def _handle_response(self, request_id: int, data: Dict[str, Any]) -> None:
        """Route response to appropriate handler based on request ID."""
        result = data.get("result")

        if request_id == self._ID_AUTHORIZE:
            self._handle_authorize_response(result)
        elif request_id == self._ID_QUERY_HEADSETS:
            self._handle_query_headsets_response(result)
        elif request_id == self._ID_CREATE_SESSION:
            self._handle_create_session_response(result)
        elif request_id == self._ID_SUBSCRIBE:
            self._handle_subscribe_response(result)

    def _handle_authorize_response(self, result: Optional[Dict[str, Any]]) -> None:
        """Handle authorize response."""
        if result is None:
            self._handle_error(AuthenticationError("No result in authorize response"))
            return

        token = result.get("cortexToken")
        if not token:
            self._handle_error(
                AuthenticationError("No cortexToken in authorize response")
            )
            return

        self._cortex_token = token
        logger.info("Authentication successful")
        self._send_query_headsets()

    def _handle_query_headsets_response(
        self, result: Optional[list[Dict[str, Any]]]
    ) -> None:
        """Handle queryHeadsets response."""
        if not result:
            self._handle_error(
                DeviceNotFoundError(
                    "No headsets found. Ensure your Emotiv headset is connected.",
                    device_type="Emotiv",
                )
            )
            return

        # Find target headset or use first available
        headset = None
        if self._target_headset_id:
            for h in result:
                if h.get("id") == self._target_headset_id:
                    headset = h
                    break
            if not headset:
                available = [h.get("id", "unknown") for h in result]
                self._handle_error(
                    DeviceNotFoundError(
                        f"Headset '{self._target_headset_id}' not found. "
                        f"Available: {available}",
                        device_type="Emotiv",
                    )
                )
                return
        else:
            headset = result[0]

        self._headset_id = headset.get("id")
        logger.info(f"Found headset: {self._headset_id}")
        self._send_create_session(self._headset_id)

    def _handle_create_session_response(
        self, result: Optional[Dict[str, Any]]
    ) -> None:
        """Handle createSession response."""
        if result is None:
            self._handle_error(SessionError("No result in createSession response"))
            return

        session_id = result.get("id")
        if not session_id:
            self._handle_error(SessionError("No session ID in createSession response"))
            return

        self._session_id = session_id
        logger.info(f"Session created: {self._session_id}")
        self._send_subscribe()

    def _handle_subscribe_response(self, result: Optional[Dict[str, Any]]) -> None:
        """Handle subscribe response."""
        if result is None:
            self._handle_error(
                SubscriptionError(
                    "No result in subscribe response",
                    streams=self._streams,
                )
            )
            return

        self._state = CortexState.STREAMING
        logger.info(f"Subscribed to streams: {self._streams}")

        if self.on_connection_change:
            self.on_connection_change(True, f"Connected to {self._headset_id}")

    def _handle_mental_command(self, data: Dict[str, Any]) -> None:
        """Handle mental command stream data."""
        com_data = data.get("com")
        if not com_data or not isinstance(com_data, list) or len(com_data) < 2:
            logger.warning(f"Invalid mental command data: {data}")
            return

        action = com_data[0]
        power = com_data[1]

        if not isinstance(action, str) or not isinstance(power, (int, float)):
            logger.warning(f"Invalid mental command types: action={action}, power={power}")
            return

        if self.on_mental_command:
            self.on_mental_command(action, float(power))

    def _handle_api_error(self, data: Dict[str, Any]) -> None:
        """Handle Cortex API error response."""
        error = data.get("error", {})
        code = error.get("code", "unknown")
        message = error.get("message", "Unknown error")

        logger.error(f"Cortex API error [{code}]: {message}")

        # Map error codes to appropriate exceptions
        if code in (-32600, -32601, -32602, -32603):
            # JSON-RPC errors
            exc = ConnectionError(f"API error: {message}")
        elif code in (100, 101, 102):
            # Authentication errors
            exc = AuthenticationError(message)
        elif code in (103, 104):
            # Headset errors
            exc = DeviceNotFoundError(message, device_type="Emotiv")
        elif code in (105, 106):
            # Session errors
            exc = SessionError(message, session_id=self._session_id)
        else:
            exc = ConnectionError(f"Cortex error [{code}]: {message}")

        self._handle_error(exc)

    def _handle_error(self, error: Exception) -> None:
        """Handle errors by updating state and notifying callback."""
        self._state = CortexState.ERROR

        if self.on_error:
            self.on_error(error)
        else:
            logger.error(f"Unhandled error: {error}")
