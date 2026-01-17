"""
CONTROL DE MOUSE CON BCI + SELENIUM DWELL TIME + AUTO-SCROLL
=============================================================
- Clic exacto en posición del cursor
- Tracking por elemento (más tolerante a movimientos involuntarios)
- Auto-scroll cuando el cursor llega a los límites superior/inferior
"""

import ctypes
import time
import threading
from dataclasses import dataclass
from typing import Optional, Callable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# BCIpyDummies imports
from bcipydummies import BCIPipeline
from bcipydummies.sources. emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies.processors import ThresholdProcessor
from bcipydummies.publishers.base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand


# ============================================
# CONFIGURACIÓN
# ============================================

CLIENT_ID = "tu_client_id_aqui"
CLIENT_SECRET = "tu_client_secret_aqui"

PIXELS_POR_MOVIMIENTO = 30
DWELL_TIME_SECONDS = 1.5
DWELL_CHECK_INTERVAL = 0.1
URL_INICIAL = "https://www.google.com"

# Configuración de scroll automático
SCROLL_ZONE_HEIGHT = 80      # Píxeles desde el borde para activar scroll
SCROLL_AMOUNT = 150          # Píxeles a scrollear por cada activación
SCROLL_INTERVAL = 0.3        # Segundos entre cada scroll mientras está en la zona


# ============================================
# CONTROLADOR DE MOUSE (WINDOWS API)
# ============================================

class MouseController:
    """Control directo del mouse usando Windows API."""
    
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    
    @staticmethod
    def get_position() -> tuple:
        """Obtiene la posición actual del cursor."""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes. byref(pt))
        return (pt.x, pt.y)
    
    @staticmethod
    def set_position(x: int, y: int):
        """Mueve el cursor a una posición específica."""
        ctypes.windll.user32.SetCursorPos(x, y)
    
    @staticmethod
    def click():
        """Ejecuta un clic izquierdo en la posición actual del cursor."""
        ctypes.windll.user32.mouse_event(
            MouseController.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0
        )
        time.sleep(0.01)
        ctypes.windll.user32.mouse_event(
            MouseController.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0
        )


# ============================================
# AUTO-SCROLL MANAGER
# ============================================

