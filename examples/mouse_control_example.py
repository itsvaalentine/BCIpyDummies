#!/usr/bin/env python3
"""
Ejemplo de Control de Mouse con BCIpyDummies (Hardware Real Emotiv)
====================================================================

Este ejemplo muestra cómo usar la librería BCIpyDummies para controlar
el mouse usando comandos mentales con un headset Emotiv real.

Comandos soportados:
- LEFT (izquierda): Mueve el mouse hacia la izquierda
- RIGHT (derecha): Mueve el mouse hacia la derecha
- LIFT (arriba): Mueve el mouse hacia arriba

Requisitos:
- Python 3.9+
- BCIpyDummies instalado (pip install -e .)
- pyautogui instalado (pip install pyautogui)
- Emotiv Cortex app corriendo
- Headset Emotiv conectado (EPOC X, EPOC+, Insight, etc.)
- Comandos mentales entrenados en la app EmotivBCI

Configuración:
    Antes de ejecutar, configura tus credenciales de Emotiv:
    
    Windows (PowerShell):
        $env:EMOTIV_CLIENT_ID = "tu_client_id"
        $env:EMOTIV_CLIENT_SECRET = "tu_client_secret"
    
    Windows (CMD):
        set EMOTIV_CLIENT_ID=tu_client_id
        set EMOTIV_CLIENT_SECRET=tu_client_secret
    
    Linux/Mac:
        export EMOTIV_CLIENT_ID="tu_client_id"
        export EMOTIV_CLIENT_SECRET="tu_client_secret"

Uso:
    python mouse_control_example.py
"""

import os
import time
import logging
from typing import Optional

from bcipydummies.core.events import MentalCommandEvent, MentalCommand

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Configuración
# ============================================

# Píxeles que se mueve el mouse por cada comando mental
MOUSE_MOVE_PIXELS = 50

# Potencia mínima requerida para activar el movimiento (0.0 - 1.0)
POWER_THRESHOLD = 0.5


# ============================================
# Publisher personalizado para control de mouse
# ============================================

class MousePublisher:
    """Publisher que mueve el mouse basándose en comandos mentales.
    
    Este publisher usa pyautogui para mover el mouse en la dirección
    indicada por el comando mental recibido desde el headset Emotiv.
    
    Mapeo de comandos:
        - LEFT: Mueve el mouse a la izquierda
        - RIGHT: Mueve el mouse a la derecha
        - LIFT: Mueve el mouse hacia arriba
        
    Ejemplo:
        >>> publisher = MousePublisher(move_pixels=50)
        >>> publisher.start()
        >>> # Conectar a un pipeline BCI...
        >>> publisher.stop()
    """
    
    def __init__(self, move_pixels: int = 50, power_threshold: float = 0.5):
        """Inicializa el MousePublisher.
        
        Args:
            move_pixels: Número de píxeles que se mueve el mouse por comando.
            power_threshold: Potencia mínima (0.0-1.0) para activar el movimiento.
        """
        self._move_pixels = move_pixels
        self._power_threshold = power_threshold
        self._is_ready = False
        self._pyautogui: Optional[object] = None
        
    @property
    def is_ready(self) -> bool:
        """Verifica si el publisher está listo."""
        return self._is_ready
        
    def start(self) -> None:
        """Inicia el publisher e importa pyautogui."""
        try:
            import pyautogui
            self._pyautogui = pyautogui
            # Configurar pyautogui para seguridad
            pyautogui.FAILSAFE = True  # Mover mouse a esquina superior izquierda para detener
            pyautogui.PAUSE = 0.1  # Pausa entre movimientos
            self._is_ready = True
            logger.info("MousePublisher iniciado correctamente")
        except ImportError:
            raise ImportError(
                "pyautogui es requerido para MousePublisher. "
                "Instálalo con: pip install pyautogui"
            )
            
    def stop(self) -> None:
        """Detiene el publisher."""
        self._is_ready = False
        logger.info("MousePublisher detenido")
        
    def publish(self, event) -> None:
        """Procesa un evento y mueve el mouse si corresponde.
        
        Args:
            event: Evento EEG a procesar.
        """
        if not self._is_ready:
            return
        
        if not isinstance(event, MentalCommandEvent):
            return
            
        # Verificar si la potencia supera el umbral
        if event.power < self._power_threshold:
            return
            
        # Mapear comando a movimiento de mouse
        if event.command == MentalCommand.LEFT:
            self._move_mouse(-self._move_pixels, 0)
            logger.info(f"⬅️  Moviendo izquierda ({event.power*100:.1f}% potencia)")
            
        elif event.command == MentalCommand.RIGHT:
            self._move_mouse(self._move_pixels, 0)
            logger.info(f"➡️  Moviendo derecha ({event.power*100:.1f}% potencia)")
            
        elif event.command == MentalCommand.LIFT:
            self._move_mouse(0, -self._move_pixels)  # Negativo = arriba
            logger.info(f"⬆️  Moviendo arriba ({event.power*100:.1f}% potencia)")
            
    def _move_mouse(self, dx: int, dy: int) -> None:
        """Mueve el mouse relativamente.
        
        Args:
            dx: Movimiento horizontal (positivo = derecha).
            dy: Movimiento vertical (positivo = abajo).
        """
        if self._pyautogui:
            self._pyautogui.moveRel(dx, dy)


