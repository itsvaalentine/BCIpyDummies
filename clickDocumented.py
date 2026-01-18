"""
BCI Mouse Controller con Dwell Time y Auto-Scroll
=================================================

Este módulo implementa un sistema de control del mouse mediante comandos
mentales utilizando un headset Emotiv EEG.  Incluye funcionalidades de: 

- Control del cursor mediante comandos mentales (LEFT, RIGHT, PUSH, PULL, LIFT)
- Dwell Time:  clic automático al mantener el cursor sobre un elemento
- Auto-Scroll: scroll automático cuando el cursor llega a los bordes
- Resaltado visual del elemento actual

Requisitos:
    - Python 3.9+
    - Windows 10/11
    - Headset Emotiv con comandos mentales entrenados
    - Emotiv Cortex ejecutándose

Dependencias:
    - bcipydummies:  Librería para interfaz con Emotiv
    - selenium: Automatización del navegador
    - webdriver-manager: Gestión automática de ChromeDriver

Uso:
    1. Configurar CLIENT_ID y CLIENT_SECRET con credenciales de Emotiv
    2. Ejecutar: python bci_mouse_dwell.py
    3. Usar comandos mentales para controlar el cursor
    4. Presionar Ctrl+C para salir

Autor: Usuario
Fecha: 2026-01-18
Versión: 1.0.0
"""

import ctypes
import time
import threading
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium. webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from bcipydummies import BCIPipeline
from bcipydummies.sources. emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies.processors import ThresholdProcessor
from bcipydummies.publishers. base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

# Credenciales de Emotiv Developer
# Obtener en:  https://www.emotiv.com/developer/
CLIENT_ID = "tu_client_id_aqui"
CLIENT_SECRET = "tu_client_secret_aqui"

# Configuración del movimiento del mouse
PIXELS = 30  # Píxeles que se mueve el cursor por cada comando mental

# Configuración del Dwell Time (clic automático)
DWELL_TIME = 1.5  # Segundos que debe permanecer sobre un elemento para hacer clic

# Configuración del Auto-Scroll
SCROLL_ZONE = 80     # Altura en píxeles de la zona de activación del scroll
SCROLL_AMOUNT = 150  # Píxeles que se desplaza por cada activación del scroll

# URL que se abre al iniciar el navegador
URL_INICIAL = "https://www.google.com"


# ============================================================================
# CLASE MOUSE - Control del cursor mediante Windows API
# ============================================================================

class Mouse:
    """
    Clase estática para controlar el cursor del mouse usando la API de Windows.
    
    Proporciona métodos para obtener la posición actual del cursor,
    mover el cursor a una posición específica y ejecutar clics.
    
    Note:
        Esta clase solo funciona en Windows ya que utiliza ctypes
        para acceder a user32.dll. 
    
    Example:
        >>> x, y = Mouse.pos()
        >>> Mouse.move(x + 100, y)
        >>> Mouse.click()
    """
    
    @staticmethod
    def pos() -> Tuple[int, int]:
        """
        Obtiene la posición actual del cursor. 
        
        Utiliza la función GetCursorPos de la API de Windows para obtener
        las coordenadas X e Y del cursor en la pantalla.
        
        Returns:
            Tuple[int, int]: Tupla con las coordenadas (x, y) del cursor.
        
        Example:
            >>> x, y = Mouse.pos()
            >>> print(f"Cursor en:  ({x}, {y})")
        """
        # Estructura POINT de Windows para almacenar coordenadas
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes. byref(pt))
        return (pt.x, pt.y)
    
    @staticmethod
    def move(x: int, y: int) -> None:
        """
        Mueve el cursor a una posición específica. 
        
        Args:
            x: Coordenada X de destino en píxeles.
            y: Coordenada Y de destino en píxeles.
        
        Example:
            >>> Mouse.move(500, 300)  # Mueve el cursor a (500, 300)
        """
        ctypes.windll.user32.SetCursorPos(x, y)
    
    @staticmethod
    def click() -> None:
        """
        Ejecuta un clic izquierdo en la posición actual del cursor.
        
        Simula presionar y soltar el botón izquierdo del mouse usando
        los eventos MOUSEEVENTF_LEFTDOWN (0x0002) y MOUSEEVENTF_LEFTUP (0x0004).
        
        Note:
            Incluye una pequeña pausa de 10ms entre presionar y soltar
            para asegurar que el clic sea registrado correctamente.
        
        Example:
            >>> Mouse.move(100, 200)
            >>> Mouse.click()  # Clic en (100, 200)
        """
        # Presionar botón izquierdo
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.01)  # Pausa para asegurar registro del clic
        # Soltar botón izquierdo
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)


