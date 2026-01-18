"""
BCI Mouse + Dwell Time + Auto-Scroll
"""

import ctypes
import time
import threading
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver. chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager. chrome import ChromeDriverManager

from bcipydummies import BCIPipeline
from bcipydummies. sources. emotiv import EmotivSource
from bcipydummies.sources. emotiv.cortex_client import CortexCredentials
from bcipydummies.processors import ThresholdProcessor
from bcipydummies.publishers.base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand

# ============================================
# CONFIGURACIÓN
# ============================================
CLIENT_ID = "APvEkVWaNRThrdfMKOjTL7DFsm1lZ212PN9X3GiZ"
CLIENT_SECRET = "k3piWq0YRfk4d2Tct5mjaEUWFKLrrn36aYhU1gsdGXckAFZQ0x5vz0Vh9H7Pvy1w9qDLYKxYfFx9zw7AKOuymCWcwXbWDG85TuzNXs2h47p8RCLxsPqRzj9PAABNcxfr"
PIXELS = 30
DWELL_TIME = 1.5
SCROLL_ZONE = 80
SCROLL_AMOUNT = 150
URL_INICIAL = "https://www.google.com"


# ============================================
# MOUSE CONTROLLER
# ============================================
class Mouse:
    @staticmethod
    def pos() -> Tuple[int, int]: 
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes. c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt. y)
    
    @staticmethod
    def move(x:  int, y: int):
        ctypes.windll.user32.SetCursorPos(x, y)
    
    @staticmethod
    def click():
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)


# ============================================
# DWELL TIME + SCROLL
# ============================================
class DwellManager:
    def __init__(self, driver: webdriver. Chrome, dwell_time: float = 1.5):
        self.driver = driver
        self.dwell_time = dwell_time
        self.last_element_id = None
        self.hover_start = 0
        self._running = False
    
    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        print(f"⏱️ Dwell:  {self.dwell_time}s | Scroll zone: {SCROLL_ZONE}px")
    
    def stop(self):
        self._running = False
        self._clear_highlight()
    
    def _get_browser_rect(self):
        try:
            r = self.driver.get_window_rect()
            return r['x'], r['y'] + 80, r['width'], r['height'] - 80
        except: 
            return 0, 0, 1920, 1080
    
    def _get_element(self):
        try:
            x, y = Mouse. pos()
            bx, by, bw, bh = self._get_browser_rect()
            rx, ry = x - bx, y - by
            if rx < 0 or ry < 0:
                return None, None
            elem = self.driver.execute_script(f"return document.elementFromPoint({rx}, {ry});")
            if elem:
                tag = elem.tag_name
                eid = elem.get_attribute('id') or ''
                cls = elem.get_attribute('class') or ''
                rect = elem. rect
                elem_id = f"{tag}|{eid}|{cls}|{int(rect['x'])},{int(rect['y'])}"
                return elem, elem_id
            return None, None
        except:
            return None, None
    
    def _highlight_element(self, elem):
        """Resalta el elemento con borde y muestra etiqueta."""
        try:
            rect = elem.rect
            tag = elem.tag_name
            text = (elem.text or "")[:25]. replace("'", "\\'").replace("\n", " ")
            label = f"<{tag}> {text}" if text else f"<{tag}>"
            color = "#4CAF50"  # Verde
            
            # Color según progreso
            # if progress < 0.5:
            #     color = "#4CAF50"  # Verde
            # elif progress < 0.9:
            #     color = "#FF9800"  # Naranja
            # else:
            #     color = "#f44336"  # Rojo
            
            self.driver.execute_script(f"""
                (function() {{
                    // Highlight del elemento
                    let hl = document.getElementById('dwell-hl');
                    if (! hl) {{
                        hl = document.createElement('div');
                        hl.id = 'dwell-hl';
                        document.body.appendChild(hl);
                    }}
                    hl.style. cssText = `
                        position: fixed;
                        left: {rect['x']}px;
                        top: {rect['y']}px;
                        width: {rect['width']}px;
                        height: {rect['height']}px;
                        border: 3px solid {color};
                        background: {color}22;
                        pointer-events: none;
                        z-index: 999998;
                        box-sizing: border-box;
                        transition: border-color 0.2s, background 0.2s;
                    `;
                    
                    // Etiqueta
                    let lbl = document.getElementById('dwell-lbl');
                    if (!lbl) {{
                        lbl = document.createElement('div');
                        lbl.id = 'dwell-lbl';
                        document. body.appendChild(lbl);
                    }}
                    lbl.textContent = '{label}';
                    lbl.style. cssText = `
                        position: fixed;
                        left: {rect['x']}px;
                        top: {rect['y'] - 30}px;
                        background: {color};
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font: bold 12px sans-serif;
                        pointer-events: none;
                        z-index: 999999;
                        white-space: nowrap;
                    `;
                }})();
            """)
        except:
            pass
    
    def _clear_highlight(self):
        """Elimina el resaltado y la etiqueta."""
        try:
            self.driver.execute_script("""
                document.getElementById('dwell-hl')?.remove();
                document.getElementById('dwell-lbl')?.remove();
            """)
        except:
            pass
    
    def _scroll(self, direction: str):
        try:
            amount = -SCROLL_AMOUNT if direction == 'up' else SCROLL_AMOUNT
            self.driver. execute_script(f"window. scrollBy(0, {amount});")
            print(f"{'⬆️' if direction == 'up' else '⬇️'} Scroll {direction}")
        except:
            pass
    
    def _loop(self):
        last_scroll = 0
        
        while self._running:
            try:
                x, y = Mouse.pos()
                bx, by, bw, bh = self._get_browser_rect()
                now = time.time()
                
                # Verificar si está dentro del navegador
                if not (bx <= x <= bx + bw and by <= y <= by + bh):
                    self._clear_highlight()
                    self. last_element_id = None
                    time.sleep(0.1)
                    continue
                
                ry = y - by  # Posición relativa Y
                
                # Scroll zones
                if ry < SCROLL_ZONE:
                    self._clear_highlight()
                    self. last_element_id = None
                    if now - last_scroll > 0.3:
                        self._scroll('up')
                        last_scroll = now
                    time.sleep(0.05)
                    continue
                elif ry > bh - SCROLL_ZONE:
                    self._clear_highlight()
                    self. last_element_id = None
                    if now - last_scroll > 0.3:
                        self._scroll('down')
                        last_scroll = now
                    time.sleep(0.05)
                    continue
                
                # Dwell tracking
                elem, elem_id = self._get_element()
                
                if elem and elem_id: 
                    if elem_id == self.last_element_id:
                        elapsed = now - self.hover_start
                        
                        # Actualizar highlight con progreso
                        self._highlight_element(elem)
                        
                        if elapsed >= self.dwell_time:
                            tag = elem.tag_name
                            print(f"🖱️ CLICK en <{tag}> ({x}, {y})")
                            Mouse.click()
                            self.last_element_id = None
                            time.sleep(0.5)
                    else:
                        # Nuevo elemento
                        self.last_element_id = elem_id
                        self.hover_start = now
                        self._highlight_element(elem)
                        print(f"🎯 <{elem.tag_name}>")
                else:
                    if self.last_element_id:
                        self._clear_highlight()
                    self.last_element_id = None
                    
            except:
                pass
            
            time.sleep(0.1)


