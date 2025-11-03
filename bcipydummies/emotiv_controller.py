import websocket
import json
import threading
import time
import win32gui
import win32con

# ============================================
#  🧱 CÓDIGO BASE - EMOTIV EEG CONTROL MODULE
# ============================================

VK_CODES = {
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'W': 0x57,
    'SPACE': 0x20
}

class EmotivController:
    """
    Controlador principal que conecta con el Emotiv Cortex API
    y envía comandos mentales a una ventana de Windows.
    """

    def __init__(self, window_name: str):
        self.window_name = window_name
        self.hwnd = self._find_window(window_name)
        self.ws_app = None
        self.lastMove = 'D'
        self.cortex_token = None
        self.session_id = None
        self.headset_id = None

        if not self.hwnd:
            raise RuntimeError(f"❌ No se encontró la ventana: '{window_name}'")
        else:
            print(f"✅ Ventana encontrada: '{window_name}' (HWND={self.hwnd})")
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.2)

    # -----------------------------
    # 🧩 Funciones auxiliares
    # -----------------------------

    @staticmethod
    def list_windows():
        """Devuelve una lista con los títulos de todas las ventanas visibles."""
        ventanas = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                titulo = win32gui.GetWindowText(hwnd)
                if titulo:
                    ventanas.append(titulo)
        win32gui.EnumWindows(callback, None)
        return ventanas

    def _find_window(self, title):
        """Busca la ventana por nombre."""
        return win32gui.FindWindow(None, title)

    def _press_key(self, key: str, hold=0.05):
        """Presiona y suelta una tecla."""
        if key not in VK_CODES:
            print(f"⚠️ Tecla {key} no reconocida.")
            return
        keycode = VK_CODES[key]
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, keycode, 0)
        time.sleep(hold)
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, keycode, 0)

    # -----------------------------
    # 🎮 Control de acciones mentales
    # -----------------------------

    def _control(self, key, hold=0.05):
        """Ejecuta la acción asociada a una tecla."""
        print(f"🎯 Ejecutando control: {key}")
        self._press_key(key, hold)

    def _process_command(self, action, power):
        """Procesa los comandos mentales recibidos del Emotiv."""
        if action == "left" and power >= 0.80:
            print(f"<-- Potencia: {power * 100:.1f}%")
            self._control('A')
            self.lastMove = 'A'
        elif action == "right" and power >= 0.00:
            print(f"--> Potencia: {power * 100:.1f}%")
            self._control('D', 0.2)
            self.lastMove = 'D'
        elif action == "lift" and power >= 0.00:
            print(f"^ Potencia: {power * 100:.1f}%")
            self._control('SPACE', 0.45)
            self._control(self.lastMove, 0.02)

    # -----------------------------
    # 🔌 WebSocket con Emotiv Cortex
    # -----------------------------

    def _on_message(self, ws, message):
        data = json.loads(message)
        if data.get("id") == 1 and "result" in data:
            self.cortex_token = data["result"]["cortexToken"]
            print("🔑 Token obtenido:", self.cortex_token)
            ws.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "queryHeadsets",
                "params": {},
                "id": 2
            }))
        elif data.get("id") == 2 and "result" in data:
            if data["result"]:
                self.headset_id = data["result"][0]["id"]
                print("🎧 Headset:", self.headset_id)
                ws.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "createSession",
                    "params": {
                        "cortexToken": self.cortex_token,
                        "headset": self.headset_id,
                        "status": "active"
                    },
                    "id": 3
                }))
            else:
                print("⚠️ No se encontró ningún headset.")
        elif data.get("id") == 3 and "result" in data:
            self.session_id = data["result"]["id"]
            print("🆔 Sesión creada:", self.session_id)
            ws.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "subscribe",
                "params": {
                    "cortexToken": self.cortex_token,
                    "session": self.session_id,
                    "streams": ["com"]
                },
                "id": 4
            }))
        elif data.get("id") == 4 and "result" in data:
            print("✅ Suscripción completada.")
        if "com" in data:
            action, power = data["com"]
            self._process_command(action, power)

    def _on_error(self, ws, error):
        print("❌ Error:", error)

    def _on_close(self, ws, code, msg):
        print("🔌 Conexión cerrada.")

    def _on_open(self, ws):
        print("🔐 Autenticando con Emotiv Cortex...")
        ws.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "authorize",
            "params": {
                "clientId": "TU_CLIENT_ID",
                "clientSecret": "TU_CLIENT_SECRET",
                "debit": 0
            },
            "id": 1
        }))

    # -----------------------------
    # 🧠 Métodos públicos
    # -----------------------------

    def connect(self):
        """Inicia el hilo de conexión WebSocket."""
        ws_url = "wss://127.0.0.1:6868"
        self.ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        thread = threading.Thread(target=self.ws_app.run_forever)
        thread.start()
        print("🧠 Conectando a Emotiv Cortex...")
        return thread

    def close(self):
        """Cierra la conexión WebSocket."""
        if self.ws_app:
            print("🧩 Cerrando conexión...")
            self.ws_app.close()
