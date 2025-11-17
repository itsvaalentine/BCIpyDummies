from cortex.session_manager import SessionManager
from control.window_control import WindowControl
from control.action_mapper import ActionMapper


class EmotivController:

    def __init__(self, window, client_id, client_secret):
        self.window = WindowControl(window)
        self.session = SessionManager(client_id, client_secret)
        self.mapper = ActionMapper()

    def start(self):
        self.session.connect()
        self.session.authorize()
        self.session.query_headsets()
        self.session.create_session()

        # Suscribirse al stream COM
        self.session.subscribe_com()

        # Ahora queremos recibir comandos mentales
        self.session.client.on_message = self._on_com

    def _on_com(self, data):
        if "com" not in data:
            return
        action, power = data["com"]
        key = self.mapper.map(action, power)
        if key:
            self.window.press(key)