# ============================================================================
# CLASE DWELLMANAGER - Gestión de Dwell Time y Auto-Scroll
# ============================================================================

class DwellManager: 
    """
    Gestor de Dwell Time y Auto-Scroll para navegador web.
    
    Esta clase monitorea la posición del cursor y proporciona: 
    - Dwell Time:  Ejecuta clic automático cuando el cursor permanece
      sobre un elemento web por un tiempo determinado. 
    - Auto-Scroll:  Ejecuta scroll automático cuando el cursor está
      en las zonas superior o inferior del navegador.
    - Resaltado visual:  Muestra el elemento actual con borde y etiqueta.
    
    Attributes:
        driver (webdriver.Chrome): Instancia del navegador Selenium.
        dwell_time (float): Tiempo en segundos para activar el clic automático.
        last_element_id (str): Identificador del último elemento detectado.
        hover_start (float): Timestamp de inicio del hover actual.
        _running (bool): Estado del loop de monitoreo.
    
    Example:
        >>> driver = webdriver.Chrome()
        >>> dwell = DwellManager(driver, dwell_time=1.5)
        >>> dwell.start()
        >>> # ...  el monitoreo se ejecuta en segundo plano
        >>> dwell.stop()
    """
    
    def __init__(self, driver: webdriver.Chrome, dwell_time: float = 1.5):
        """
        Inicializa el gestor de Dwell Time. 
        
        Args:
            driver: Instancia del navegador Chrome de Selenium.
            dwell_time: Segundos que debe permanecer sobre un elemento
                       para ejecutar el clic automático.  Default: 1.5
        """
        self.driver = driver
        self.dwell_time = dwell_time
        self. last_element_id:  Optional[str] = None
        self.hover_start: float = 0
        self._running:  bool = False
    
    def start(self) -> None:
        """
        Inicia el monitoreo de Dwell Time y Auto-Scroll.
        
        Crea un hilo daemon que ejecuta el loop de monitoreo en segundo plano.
        El hilo se detendrá automáticamente cuando el programa principal termine.
        """
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        print(f"⏱️ Dwell:  {self.dwell_time}s | Scroll zone: {SCROLL_ZONE}px")
    
    def stop(self) -> None:
        """
        Detiene el monitoreo y limpia los elementos visuales.
        
        Establece la bandera _running en False para terminar el loop
        y elimina cualquier resaltado visual que quede en la página.
        """
        self._running = False
        self._clear_highlight()
    
    def _get_browser_rect(self) -> Tuple[int, int, int, int]:
        """
        Obtiene las dimensiones del área de contenido del navegador.
        
        Calcula el rectángulo del área donde se muestra el contenido web,
        excluyendo la barra de herramientas del navegador (aprox. 80px).
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) del área de contenido.
            
        Note:
            Si hay un error, retorna valores por defecto de 1920x1080.
        """
        try:
            r = self.driver.get_window_rect()
            # Resta 80px de altura para excluir la barra de herramientas
            return r['x'], r['y'] + 80, r['width'], r['height'] - 80
        except: 
            return 0, 0, 1920, 1080
    
    def _get_element(self) -> Tuple[Optional[object], Optional[str]]:
        """
        Obtiene el elemento web bajo la posición actual del cursor.
        
        Utiliza document.elementFromPoint() de JavaScript para detectar
        qué elemento HTML está bajo el cursor.  Genera un identificador
        único basado en las propiedades del elemento.
        
        Returns:
            Tuple[Optional[object], Optional[str]]: 
                - Elemento de Selenium (o None si no hay elemento)
                - Identificador único del elemento (o None)
        
        Note:
            El identificador se genera combinando:  tag, id, clase y posición.
        """
        try:
            x, y = Mouse.pos()
            bx, by, bw, bh = self._get_browser_rect()
            
            # Calcular posición relativa al área de contenido
            rx, ry = x - bx, y - by
            
            # Verificar que el cursor está dentro del área de contenido
            if rx < 0 or ry < 0:
                return None, None
            
            # Obtener elemento usando JavaScript
            elem = self.driver.execute_script(
                f"return document.elementFromPoint({rx}, {ry});"
            )
            
            if elem: 
                # Generar identificador único del elemento
                tag = elem.tag_name
                eid = elem.get_attribute('id') or ''
                cls = elem.get_attribute('class') or ''
                rect = elem.rect
                elem_id = f"{tag}|{eid}|{cls}|{int(rect['x'])},{int(rect['y'])}"
                return elem, elem_id
            
            return None, None
        except: 
            return None, None
    
    def _highlight_element(self, elem) -> None:
        """
        Resalta visualmente el elemento actual en la página.
        
        Crea dos elementos HTML inyectados en la página: 
        1. Un div con borde verde que rodea el elemento
        2. Una etiqueta encima mostrando el tag y texto del elemento
        
        Args:
            elem: Elemento de Selenium a resaltar.
        
        Note:
            Los elementos inyectados tienen pointer-events: none
            para no interferir con la interacción del usuario.
        """
        try:
            rect = elem.rect
            tag = elem.tag_name
            # Obtener texto del elemento (máximo 25 caracteres)
            text = (elem.text or "")[:25]. replace("'", "\\'").replace("\n", " ")
            label = f"<{tag}> {text}" if text else f"<{tag}>"
            color = "#4CAF50"  # Verde
            
            self.driver.execute_script(f"""
                (function() {{
                    // Crear o actualizar el resaltado del elemento
                    let hl = document.getElementById('dwell-hl');
                    if (! hl) {{
                        hl = document.createElement('div');
                        hl.id = 'dwell-hl';
                        document.body.appendChild(hl);
                    }}
                    hl.style.cssText = `
                        position: fixed;
                        left: {rect['x']}px;
                        top: {rect['y']}px;
                        width: {rect['width']}px;
                        height: {rect['height']}px;
                        border: 3px solid {color};
                        background:  {color}22;
                        pointer-events: none;
                        z-index: 999998;
                        box-sizing: border-box;
                        transition: border-color 0.2s, background 0.2s;
                    `;
                    
                    // Crear o actualizar la etiqueta
                    let lbl = document.getElementById('dwell-lbl');
                    if (!lbl) {{
                        lbl = document. createElement('div');
                        lbl.id = 'dwell-lbl';
                        document.body.appendChild(lbl);
                    }}
                    lbl.textContent = '{label}';
                    lbl.style.cssText = `
                        position: fixed;
                        left: {rect['x']}px;
                        top:  {rect['y'] - 30}px;
                        background: {color};
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font:  bold 12px sans-serif;
                        pointer-events: none;
                        z-index: 999999;
                        white-space: nowrap;
                    `;
                }})();
            """)
        except:
            pass
    
    def _clear_highlight(self) -> None:
        """
        Elimina los elementos visuales de resaltado de la página.
        
        Remueve tanto el borde de resaltado como la etiqueta
        que fueron inyectados por _highlight_element().
        """
        try:
            self.driver.execute_script("""
                document.getElementById('dwell-hl')?.remove();
                document.getElementById('dwell-lbl')?.remove();
            """)
        except:
            pass
    
    def _scroll(self, direction: str) -> None:
        """
        Ejecuta scroll en la página.
        
        Args:
            direction: Dirección del scroll ('up' o 'down').
        
        Note:
            La cantidad de scroll está definida por SCROLL_AMOUNT.
        """
        try:
            amount = -SCROLL_AMOUNT if direction == 'up' else SCROLL_AMOUNT
            self.driver.execute_script(f"window.scrollBy(0, {amount});")
            emoji = '⬆️' if direction == 'up' else '⬇️'
            print(f"{emoji} Scroll {direction}")
        except:
            pass
    
    def _loop(self) -> None:
        """
        Loop principal de monitoreo. 
        
        Ejecuta continuamente mientras _running sea True: 
        1. Verifica si el cursor está dentro del navegador
        2. Detecta si está en zona de scroll y ejecuta scroll
        3. Detecta el elemento bajo el cursor
        4. Gestiona el Dwell Time y ejecuta clic si corresponde
        5. Actualiza el resaltado visual
        
        Note:
            Este método se ejecuta en un hilo separado iniciado por start().
            El intervalo de verificación es de 100ms para contenido normal
            y 50ms para las zonas de scroll.
        """
        last_scroll = 0  # Timestamp del último scroll
        
        while self._running:
            try:
                x, y = Mouse.pos()
                bx, by, bw, bh = self._get_browser_rect()
                now = time.time()
                
                # Verificar si el cursor está dentro del navegador
                if not (bx <= x <= bx + bw and by <= y <= by + bh):
                    self._clear_highlight()
                    self. last_element_id = None
                    time.sleep(0.1)
                    continue
                
                # Calcular posición relativa Y
                ry = y - by
                
                # ========== ZONA DE SCROLL SUPERIOR ==========
                if ry < SCROLL_ZONE:
                    self._clear_highlight()
                    self. last_element_id = None
                    # Scroll con cooldown de 300ms
                    if now - last_scroll > 0.3:
                        self._scroll('up')
                        last_scroll = now
                    time.sleep(0.05)
                    continue
                
                # ========== ZONA DE SCROLL INFERIOR ==========
                elif ry > bh - SCROLL_ZONE: 
                    self._clear_highlight()
                    self.last_element_id = None
                    # Scroll con cooldown de 300ms
                    if now - last_scroll > 0.3:
                        self._scroll('down')
                        last_scroll = now
                    time.sleep(0.05)
                    continue
                
                # ========== TRACKING DE DWELL TIME ==========
                elem, elem_id = self._get_element()
                
                if elem and elem_id:
                    if elem_id == self.last_element_id:
                        # Mismo elemento - calcular tiempo transcurrido
                        elapsed = now - self.hover_start
                        
                        # Actualizar resaltado visual
                        self._highlight_element(elem)
                        
                        # Verificar si se alcanzó el tiempo de dwell
                        if elapsed >= self. dwell_time:
                            tag = elem.tag_name
                            print(f"🖱️ CLICK en <{tag}> ({x}, {y})")
                            Mouse.click()
                            # Resetear estado
                            self.last_element_id = None
                            time.sleep(0.5)  # Pausa post-clic
                    else:
                        # Nuevo elemento - iniciar nuevo tracking
                        self.last_element_id = elem_id
                        self.hover_start = now
                        self._highlight_element(elem)
                        print(f"🎯 <{elem.tag_name}>")
                else:
                    # No hay elemento bajo el cursor
                    if self.last_element_id:
                        self._clear_highlight()
                    self.last_element_id = None
                    
            except: 
                pass
            
            time.sleep(0.1)