class AutoScrollManager:
    """
    Gestiona el scroll automático cuando el cursor está en los bordes.
    """
    
    def __init__(self, driver: webdriver.Chrome,
                 zone_height: int = 80,
                 scroll_amount: int = 150,
                 scroll_interval: float = 0.3):
        """
        Args:
            driver: WebDriver de Selenium
            zone_height:  Altura de la zona de activación (píxeles desde el borde)
            scroll_amount: Cantidad de píxeles a scrollear
            scroll_interval: Tiempo entre scrolls continuos
        """
        self.driver = driver
        self.zone_height = zone_height
        self. scroll_amount = scroll_amount
        self.scroll_interval = scroll_interval
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_scroll_time = 0
        self._enabled = True
    
    def start(self):
        """Inicia el monitoreo de scroll."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"📜 Auto-scroll iniciado (zona: {self.zone_height}px)")
    
    def stop(self):
        """Detiene el monitoreo."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("📜 Auto-scroll detenido")
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False
    
    def _get_browser_content_area(self) -> dict:
        """Obtiene el área de contenido del navegador."""
        try:
            window_rect = self.driver.get_window_rect()
            # Aproximación: toolbar ~80px, bordes ~10px
            toolbar_height = 80
            return {
                'x': window_rect['x'],
                'y': window_rect['y'] + toolbar_height,
                'width': window_rect['width'],
                'height':  window_rect['height'] - toolbar_height,
                'top': window_rect['y'] + toolbar_height,
                'bottom': window_rect['y'] + window_rect['height']
            }
        except: 
            return None
    
    def _check_scroll_zone(self, cursor_y: int, content_area: dict) -> str:
        """
        Determina si el cursor está en una zona de scroll.
        
        Returns:
            'up', 'down', o 'none'
        """
        top_zone_end = content_area['top'] + self.zone_height
        bottom_zone_start = content_area['bottom'] - self.zone_height
        
        if cursor_y <= top_zone_end: 
            return 'up'
        elif cursor_y >= bottom_zone_start:
            return 'down'
        return 'none'
    
    def _perform_scroll(self, direction: str):
        """Ejecuta el scroll en la dirección indicada."""
        try:
            if direction == 'up':
                scroll_value = -self.scroll_amount
                emoji = "⬆️"
            else: 
                scroll_value = self.scroll_amount
                emoji = "⬇️"
            
            self.driver.execute_script(f"window.scrollBy(0, {scroll_value});")
            print(f"{emoji} Auto-scroll {direction}")
            
        except Exception as e: 
            pass
    
    def _show_scroll_indicator(self, direction: str, content_area: dict):
        """Muestra indicador visual de la zona de scroll activa."""
        try:
            color = "#4CAF50" if direction == 'up' else "#2196F3"
            position = "top:  0" if direction == 'up' else "bottom: 0"
            arrow = "▲" if direction == 'up' else "▼"
            
            script = f"""
            (function() {{
                let indicator = document.getElementById('scroll-indicator');
                if (! indicator) {{
                    indicator = document.createElement('div');
                    indicator.id = 'scroll-indicator';
                    document.body.appendChild(indicator);
                }}
                indicator.innerHTML = '{arrow} SCROLL {direction. upper()} {arrow}';
                indicator.style. cssText = `
                    position: fixed;
                    {position};
                    left: 0;
                    right: 0;
                    height: {self.zone_height}px;
                    background: linear-gradient(
                        {'to bottom' if direction == 'up' else 'to top'},
                        {color}66,
                        transparent
                    );
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 1px 1px 2px black;
                    pointer-events: none;
                    z-index: 999999;
                    opacity: 0.8;
                `;
            }})();
            """
            self. driver.execute_script(script)
        except: 
            pass
    
    def _hide_scroll_indicator(self):
        """Oculta el indicador de scroll."""
        try:
            self.driver.execute_script("""
                let indicator = document.getElementById('scroll-indicator');
                if (indicator) indicator.remove();
            """)
        except:
            pass
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        last_direction = 'none'
        
        while self._running:
            try:
                if not self._enabled:
                    time.sleep(0.1)
                    continue
                
                cursor_pos = MouseController.get_position()
                content_area = self._get_browser_content_area()
                
                if not content_area:
                    time.sleep(0.1)
                    continue
                
                # Verificar si el cursor está dentro del navegador (horizontalmente)
                if not (content_area['x'] <= cursor_pos[0] <= content_area['x'] + content_area['width']):
                    if last_direction != 'none':
                        self._hide_scroll_indicator()
                        last_direction = 'none'
                    time.sleep(0.1)
                    continue
                
                direction = self._check_scroll_zone(cursor_pos[1], content_area)
                current_time = time.time()
                
                if direction != 'none':
                    # Mostrar indicador
                    if direction != last_direction:
                        self._show_scroll_indicator(direction, content_area)
                    
                    # Ejecutar scroll si pasó suficiente tiempo
                    if current_time - self._last_scroll_time >= self.scroll_interval:
                        self._perform_scroll(direction)
                        self._last_scroll_time = current_time
                else:
                    # Ocultar indicador si salió de la zona
                    if last_direction != 'none': 
                        self._hide_scroll_indicator()
                
                last_direction = direction
                
            except Exception as e:
                pass
            
            time.sleep(0.05)  # Check más frecuente para scroll suave


# ============================================
# DWELL TIME TRACKER (POR ELEMENTO + CLIC EXACTO)
# ============================================

@dataclass
class DwellState:
    """Estado del tracking de dwell time."""
    last_element:  Optional[object] = None
    last_element_id: Optional[str] = None
    hover_start_time: float = 0.0
    is_hovering: bool = False


