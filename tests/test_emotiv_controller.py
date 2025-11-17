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

    ctrl._process_action("left", 0.9)
    ctrl._process_action("right", 0.5)
    ctrl._process_action("lift", 0.7)

    assert "A" in calls
    assert "D" in calls
    assert "SPACE" in calls