# ============================================
# BCI MOUSE PUBLISHER
# ============================================
class BCIMouse(Publisher):
    def __init__(self, pixels:  int = 30):
        self._ready = False
        self. pixels = pixels
    
    def start(self):
        self._ready = True
        print(f"🖱️ Mouse BCI:  {self.pixels}px")
    
    def stop(self):
        self._ready = False
    
    @property
    def is_ready(self):
        return self._ready
    
    def publish(self, event: EEGEvent):
        if not isinstance(event, MentalCommandEvent) or event.command == MentalCommand.NEUTRAL: 
            return
        
        x, y = Mouse.pos()
        cmd = event.command
        
        if cmd == MentalCommand.LEFT:
            Mouse.move(x - self.pixels, y)
            print(f"⬅️ LEFT ({event.power:.0%})")
        elif cmd == MentalCommand. RIGHT:
            Mouse.move(x + self.pixels, y)
            print(f"➡️ RIGHT ({event.power:. 0%})")
        elif cmd == MentalCommand.LIFT:
            Mouse.move(x, y - self.pixels)
            print(f"⬆️ LIFT ({event.power:.0%})")
        elif cmd == MentalCommand.DROP:
            Mouse.move(x, y + self.pixels)
            print(f"⬇️ DROP ({event.power:.0%})")
        # elif cmd == MentalCommand. LIFT:
        #     Mouse.click()
        #     print(f"🖱️ CLICK ({event.power:.0%})")


# ============================================
# MAIN
# ============================================
def main():
    print("\n🧠 BCI MOUSE + DWELL TIME\n")
    
    if CLIENT_ID == "tu_client_id_aqui":
        print("❌ Configura CLIENT_ID y CLIENT_SECRET")
        return
    
    # Browser
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(URL_INICIAL)
    
    # Dwell
    dwell = DwellManager(driver, DWELL_TIME)
    dwell.start()
    
    # BCI
    source = EmotivSource(
        credentials=CortexCredentials(CLIENT_ID, CLIENT_SECRET)
    )
    pipeline = BCIPipeline(
        source=source,
        processors=[ThresholdProcessor(thresholds={"left": 0.3, "right": 0.3, "push": 0.3, "pull": 0.3, "lift": 0.3})],
        publishers=[BCIMouse(PIXELS)]
    )
    
    print("\n📝 Controles:")
    print("   LEFT/RIGHT/PUSH/PULL = Mover mouse")
    print("   LIFT = Clic manual")
    print(f"   Dwell {DWELL_TIME}s = Clic automático")
    print("   Cursor en bordes = Auto-scroll\n")
    
    try:
        with pipeline:
            print("🚀 Sistema activo.  Ctrl+C para salir.\n")
            while True: 
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo...")
    finally:
        dwell. stop()
        driver.quit()
        print("✅ Cerrado")

if __name__ == "__main__":
    main()