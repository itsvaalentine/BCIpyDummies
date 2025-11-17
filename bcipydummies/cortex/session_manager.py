from .websocket_client import WebSocketClient
import time


class SessionManager:
    """
    Maneja:
    - authorize
    - queryHeadsets
    - createSession
    - subscribe
    """

    def __init__(self, client_id, client_secret, url="wss://127.0.0.1:6868"):
        self.client = WebSocketClient(url)
        self.client.on_message = self._on_message

        self.client_id = client_id
        self.client_secret = client_secret

        self.token = None
        self.headset_id = None
        self.session_id = None

        self._pending = {}

    # ------ RECEPCIÓN ----------------------

    def _on_message(self, data):
        if "id" in data:
            self._pending[data["id"]] = data

    def _wait(self, id):
        timeout = time.time() + 5
        while id not in self._pending and time.time() < timeout:
            time.sleep(0.1)
        return self._pending.pop(id, None)

    # ------ COMANDOS CORTEX ---------------

    def connect(self):
        self.client.connect()

    def authorize(self):
        self.client.send_request("authorize", {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "debit": 0
        }, id=1)

        resp = self._wait(1)
        self.token = resp["result"]["cortexToken"]
        return self.token

    def query_headsets(self):
        self.client.send_request("queryHeadsets", {}, id=2)
        resp = self._wait(2)
        self.headset_id = resp["result"][0]["id"]
        return self.headset_id

    def create_session(self):
        self.client.send_request("createSession", {
            "cortexToken": self.token,
            "headset": self.headset_id,
            "status": "active"
        }, id=3)

        resp = self._wait(3)
        self.session_id = resp["result"]["id"]
        return self.session_id

    def subscribe_com(self):
        self.client.send_request("subscribe", {
            "cortexToken": self.token,
            "session": self.session_id,
            "streams": ["com"]
        }, id=4)

        return self._wait(4)