# ============================================================================
# CLASE BCIMOUSE - Publisher para BCIpyDummies
# ============================================================================

class BCIMouse(Publisher):
    """
    Publisher que convierte comandos mentales en movimientos del mouse.
    
    Implementa la interfaz Publisher de BCIpyDummies para recibir eventos
    de comandos mentales y traducirlos en movimientos del cursor.
    
    Attributes:
        _ready (bool): Indica si el publisher está listo para recibir eventos.
        pixels (int): Cantidad de píxeles a mover por cada comando. 
    
    Comandos soportados:
        - LEFT:  Mueve el cursor a la izquierda
        - RIGHT: Mueve el cursor a la derecha
        - PUSH: Mueve el cursor hacia arriba
        - PULL:  Mueve el cursor hacia abajo
        - LIFT: Ejecuta un clic
    
    Example:
        >>> mouse_pub = BCIMouse(pixels=30)
        >>> pipeline = BCIPipeline(source=source, publishers=[mouse_pub])
    """
    
    def __init__(self, pixels: int = 30):
        """
        Inicializa el publisher de mouse. 
        
        Args:
            pixels: Cantidad de píxeles a mover por cada comando mental.
                   Default: 30
        """
        self._ready: bool = False
        self.pixels: int = pixels
    
    def start(self) -> None:
        """
        Inicia el publisher. 
        
        Llamado automáticamente por BCIPipeline al iniciar.
        Establece el estado como listo para recibir eventos. 
        """
        self._ready = True
        print(f"🖱️ Mouse BCI:  {self.pixels}px")
    
    def stop(self) -> None:
        """
        Detiene el publisher. 
        
        Llamado automáticamente por BCIPipeline al detener.
        """
        self._ready = False
    
    @property
    def is_ready(self) -> bool:
        """
        Indica si el publisher está listo para recibir eventos.
        
        Returns:
            bool: True si está listo, False en caso contrario.
        """
        return self._ready
    
    def publish(self, event: EEGEvent) -> None:
        """
        Procesa un evento de comando mental.
        
        Recibe eventos del pipeline de BCIpyDummies y ejecuta
        la acción correspondiente según el comando mental detectado.
        
        Args:
            event: Evento EEG recibido del pipeline.
        
        Note:
            Los eventos NEUTRAL son ignorados.
            La potencia del comando se muestra en la consola.
        """
        # Filtrar eventos que no son comandos mentales o son neutrales
        if not isinstance(event, MentalCommandEvent):
            return
        if event.command == MentalCommand. NEUTRAL:
            return
        
        # Obtener posición actual del cursor
        x, y = Mouse.pos()
        cmd = event.command
        
        # Ejecutar acción según el comando
        if cmd == MentalCommand.LEFT:
            Mouse.move(x - self.pixels, y)
            print(f"⬅️ LEFT ({event.power:. 0%})")
            
        elif cmd == MentalCommand.RIGHT:
            Mouse. move(x + self.pixels, y)
            print(f"➡️ RIGHT ({event. power:.0%})")
            
        elif cmd == MentalCommand.PUSH:
            Mouse.move(x, y - self.pixels)
            print(f"⬆️ PUSH ({event.power:.0%})")
            
        elif cmd == MentalCommand.PULL:
            Mouse.move(x, y + self.pixels)
            print(f"⬇️ PULL ({event.power:.0%})")
            
        elif cmd == MentalCommand.LIFT:
            Mouse.click()
            print(f"🖱️ CLICK ({event.power:.0%})")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main() -> None:
    """
    Función principal del programa.
    
    Ejecuta los siguientes pasos:
    1. Verifica la configuración de credenciales
    2. Inicia el navegador Chrome con Selenium
    3. Configura el gestor de Dwell Time
    4. Configura el pipeline de BCI con Emotiv
    5. Ejecuta el loop principal hasta recibir Ctrl+C
    6. Limpia los recursos al terminar
    
    Raises:
        KeyboardInterrupt:  Cuando el usuario presiona Ctrl+C. 
    
    Example:
        >>> main()
        🧠 BCI MOUSE + DWELL TIME
        ... 
    """
    print("\n🧠 BCI MOUSE + DWELL TIME\n")
    
    # ===== VERIFICAR CONFIGURACIÓN =====
    if CLIENT_ID == "tu_client_id_aqui":
        print("❌ Configura CLIENT_ID y CLIENT_SECRET")
        return
    
    # ===== INICIAR NAVEGADOR =====
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(URL_INICIAL)
    
    # ===== INICIAR DWELL MANAGER =====
    dwell = DwellManager(driver, DWELL_TIME)
    dwell.start()
    
    # ===== CONFIGURAR PIPELINE BCI =====
    source = EmotivSource(
        credentials=CortexCredentials(CLIENT_ID, CLIENT_SECRET)
    )
    
    # Configurar umbrales de detección (30% de potencia mínima)
    processors = [
        ThresholdProcessor(
            thresholds={
                "left": 0.3,
                "right": 0.3,
                "push": 0.3,
                "pull": 0.3,
                "lift": 0.3
            }
        )
    ]
    
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[BCIMouse(PIXELS)]
    )
    
    # ===== MOSTRAR INSTRUCCIONES =====
    print("\n📝 Controles:")
    print("   LEFT/RIGHT/PUSH/PULL = Mover mouse")
    print("   LIFT = Clic manual")
    print(f"   Dwell {DWELL_TIME}s = Clic automático")
    print("   Cursor en bordes = Auto-scroll\n")
    
    # ===== EJECUTAR LOOP PRINCIPAL =====
    try:
        with pipeline: 
            print("🚀 Sistema activo.  Ctrl+C para salir.\n")
            while True: 
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo...")
    finally:
        # ===== LIMPIAR RECURSOS =====
        dwell.stop()
        driver.quit()
        print("✅ Cerrado")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()