# ============================================
# Función principal
# ============================================

def main():
    """Función principal que ejecuta el ejemplo de control de mouse con Emotiv."""
    
    print("=" * 60)
    print("  BCIpyDummies - Control de Mouse con Emotiv")
    print("=" * 60)
    print()
    print("Comandos mentales -> Movimiento de mouse:")
    print("  - LEFT  -> Mover izquierda")
    print("  - RIGHT -> Mover derecha") 
    print("  - LIFT  -> Mover arriba")
    print()
    
    # Verificar credenciales de Emotiv
    client_id = os.environ.get("EMOTIV_CLIENT_ID")
    client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Error: No se encontraron las credenciales de Emotiv.")
        print()
        print("Configura las variables de entorno antes de ejecutar:")
        print()
        print("  Windows (PowerShell):")
        print('    $env:EMOTIV_CLIENT_ID = "tu_client_id"')
        print('    $env:EMOTIV_CLIENT_SECRET = "tu_client_secret"')
        print()
        print("  Windows (CMD):")
        print("    set EMOTIV_CLIENT_ID=tu_client_id")
        print("    set EMOTIV_CLIENT_SECRET=tu_client_secret")
        print()
        print("  Linux/Mac:")
        print('    export EMOTIV_CLIENT_ID="tu_client_id"')
        print('    export EMOTIV_CLIENT_SECRET="tu_client_secret"')
        print()
        print("Obtén tus credenciales en: https://www.emotiv.com/developer/")
        return
    
    print("✅ Credenciales de Emotiv encontradas")
    print()
    
    # Importar componentes de bcipydummies
    from bcipydummies import BCIPipeline
    from bcipydummies.sources.emotiv import EmotivSource, CortexCredentials
    
    # Crear credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Crear el publisher de mouse
    mouse_publisher = MousePublisher(
        move_pixels=MOUSE_MOVE_PIXELS,
        power_threshold=POWER_THRESHOLD
    )
    
    # Crear source de Emotiv
    print("🎧 Configurando conexión con Emotiv Cortex...")
    source = EmotivSource(
        credentials=credentials,
        streams=["com"]  # Solo comandos mentales
    )
    
    # Crear el pipeline
    pipeline = BCIPipeline(
        source=source,
        publishers=[mouse_publisher]
    )
    
    print()
    print("📋 Checklist antes de iniciar:")
    print("   [ ] Emotiv Cortex app está corriendo")
    print("   [ ] Headset Emotiv está conectado a Cortex")
    print("   [ ] Comandos mentales (left, right, lift) están entrenados")
    print("   [ ] Calidad de contacto de sensores es buena (verde)")
    print()
    print("Presiona Ctrl+C en cualquier momento para detener.")
    print()
    input("Presiona Enter para conectar con el headset...")
    print()
    
    try:
        # Iniciar el pipeline
        print("🚀 Conectando con Emotiv Cortex...")
        pipeline.start()
        print()
        print("=" * 60)
        print("✅ ¡Conectado! El mouse se moverá con tus comandos mentales.")
        print("=" * 60)
        print()
        print("Comandos activos:")
        print(f"  - Piensa 'LEFT'  -> Mouse izquierda ({MOUSE_MOVE_PIXELS}px)")
        print(f"  - Piensa 'RIGHT' -> Mouse derecha ({MOUSE_MOVE_PIXELS}px)")
        print(f"  - Piensa 'LIFT'  -> Mouse arriba ({MOUSE_MOVE_PIXELS}px)")
        print()
        print("Umbral de potencia: {:.0f}%".format(POWER_THRESHOLD * 100))
        print()
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print()
        print("⏹️  Deteniendo conexión...")
        
    finally:
        pipeline.stop()
        print("👋 ¡Hasta luego!")


if __name__ == "__main__":
    main()
