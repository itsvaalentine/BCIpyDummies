import win32gui
import win32con
import time

VK = {
    "A": 0x41,
    "D": 0x44,
    "W": 0x57,
    "S": 0x53,
    "SPACE": 0x20,
}

class WindowControl:

    def __init__(self, window_name):
        self.window_name = window_name
        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise RuntimeError(f"Ventana no encontrada: {window_name}")

        win32gui.SetForegroundWindow(self.hwnd)
        time.sleep(0.2)

    def press(self, key, hold=0.1):
        if key not in VK:
            return
        code = VK[key]
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, code, 0)
        time.sleep(hold)
        win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, code, 0)
