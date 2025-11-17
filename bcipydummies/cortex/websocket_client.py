import json
import threading
import time
import websocket


class WebSocketClient:
    """
    Cliente genérico para comunicarse con el Emotiv Cortex API.
    Permite conectar, enviar solicitudes JSON-RPC y escuchar mensajes.
    """

    def __init__(self, url="wss://127.0.0.1:6868"):
        self.url = url
        self.ws_app = None
        self.thread = None
        self.connected = False
        self.on_message = None
        self.on_error = None
        self.on_close = None

    # ------------------------------------------------------------------
    # 🧠 Callbacks base
    # ------------------------------------------------------------------

    def _on_open(self, ws):
        """Callback al establecer conexión."""
        self.connected = True
        print(f"✅ Conectado al servidor WebSocket: {self.url}")

    def _on_message(self, ws, message):
        """Callback al recibir un mensaje del servidor."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print(f"⚠️ Mensaje no válido: {message}")
            return

        if self.on_message:
            self.on_message(data)
        else:
            print("📩 Mensaje recibido:", data)

    def _on_error(self, ws, error):
        """Callback al ocurrir un error en la conexión."""
        if self.on_error:
            self.on_error(error)
        else:
            print(f"❌ Error WebSocket: {error}")

    def _on_close(self, ws, code, msg):
        """Callback al cerrar la conexión."""
        self.connected = False
        if self.on_close:
            self.on_close(code, msg)
        else:
            print(f"🔌 Conexión cerrada (code={code}, msg={msg})")

    # ------------------------------------------------------------------
    # 🔌 Métodos públicos
    # ------------------------------------------------------------------

    def connect(self):
        """
        Inicia la conexión con el servidor WebSocket.
        Ejecuta el cliente en un hilo separado.
        """
        self.ws_app = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self.thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
        self.thread.start()

        # Esperar a que conecte
        timeout = time.time() + 5
        while not self.connected and time.time() < timeout:
            time.sleep(0.2)

        if not self.connected:
            raise ConnectionError(f"❌ No se pudo conectar a {self.url}")

        return self.thread

    def send_request(self, method, params=None, id=1):
        """
        Envía una solicitud JSON-RPC al servidor.
        """
        if not self.connected:
            raise RuntimeError("⚠️ No hay conexión WebSocket activa.")

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": id
        }
        self.ws_app.send(json.dumps(message))
        print(f"📤 Enviado → {method}: {params}")

    def close(self):
        """Cierra la conexión WebSocket."""
        if self.ws_app:
            print("🧩 Cerrando conexión WebSocket...")
            self.ws_app.close()
            self.connected = False
