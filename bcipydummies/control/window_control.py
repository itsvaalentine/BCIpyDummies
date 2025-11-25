import win32gui
import win32con
import win32api  
import time
from pynput import keyboard 

# ============================================================
#   DEFINICIÓN DE TECLADOS
# ============================================================

# --- Teclado Inglés (default Windows) ---
VK_EN = {
    # Letras
    **{chr(c): c for c in range(0x41, 0x5B)},  # A-Z

    # Números
    **{str(n): 0x30 + n for n in range(10)},

    # Teclas especiales
    "SPACE": 0x20,
    "ENTER": 0x0D,
    "ESC": 0x1B,
    "TAB": 0x09,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "ALT": 0x12,

    # Función
    **{f"F{i}": 0x70 + i - 1 for i in range(1, 13)},

    # Símbolos típicos EN
    "/": 0xBF,
    "?": 0xBF,       # shift + /
    "-": 0xBD,
    "=": 0xBB,
    ".": 0xBE,
    ",": 0xBC,
    ";": 0xBA,
    ":": 0xBA,       # shift + ;
    "'": 0xDE,
    '"': 0xDE,       # shift + '
    "[": 0xDB,
    "{": 0xDB,       # shift + [
    "]": 0xDD,
    "}": 0xDD,       # shift + ]
    "\\": 0xDC,
    "|": 0xDC,       # shift + \
}

# --- Teclado Español (MX / ES) ---
# Notas:
# - Las letras son iguales
# - Ñ existe físicamente → VK 0xBA o 0xDC según layout
# - ? y / cambian
# - Símbolos cambian de posición
VK_ES = VK_EN.copy()
VK_ES.update({
    "Ñ": 0xDC,

    # Símbolos diferentes en teclado ES
    "/": 0xBF,
    "?": 0xBF,
    "'": 0xDE,
    "¡": 0xDE,
    "¿": 0xDB,
})

# Diccionario de layouts disponibles
KEYBOARD_LAYOUTS = {
    "EN": VK_EN,
    "ES": VK_ES,
}

# ============================================================
#   CLASE PRINCIPAL
# ============================================================

class WindowControl:
    def __init__(self, window_name, layout="EN"):
        """
        Inicializa el controlador de una ventana específica.

        Parámetros:
        - window_name: Nombre EXACTO de la ventana objetivo.
        - layout: Distribución del teclado ("EN" o "ES").

        Notas:
        - No se intenta forzar foreground.
        - Todo el sistema funciona con RAW MODE (SendMessage), lo que
          permite enviar teclas aunque la ventana esté en segundo plano.
        """
        self.interrupt_key = "ENTER"   # Tecla que activa o desactiva la pausa global
        self.paused = False            # Estado ON/OFF que bloquea el envío de comandos
        self.listener = None  

        self.window_name = window_name

        if layout.upper() not in KEYBOARD_LAYOUTS:
            raise ValueError(f"Layout inválido. Usa: {list(KEYBOARD_LAYOUTS.keys())}")

        # Diccionario de teclas según layout elegido
        self.VK = KEYBOARD_LAYOUTS[layout.upper()]

        # Obtener el handle (HWND) de la ventana objetivo
        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise RuntimeError(f"Ventana no encontrada: {window_name}")

        # No se usa foco: RAW MODE lo hace innecesario
        time.sleep(0.1)

    @staticmethod
    def list_windows():
        """
        Enumera y devuelve todas las ventanas visibles del sistema.

        Returns:
        - Lista de strings con los títulos de las ventanas visibles.
        """
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    windows.append(title)

        win32gui.EnumWindows(callback, None)
        return windows

    # -----------------------------------------------------------

    def trigger_interrupt(self):
        """
        Alterna el estado de pausa global.
        
        Si estaba enviando comandos → se detiene.
        Si estaba pausado → vuelve a enviar comandos.

        Este comportamiento se activa automáticamente al presionar
        la tecla asignada como interruptor (por defecto ENTER).
        """
        self.paused = not self.paused
        print(f"⏸ PAUSA = {self.paused}")

    # -----------------------------------------------------------

    def set_interrupt_key(self, key):
        """
        Define qué tecla actuará como "interruptor global".

        Parámetros:
        - key: Tecla (string) que activará/desactivará la pausa.

        Ejemplo:
            ctrl.set_interrupt_key("SHIFT")

        Notas:
        - Debe existir en el diccionario de teclas del layout activo.
        """
        if key.upper() in self.VK:
            self.interrupt_key = key.upper()
        else:
            raise ValueError(f"Tecla inválida para interruptor: {key}")

    # -----------------------------------------------------------

    def send_raw_key(self, vk):
        """
        Envía una tecla en modo RAW usando SendMessage.

        Este método:
        - Funciona incluso si la ventana está en segundo plano.
        - No cambia el foco.
        - No requiere permisos especiales.

        Parámetros:
        - vk: Código virtual-key de la tecla.
        """
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk, 0)
        time.sleep(0.05)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, vk, 0)

    # -----------------------------------------------------------

    def press(self, key, hold=0.1):
        """
        Envía una tecla SIEMPRE en modo RAW (sin usar foreground).

        Flujo:
        1. Si está pausado → no envía nada.
        2. Si la tecla es el interruptor → activa/desactiva pausa.
        3. Convierte la tecla a VK.
        4. Envía con send_raw_key().

        Parámetros:
        - key: tecla a enviar (string).
        - hold: tiempo entre KEYDOWN y KEYUP.
        """
        # ====== PAUSA GLOBAL ======
        if self.paused:
            print(f"⏸ Comando bloqueado (pausado): {key}")
            return

        # ====== INTERRRUPTOR ======
        if key.upper() == self.interrupt_key:
            self.trigger_interrupt()
            return

        # Obtener VK code
        vk = self.VK.get(key.upper())
        if vk is None:
            print(f"⚠ Tecla desconocida: {key}")
            return

        # Enviar tecla RAW
        self.send_raw_key(vk)
        time.sleep(hold)

    # -----------------------------------------------------------

    def type_text(self, text, spacing=0.05):
        """
        Escribe texto carácter por carácter usando press().

        Parámetros:
        - text: string a escribir.
        - spacing: tiempo entre cada tecla.

        Notas:
        - Todo funciona en RAW MODE.
        - Respeta el interruptor global.
        """
        for char in text.upper():
            if char in self.VK:
                self.press(char)
                time.sleep(spacing)

    # -----------------------------------------------------------

    def enable_global_interrupt(self):
        """
        Activa un listener global que detecta la tecla interruptora
        aunque la ventana NO esté activa.
        
        Usa pynput.Listener en un thread separado.
        """
        if self.listener is not None:
            return  # Ya estaba activo

        def on_press(key):
            """Detecta la tecla física presionada."""
            try:
                # Caso 1: teclas normales → key.char
                if hasattr(key, "char") and key.char:
                    pressed = key.char.upper()
                # Caso 2: teclas especiales → key.name
                elif hasattr(key, "name"):
                    pressed = key.name.upper()
                else:
                    return

                if pressed == self.interrupt_key:
                    self.trigger_interrupt()

            except:
                pass

        # Crear listener
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

        print(f"🎧 Listener global activado (interruptor = {self.interrupt_key})")
    # -----------------------------------------------------------

    def hold_key(self, key):
        """
        Envía WM_KEYDOWN de forma repetida para simular que la tecla
        está mantenida presionada en RAW MODE (segundo plano).
        """
        vk = self.VK.get(key.upper())
        if vk is None:
            print(f"⚠ Tecla desconocida en hold_key(): {key}")
            return

        # KEYDOWN sin KEYUP
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk, 0)