class DwellTimeTracker: 
    """
    Rastrea cuando el mouse permanece sobre un elemento web.
    - Tracking por ELEMENTO (tolerante a pequeños movimientos)
    - Clic EXACTO en la posición del cursor
    """
    
    def __init__(self, driver: webdriver.Chrome,
                 dwell_time: float = 1.5,
                 on_dwell_click: Optional[Callable] = None):
        """
        Args: 
            driver: WebDriver de Selenium
            dwell_time:  Segundos sobre el elemento para activar clic
            on_dwell_click: Callback después del clic (recibe x, y, element)
        """
        self. driver = driver
        self. dwell_time = dwell_time
        self.on_dwell_click = on_dwell_click
        
        self. state = DwellState()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._enabled = True
    
    def start(self):
        """Inicia el monitoreo."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"⏱️  Dwell Time iniciado: {self.dwell_time}s (tracking por elemento)")
    
    def stop(self):
        """Detiene el monitoreo."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._hide_visual_feedback()
        print("⏱️  Dwell Time detenido")
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False
        self. state.is_hovering = False
    
    def reset(self):
        """Reinicia el estado del dwell."""
        self.state.is_hovering = False
        self.state.last_element = None
        self.state.last_element_id = None
        self._hide_visual_feedback()
    
    def _get_browser_offset(self) -> tuple:
        """Obtiene el offset de la ventana del navegador."""
        try:
            rect = self.driver.get_window_rect()
            toolbar_height = 80
            return (rect['x'], rect['y'] + toolbar_height)
        except:
            return (0, 0)
    
    def _get_element_at_cursor(self) -> Optional[object]: 
        """Obtiene el elemento web bajo el cursor actual."""
        try:
            cursor_pos = MouseController.get_position()
            offset = self._get_browser_offset()
            
            rel_x = cursor_pos[0] - offset[0]
            rel_y = cursor_pos[1] - offset[1]
            
            if rel_x < 0 or rel_y < 0:
                return None
            
            script = f"return document.elementFromPoint({rel_x}, {rel_y});"
            element = self.driver.execute_script(script)
            return element
            
        except:
            return None
    
    def _get_element_identifier(self, element) -> Optional[str]:
        """Genera un identificador único para el elemento."""
        if element is None:
            return None
        try:
            # Usar combinación de propiedades para identificar
            tag = element.tag_name
            element_id = element.get_attribute('id') or ''
            class_name = element.get_attribute('class') or ''
            text = (element.text or '')[: 20]
            
            # También usar la posición como fallback
            rect = element.rect
            
            return f"{tag}|{element_id}|{class_name}|{text}|{rect['x']:. 0f},{rect['y']:.0f}"
        except:
            return None
    
    def _is_same_element(self, elem1, elem2, id1:  str, id2: str) -> bool:
        """Compara si dos elementos son el mismo."""
        if elem1 is None or elem2 is None:
            return False
        
        # Comparar por identificador generado
        if id1 and id2:
            return id1 == id2
        
        # Fallback:  comparar por ID interno de Selenium
        try:
            return elem1.id == elem2.id
        except:
            return False
    
    def _show_visual_feedback(self, element, progress:  float):
        """Muestra feedback visual del progreso del dwell."""
        try:
            # Crear indicador circular en el cursor
            cursor_pos = MouseController.get_position()
            offset = self._get_browser_offset()
            rel_x = cursor_pos[0] - offset[0]
            rel_y = cursor_pos[1] - offset[1]
            
            degrees = progress * 360
            color = "#4CAF50" if progress < 1 else "#FF5722"
            scale = 1 + (progress * 0.3)
            
            script = f"""
            (function() {{
                // Indicador circular en el cursor
                let indicator = document. getElementById('dwell-indicator');
                if (!indicator) {{
                    indicator = document.createElement('div');
                    indicator.id = 'dwell-indicator';
                    document.body.appendChild(indicator);
                }}
                indicator. style.cssText = `
                    position: fixed;
                    left: {rel_x}px;
                    top: {rel_y}px;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    border: 3px solid {color};
                    background: conic-gradient({color} {degrees}deg, transparent {degrees}deg);
                    transform:  translate(-50%, -50%) scale({scale});
                    pointer-events: none;
                    z-index: 999999;
                    opacity: 0.8;
                    transition: transform 0.1s;
                `;
                
                // Resaltar elemento
                let highlight = document.getElementById('element-highlight');
                if (!highlight) {{
                    highlight = document.createElement('div');
                    highlight.id = 'element-highlight';
                    document.body.appendChild(highlight);
                }}
            }})();
            """
            self.driver.execute_script(script)
            
            # Resaltar el elemento
            if element:
                try:
                    rect = element.rect
                    highlight_script = f"""
                    (function() {{
                        let highlight = document.getElementById('element-highlight');
                        if (highlight) {{
                            highlight. style.cssText = `
                                position: fixed;
                                left: {rect['x']}px;
                                top:  {rect['y']}px;
                                width: {rect['width']}px;
                                height: {rect['height']}px;
                                border:  2px dashed {color};
                                background: {color}22;
                                pointer-events: none;
                                z-index: 999998;
                                transition: all 0.1s;
                            `;
                        }}
                    }})();
                    """
                    self. driver.execute_script(highlight_script)
                except:
                    pass
                    
        except: 
            pass
    
    def _hide_visual_feedback(self):
        """Oculta los indicadores visuales."""
        try:
            self.driver.execute_script("""
                let indicator = document.getElementById('dwell-indicator');
                if (indicator) indicator.remove();
                let highlight = document.getElementById('element-highlight');
                if (highlight) highlight.remove();
            """)
        except:
            pass
    
    def _perform_click(self, element):
        """Ejecuta clic en la posición actual del cursor."""
        cursor_pos = MouseController.get_position()
        
        # Info del elemento para logging
        try:
            tag = element.tag_name if element else "?"
            text = (element.text[: 30] if element and element.text else "N/A")
        except:
            tag, text = "?", "N/A"
        
        print(f"🖱️  ¡DWELL CLICK! en ({cursor_pos[0]}, {cursor_pos[1]}) - <{tag}>:  '{text}'")
        
        # Clic exacto en la posición del cursor
        MouseController.click()
        
        # Callback
        if self.on_dwell_click:
            self.on_dwell_click(cursor_pos[0], cursor_pos[1], element)
        
        # Ocultar feedback
        self._hide_visual_feedback()
        
        # Pausa post-clic
        self.state.is_hovering = False
        self.state.last_element = None
        time.sleep(0.5)
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        last_progress_shown = -1
        
        while self._running:
            try:
                if not self._enabled:
                    time.sleep(DWELL_CHECK_INTERVAL)
                    continue
                
                current_element = self._get_element_at_cursor()
                current_element_id = self._get_element_identifier(current_element)
                current_time = time.time()
                
                if current_element is not None:
                    # ¿Es el mismo elemento?
                    if self._is_same_element(
                        current_element, self.state.last_element,
                        current_element_id, self.state.last_element_id
                    ):
                        # Calcular tiempo de permanencia
                        elapsed = current_time - self.state.hover_start_time
                        progress = min(elapsed / self.dwell_time, 1.0)
                        
                        # Mostrar progreso
                        progress_step = int(progress * 4)
                        if progress_step > last_progress_shown and self.state.is_hovering:
                            last_progress_shown = progress_step
                            print(f"⏳ Dwell:  {progress * 100:.0f}%")
                        
                        # Feedback visual
                        self._show_visual_feedback(current_element, progress)
                        
                        # ¿Tiempo alcanzado?
                        if elapsed >= self.dwell_time and self.state.is_hovering:
                            self._perform_click(current_element)
                            last_progress_shown = -1
                    else:
                        # Nuevo elemento - reiniciar
                        self.state.last_element = current_element
                        self.state.last_element_id = current_element_id
                        self.state.hover_start_time = current_time
                        self.state.is_hovering = True
                        last_progress_shown = -1
                        
                        try:
                            tag = current_element.tag_name
                            print(f"🎯 Elemento:  <{tag}>")
                        except:
                            pass
                else:
                    # Cursor fuera de elementos
                    if self.state.is_hovering:
                        self. state.is_hovering = False
                        self. state.last_element = None
                        self._hide_visual_feedback()
                        last_progress_shown = -1
                        
            except Exception as e:
                pass
            
            time.sleep(DWELL_CHECK_INTERVAL)


