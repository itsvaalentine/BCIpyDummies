import pytest
import json
from unittest.mock import patch, MagicMock

from bcipydummies.emotiv_controller import EmotivController


# ===========================================================
# TESTS UNITARIOS PARA EmotivController
# ===========================================================

def test_list_windows_returns_list(monkeypatch):
    """Debe devolver una lista de nombres de ventanas."""
    fake_windows = ["Mario", "Chrome", "Bloc de notas"]

    def fake_enum(callback, _):
        for i, w in enumerate(fake_windows):
            callback(i, None)

    def fake_get_title(hwnd):
        return fake_windows[hwnd]

    monkeypatch.setattr("bcipydummies.emotiv_controller.win32gui.EnumWindows", fake_enum)
    monkeypatch.setattr("bcipydummies.emotiv_controller.win32gui.GetWindowText", fake_get_title)
    monkeypatch.setattr("bcipydummies.emotiv_controller.win32gui.IsWindowVisible", lambda x: True)

    ventanas = EmotivController.list_windows()
    assert isinstance(ventanas, list)
    assert "Mario" in ventanas


@patch("bcipydummies.emotiv_controller.win32gui.FindWindow", return_value=1234)
@patch("bcipydummies.emotiv_controller.win32gui.SetForegroundWindow", return_value=None)
def test_init_finds_window(mock_set, mock_find):
    """Debe inicializar correctamente si la ventana existe."""
    ctrl = EmotivController("Mario")
    assert ctrl.hwnd == 1234
    assert ctrl.lastMove == 'D'
    assert ctrl.window_name == "Mario"


@patch("bcipydummies.emotiv_controller.win32gui.FindWindow", return_value=0)
def test_init_raises_if_window_not_found(mock_find):
    """Debe lanzar error si no encuentra la ventana."""
    with pytest.raises(RuntimeError):
        EmotivController("VentanaInexistente")


@patch("bcipydummies.emotiv_controller.win32gui.FindWindow", return_value=123)
@patch("bcipydummies.emotiv_controller.win32gui.SetForegroundWindow", return_value=None)
@patch("bcipydummies.emotiv_controller.win32gui.PostMessage", return_value=None)
def test_press_key_and_control(mock_post, mock_set, mock_find):
    """Debe llamar correctamente a PostMessage al presionar teclas."""
    ctrl = EmotivController("Mario")
    ctrl._press_key("A")
    ctrl._press_key("SPACE")
    ctrl._control("A")
    assert mock_post.call_count >= 4  # Keydown + Keyup por tecla


@patch("bcipydummies.emotiv_controller.win32gui.FindWindow", return_value=123)
@patch("bcipydummies.emotiv_controller.win32gui.SetForegroundWindow", return_value=None)
@patch("bcipydummies.emotiv_controller.win32gui.PostMessage", return_value=None)
def test_process_command(mock_post, mock_set, mock_find):
    """Debe ejecutar las acciones correctas segun la potencia."""
    ctrl = EmotivController("Mario")

    calls = []

    def fake_control(key, hold=0.05):
        calls.append((key, hold))

    ctrl._control = fake_control

    # Accion izquierda (debe activarse si >=0.8)
    ctrl._process_command("left", 0.85)
    # Accion derecha (siempre)
    ctrl._process_command("right", 0.4)
    # Accion lift
    ctrl._process_command("lift", 0.9)

    assert any(c[0] == "A" for c in calls)
    assert any(c[0] == "D" for c in calls)
    assert any(c[0] == "SPACE" for c in calls)


@patch("bcipydummies.emotiv_controller.win32gui.FindWindow", return_value=123)
@patch("bcipydummies.emotiv_controller.win32gui.SetForegroundWindow", return_value=None)
@patch("bcipydummies.emotiv_controller.win32gui.PostMessage", return_value=None)
def test_websocket_methods(mock_post, mock_set, mock_find):
    """Debe ejecutar los metodos de WebSocket sin error."""
    ctrl = EmotivController("Mario")

    # Creamos un objeto simulado de websocket
    ws = MagicMock()
    ws.send = MagicMock()

    # Mensaje simulado de autenticacion
    ctrl._on_open(ws)
    ws.send.assert_called_once()

    # Mensaje con token (id=1)
    message_1 = json.dumps({"id": 1, "result": {"cortexToken": "abc123"}})
    ctrl._on_message(ws, message_1)
    assert ctrl.cortex_token == "abc123"

    # Mensaje con headsets (id=2)
    message_2 = json.dumps({"id": 2, "result": [{"id": "HEADSET1"}]})
    ctrl._on_message(ws, message_2)
    assert ctrl.headset_id == "HEADSET1"

    # Mensaje con sesion (id=3)
    message_3 = json.dumps({"id": 3, "result": {"id": "SESSION1"}})
    ctrl._on_message(ws, message_3)
    assert ctrl.session_id == "SESSION1"

    # Suscripcion completada (id=4)
    message_4 = json.dumps({"id": 4, "result": {}})
    ctrl._on_message(ws, message_4)

    # Comando mental (stream com) - this triggers _process_command which calls _control
    message_com = json.dumps({"com": ["right", 0.9]})
    ctrl._on_message(ws, message_com)
