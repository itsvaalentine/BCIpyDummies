from unittest.mock import patch, MagicMock
from bcipydummies.control.window_control import WindowControl


@patch("win32gui.PostMessage")
@patch("win32gui.SetForegroundWindow")
def test_windowcontroller_key_press(mock_foreground, mock_post):
    ctrl = WindowControl(hwnd=1234)
    ctrl.press("A")

    # Se envían dos mensajes: KEYDOWN y KEYUP
    assert mock_post.call_count == 2