# ============================================
# PUBLISHER DE MOUSE PARA BCI
# ============================================

class BCIMousePublisher(Publisher):
    """Publisher que convierte comandos mentales en movimientos del mouse."""
    
    def __init__(self, pixels:  int = 50,
                 dwell_tracker: Optional[DwellTimeTracker] = None):
        self._is_ready = False
        self. pixels = pixels
        self. dwell_tracker = dwell_tracker
        self.comandos_ejecutados = 0
    
    def start(self):
        self._is_ready = True
        print(f"🖱️  Mouse BCI iniciado ({self.pixels}px)")
    
    def stop(self):
        self._is_ready = False
        print(f"🖱️  Mouse BCI detenido.  Comandos:  {self.comandos_ejecutados}")
    
    @property
    def is_ready(self):
        return self._is_ready
    
    def publish(self, event: EEGEvent):
        if not isinstance(event, MentalCommandEvent):
            return
        
        if event.command == MentalCommand.NEUTRAL:
            return
        
        # Resetear dwell al moverse (opcional, para evitar clics accidentales)
        # Si prefieres que NO se resetee, comenta estas líneas:
        # if self.dwell_tracker:
        #     self.dwell_tracker.reset()
        
        x, y = MouseController.get_position()
        
        if event.command == MentalCommand.LEFT: 
            x -= self.pixels
            print(f"⬅️  LEFT ({event.power:. 0%})")
        
        elif event.command == MentalCommand.RIGHT:
            x += self.pixels
            print(f"➡️  RIGHT ({event.power:.0%})")
        
        elif event.command == MentalCommand. PUSH:
            y -= self.pixels
            print(f"⬆️  PUSH ({event.power:.0%})")
        
        elif event.command == MentalCommand.PULL: 
            y += self.pixels
            print(f"⬇️  PULL ({event.power:.0%})")
        
        elif event.command == MentalCommand.LIFT:
            MouseController.click()
            print(f"🖱️  CLICK ({event.power:.0%})")
            self.comandos_ejecutados += 1
            return
        
        MouseController.set_position(x, y)
        self.comandos_ejecutados += 1


