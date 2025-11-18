from unittest.mock import patch, MagicMock
from bcipydummies.core.emotiv_controller import EmotivController


@patch("win32gui.FindWindow", return_value=5678)
@patch("win32gui.SetForegroundWindow", return_value=None)
def test_emotivcontroller_init(mock_set, mock_find):
    ctrl = EmotivController("Mario")
    assert ctrl.hwnd == 5678


@patch("win32gui.FindWindow", return_value=5678)
@patch("win32gui.SetForegroundWindow", return_value=None)
def test_emotivcontroller_process_command(mock_set, mock_find):
    ctrl = EmotivController("Mario")

    calls = []

    def fake_press(key, hold=0.05):
        calls.append(key)

    ctrl.window.press = fake_press

    ctrl._on_com("left", 0.9)
    ctrl._on_com("right", 0.5)
    ctrl._on_com("lift", 0.7)

    assert "A" in calls
    assert "D" in calls
    assert "SPACE" in calls