# ============================================
# CONTROLADOR PRINCIPAL
# ============================================

class BCIBrowserController:
    """Integra BCI + Selenium + Dwell Time + Auto-Scroll."""
    
    def __init__(self, client_id: str, client_secret: str,
                 dwell_time: float = 1.5, pixels: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.dwell_time = dwell_time
        self.pixels = pixels
        
        self.driver:  Optional[webdriver.Chrome] = None
        self.pipeline: Optional[BCIPipeline] = None
        self.dwell_tracker: Optional[DwellTimeTracker] = None
        self.scroll_manager: Optional[AutoScrollManager] = None
    
    def setup_browser(self, url: str):
        """Inicia el navegador."""
        print("\n🌐 Iniciando navegador...")
        
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(url)
        
        print(f"✅ Navegador:  {url}")
        return self.driver
    
    def setup_dwell_tracker(self):
        """Configura el dwell tracker."""
        def on_click(x, y, element):
            tag = element.tag_name if element else "?"
            print(f"📌 Clic registrado:  ({x}, {y}) en <{tag}>")
        
        self.dwell_tracker = DwellTimeTracker(
            driver=self.driver,
            dwell_time=self. dwell_time,
            on_dwell_click=on_click
        )
        return self.dwell_tracker
    
    def setup_scroll_manager(self):
        """Configura el auto-scroll."""
        self.scroll_manager = AutoScrollManager(
            driver=self.driver,
            zone_height=SCROLL_ZONE_HEIGHT,
            scroll_amount=SCROLL_AMOUNT,
            scroll_interval=SCROLL_INTERVAL
        )
        return self.scroll_manager
    
    def setup_bci(self):
        """Configura el pipeline BCI."""
        print("\n🧠 Configurando BCI...")
        
        if self.client_id == "tu_client_id_aqui":
            raise ValueError("❌ Configura tus credenciales de Emotiv!")
        
        credentials = CortexCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        source = EmotivSource(credentials=credentials)
        
        processors = [
            ThresholdProcessor(threshold=0.3, cooldown=0.2)
        ]
        
        mouse_publisher = BCIMousePublisher(
            pixels=self.pixels,
            dwell_tracker=self. dwell_tracker
        )
        
        self.pipeline = BCIPipeline(
            source=source,
            processors=processors,
            publishers=[mouse_publisher]
        )
        
        print("✅ Pipeline BCI configurado")
        return self.pipeline
    
    def run(self, url: str = "https://www.google.com"):
        """Ejecuta el sistema."""
        print("\n" + "=" * 60)
        print("🧠 BCI BROWSER - DWELL TIME + AUTO-SCROLL")
        print("=" * 60)
        
        try:
            self. setup_browser(url)
            self.setup_dwell_tracker()
            self.setup_scroll_manager()
            self.setup_bci()
            
            print("\n" + "=" * 60)
            print("📝 CONTROLES:")
            print("=" * 60)
            print("  🧠 Comandos mentales:")
            print("     • LEFT/RIGHT → Mover horizontalmente")
            print("     • PUSH/PULL  → Mover verticalmente")
            print("     • LIFT       → Clic manual")
            print("")
            print("  ⏱️  Dwell Time:")
            print(f"     • Mantén sobre un elemento {self.dwell_time}s = clic")
            print("     • Tracking por elemento (tolerante a movimientos)")
            print("")
            print("  📜 Auto-Scroll:")
            print(f"     • Cursor en los {SCROLL_ZONE_HEIGHT}px superiores = scroll arriba")
            print(f"     • Cursor en los {SCROLL_ZONE_HEIGHT}px inferiores = scroll abajo")
            print("=" * 60 + "\n")
            
            self. dwell_tracker. start()
            self.scroll_manager.start()
            
            with self.pipeline:
                print("🚀 ¡Sistema activo!")
                while True:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Deteniendo...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback. print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos."""
        if self. dwell_tracker:
            self. dwell_tracker.stop()
        if self.scroll_manager:
            self.scroll_manager. stop()
        if self.driver:
            self.driver.quit()
        print("✅ Sistema cerrado")


# ============================================
# MODO DEMO (SIN BCI)
# ============================================

def run_demo_mode():
    """Modo demo con mouse normal."""
    print("\n" + "=" * 60)
    print("🧪 MODO DEMO - DWELL TIME + AUTO-SCROLL")
    print("=" * 60)
    
    options = Options()
    options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(URL_INICIAL)
    
    # Dwell tracker
    def on_click(x, y, element):
        tag = element.tag_name if element else "?"
        print(f"📌 Clic:  ({x}, {y}) en <{tag}>")
    
    dwell = DwellTimeTracker(
        driver=driver,
        dwell_time=DWELL_TIME_SECONDS,
        on_dwell_click=on_click
    )
    
    # Scroll manager
    scroll = AutoScrollManager(
        driver=driver,
        zone_height=SCROLL_ZONE_HEIGHT,
        scroll_amount=SCROLL_AMOUNT,
        scroll_interval=SCROLL_INTERVAL
    )
    
    print(f"\n⏱️  Dwell time: {DWELL_TIME_SECONDS}s")
    print(f"📜 Zona de scroll: {SCROLL_ZONE_HEIGHT}px desde bordes")
    print("⌨️  Ctrl+C para salir\n")
    
    dwell.start()
    scroll.start()
    
    try:
        while True:
            time. sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo...")
    finally:
        dwell.stop()
        scroll.stop()
        driver.quit()


# ============================================
# MAIN
# ============================================

def main():
    print("\n🧠 BCI MOUSE + DWELL TIME + AUTO-SCROLL")
    print("=" * 45)
    print("\n1. Modo completo (Emotiv)")
    print("2. Modo demo (mouse normal)")
    
    choice = input("\nOpción (1/2): ").strip()
    
    if choice == "1":
        controller = BCIBrowserController(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            dwell_time=DWELL_TIME_SECONDS,
            pixels=PIXELS_POR_MOVIMIENTO
        )
        controller. run(url=URL_INICIAL)
    elif choice == "2":
        run_demo_mode()
    else:
        print("Opción no válida")


if __name__ == "__main__": 
    main()