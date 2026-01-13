# 🧪 Ejemplos Prácticos

Esta guía contiene ejemplos de código listos para usar con BCIpyDummies.  Cada ejemplo está explicado paso a paso para que cualquier persona pueda usarlo, incluso sin experiencia en programación.

## 📋 Índice

1. [Ejemplo 1: Controlar el Notepad con tu Mente](#ejemplo-1-controlar-el-notepad-con-tu-mente)
2. [Ejemplo 2: Mover el Mouse con Comandos Mentales](#ejemplo-2-mover-el-mouse-con-comandos-mentales)
3. [Ejemplo 3: Controlar YouTube (Play/Pausa/Siguiente)](#ejemplo-3-controlar-youtube-playpausa-siguiente)
4. [Ejemplo 4: Jugar un Juego de Carreras](#ejemplo-4-jugar-un-juego-de-carreras)
5. [Ejemplo 5: Control de Presentaciones PowerPoint](#ejemplo-5-control-de-presentaciones-powerpoint)

---

## Antes de Empezar

### ⚙️ Configuración de Credenciales

Todos los ejemplos necesitan tus credenciales de Emotiv.  Para obtenerlas:

1. Ve a [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Crea una cuenta o inicia sesión
3. Crea una nueva aplicación
4. Copia tu **Client ID** y **Client Secret**

En los ejemplos verás esto: 

```python
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"
```

**¿Qué poner ahí?** Reemplaza el texto entre comillas con tus credenciales: 

```python
# ❌ INCORRECTO - No copies esto literalmente
client_id = "tu_client_id_aqui"

# ✅ CORRECTO - Usa tus credenciales reales
client_id = "abc123def456ghi789"
```

> ⚠️ **Importante**: Las comillas `""` deben quedarse, solo cambia el texto de adentro. 

### 📋 Requisitos para Todos los Ejemplos

- ✅ Windows 10 u 11
- ✅ Python 3.9 o superior instalado
- ✅ BCIpyDummies instalado (`pip install -e .`)
- ✅ Emotiv Cortex ejecutándose
- ✅ Headset Emotiv conectado
- ✅ Comandos mentales entrenados (left, right, lift, push)

---

## Ejemplo 1: Controlar el Notepad con tu Mente

**¿Qué hace?** Escribe letras en el Notepad usando comandos mentales.

| Comando Mental | Acción |
|----------------|--------|
| `left` | Escribe la letra "A" |
| `right` | Escribe la letra "D" |
| `push` | Escribe la letra "W" |
| `lift` | Escribe un espacio |

### Pasos:

1. Abre el Notepad en Windows (busca "Notepad" en el menú inicio)
2. Copia el código de abajo en un archivo llamado `controlar_notepad.py`
3. Ejecuta:  `python controlar_notepad.py`

```python
"""
EJEMPLO 1: Controlar Notepad con la Mente
=========================================
Este script te permite escribir en Notepad usando comandos mentales.
"""

# ============================================
# PASO 1: CONFIGURACIÓN - EDITA ESTA SECCIÓN
# ============================================

# Pon tus credenciales de Emotiv aquí (entre las comillas)
# Ejemplo: client_id = "abc123xyz"
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"

# Nombre de la ventana a controlar
# Debe coincidir EXACTAMENTE con el título de la ventana
# Para Notepad en español puede ser "Sin título de bloc de notas" o "Untitled - Notepad"
ventana_objetivo = "Untitled - Notepad"

# ============================================
# PASO 2: CÓDIGO DEL PROGRAMA (NO MODIFICAR)
# ============================================

import time
from bcipydummies import BCIPipeline
from bcipydummies.sources. emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies. processors import ThresholdProcessor, CommandMapper
from bcipydummies.publishers. keyboard. windows import WindowsKeyboardPublisher
from bcipydummies.core.events import MentalCommand

def main():
    print("=" * 50)
    print("🧠 CONTROL DE NOTEPAD CON LA MENTE")
    print("=" * 50)
    
    # Verificar que las credenciales fueron configuradas
    if client_id == "tu_client_id_aqui": 
        print("\n❌ ERROR: No has configurado tus credenciales!")
        print("   Abre este archivo y edita las líneas:")
        print('   client_id = "tu_client_id_aqui"')
        print('   client_secret = "tu_client_secret_aqui"')
        print("\n   Reemplaza el texto entre comillas con tus credenciales reales.")
        return
    
    # Mostrar ventanas disponibles para ayudar al usuario
    print("\n📋 Ventanas disponibles en tu sistema:")
    print("-" * 40)
    ventanas = WindowsKeyboardPublisher.list_windows()
    for i, v in enumerate(ventanas[: 15]):  # Mostrar solo las primeras 15
        print(f"   {i+1}. {v}")
    print("-" * 40)
    print(f"\n🎯 Buscando ventana:  '{ventana_objetivo}'")
    
    # Verificar que la ventana existe
    if ventana_objetivo not in ventanas:
        print(f"\n❌ ERROR: No se encontró la ventana '{ventana_objetivo}'")
        print("   Asegúrate de que Notepad esté abierto.")
        print("   El nombre debe coincidir EXACTAMENTE (mayúsculas y minúsculas).")
        return
    
    print(f"✅ Ventana encontrada!")
    
    # Crear credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Crear la fuente (conexión con el headset)
    source = EmotivSource(
        credentials=credentials,
        streams=["com"]  # Solo comandos mentales
    )
    
    # Crear procesadores
    processors = [
        # Filtrar señales débiles (solo acepta señales fuertes)
        ThresholdProcessor(
            thresholds={
                "left": 0.6,    # 60% de potencia mínima
                "right": 0.6,
                "push": 0.6,
                "lift": 0.5,
            },
            default_threshold=0.5
        ),
        # Mapear comandos a teclas
        CommandMapper(
            mapping={
                "left": "A",
                "right": "D",
                "push": "W",
                "lift": "SPACE"
            }
        )
    ]
    
    # Crear el publicador de teclado
    keyboard = WindowsKeyboardPublisher(
        window_name=ventana_objetivo,
        command_mapping={
            MentalCommand.LEFT: "A",
            MentalCommand. RIGHT: "D",
            MentalCommand.PUSH: "W",
            MentalCommand.LIFT: "SPACE"
        }
    )
    
    # Crear el pipeline
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[keyboard]
    )
    
    # Instrucciones para el usuario
    print("\n" + "=" * 50)
    print("📝 INSTRUCCIONES:")
    print("=" * 50)
    print("   • Piensa 'LEFT'  → Escribe 'A'")
    print("   • Piensa 'RIGHT' → Escribe 'D'")
    print("   • Piensa 'PUSH'  → Escribe 'W'")
    print("   • Piensa 'LIFT'  → Escribe ESPACIO")
    print("\n   Presiona Ctrl+C para detener el programa")
    print("=" * 50)
    
    # Ejecutar
    try:
        with pipeline: 
            print("\n🚀 ¡Pipeline activo! Usa tus comandos mentales...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Programa detenido por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Verifica que Emotiv Cortex esté ejecutándose.")

if __name__ == "__main__":
    main()
```

---

## Ejemplo 2: Mover el Mouse con Comandos Mentales

**¿Qué hace?** Mueve el cursor del mouse en la pantalla usando tu mente.

| Comando Mental | Acción |
|----------------|--------|
| `left` | Mueve el mouse a la izquierda |
| `right` | Mueve el mouse a la derecha |
| `push` | Mueve el mouse hacia arriba |
| `lift` | Hace clic |

### Pasos:

1. Copia el código en un archivo llamado `mover_mouse.py`
2. Ejecuta: `python mover_mouse.py`

```python
"""
EJEMPLO 2: Mover el Mouse con la Mente
======================================
Este script mueve el cursor del mouse usando comandos mentales.
"""

# ============================================
# PASO 1: CONFIGURACIÓN - EDITA ESTA SECCIÓN
# ============================================

# Pon tus credenciales de Emotiv aquí (entre las comillas)
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"

# Cuántos píxeles mover el mouse por cada comando
# Número más alto = movimiento más rápido
pixeles_por_movimiento = 50

# ============================================
# PASO 2: CÓDIGO DEL PROGRAMA (NO MODIFICAR)
# ============================================

import time
import ctypes
from bcipydummies import BCIPipeline
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv. cortex_client import CortexCredentials
from bcipydummies.processors import ThresholdProcessor
from bcipydummies.publishers. base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent, MentalCommand


class MousePublisher(Publisher):
    """
    Publicador personalizado que mueve el mouse. 
    """
    
    def __init__(self, pixels=50):
        self._is_ready = False
        self. pixels = pixels
        self.comandos_ejecutados = 0
    
    def start(self):
        self._is_ready = True
        print("🖱️  Control de mouse iniciado!")
    
    def stop(self):
        self._is_ready = False
        print(f"🖱️  Control de mouse detenido.  Comandos ejecutados: {self.comandos_ejecutados}")
    
    @property
    def is_ready(self):
        return self._is_ready
    
    def publish(self, event:  EEGEvent):
        if not isinstance(event, MentalCommandEvent):
            return
        
        # Ignorar comandos neutrales
        if event.command == MentalCommand.NEUTRAL: 
            return
        
        # Obtener posición actual del mouse
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes. byref(pt))
        x, y = pt.x, pt. y
        
        # Calcular nueva posición según el comando
        if event.command == MentalCommand.LEFT:
            x -= self.pixels
            print(f"⬅️  Moviendo izquierda (potencia: {event.power:. 0%})")
        
        elif event.command == MentalCommand.RIGHT:
            x += self.pixels
            print(f"➡️  Moviendo derecha (potencia: {event.power:.0%})")
        
        elif event.command == MentalCommand.PUSH:
            y -= self.pixels
            print(f"⬆️  Moviendo arriba (potencia: {event.power:.0%})")
        
        elif event.command == MentalCommand.LIFT:
            # Hacer clic
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # Mouse down
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # Mouse up
            print(f"🖱️  ¡Clic! (potencia: {event.power:.0%})")
            self.comandos_ejecutados += 1
            return
        
        # Mover el mouse a la nueva posición
        ctypes.windll.user32.SetCursorPos(x, y)
        self.comandos_ejecutados += 1


def main():
    print("=" * 50)
    print("🖱️  CONTROL DE MOUSE CON LA MENTE")
    print("=" * 50)
    
    # Verificar credenciales
    if client_id == "tu_client_id_aqui":
        print("\n❌ ERROR: No has configurado tus credenciales!")
        print("   Abre este archivo y edita las líneas:")
        print('   client_id = "tu_client_id_aqui"')
        print('   client_secret = "tu_client_secret_aqui"')
        return
    
    # Crear credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Crear fuente
    source = EmotivSource(
        credentials=credentials,
        streams=["com"]
    )
    
    # Crear procesadores
    processors = [
        ThresholdProcessor(
            thresholds={
                "left": 0.5,
                "right": 0.5,
                "push":  0.5,
                "lift": 0.6,  # Clic requiere más potencia para evitar accidentes
            },
            default_threshold=0.5
        )
    ]
    
    # Crear publicador de mouse
    mouse = MousePublisher(pixels=pixeles_por_movimiento)
    
    # Crear pipeline
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[mouse]
    )
    
    # Instrucciones
    print("\n" + "=" * 50)
    print("📝 INSTRUCCIONES:")
    print("=" * 50)
    print("   • Piensa 'LEFT'  → Mueve mouse a la izquierda")
    print("   • Piensa 'RIGHT' → Mueve mouse a la derecha")
    print("   • Piensa 'PUSH'  → Mueve mouse hacia arriba")
    print("   • Piensa 'LIFT'  → Hace clic")
    print(f"\n   Velocidad: {pixeles_por_movimiento} píxeles por movimiento")
    print("\n   Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        with pipeline:
            print("\n🚀 ¡Control de mouse activo!")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n🛑 Programa detenido.")
    except Exception as e: 
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
```

---

## Ejemplo 3: Controlar YouTube (Play/Pausa/Siguiente)

**¿Qué hace?** Controla la reproducción de videos en YouTube usando comandos mentales. 

| Comando Mental | Acción |
|----------------|--------|
| `left` | Video anterior |
| `right` | Video siguiente |
| `push` | Subir volumen |
| `lift` | Play / Pausa |

### Pasos:

1. Abre YouTube en tu navegador (Chrome, Firefox, Edge)
2. Reproduce un video
3. Copia el código en `controlar_youtube.py`
4. Ejecuta: `python controlar_youtube.py`

```python
"""
EJEMPLO 3: Controlar YouTube con la Mente
=========================================
Controla la reproducción de videos usando comandos mentales. 
Funciona con YouTube en cualquier navegador.
"""

# ============================================
# PASO 1: CONFIGURACIÓN - EDITA ESTA SECCIÓN
# ============================================

# Pon tus credenciales de Emotiv aquí
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"

# Nombre del navegador (debe estar abierto con YouTube)
# Ejemplos comunes: 
#   "YouTube - Google Chrome"
#   "YouTube - Mozilla Firefox"  
#   "YouTube - Microsoft Edge"
# CONSEJO: Ejecuta el programa una vez para ver la lista de ventanas
nombre_navegador = "YouTube - Google Chrome"

# ============================================
# PASO 2: CÓDIGO DEL PROGRAMA (NO MODIFICAR)
# ============================================

import time
from bcipydummies import BCIPipeline
from bcipydummies. sources.emotiv import EmotivSource
from bcipydummies. sources.emotiv.cortex_client import CortexCredentials
from bcipydummies.processors import ThresholdProcessor, DebounceProcessor
from bcipydummies.publishers.keyboard.windows import WindowsKeyboardPublisher
from bcipydummies. core.events import MentalCommand


def main():
    print("=" * 50)
    print("🎬 CONTROL DE YOUTUBE CON LA MENTE")
    print("=" * 50)
    
    # Verificar credenciales
    if client_id == "tu_client_id_aqui":
        print("\n❌ ERROR:  Configura tus credenciales primero!")
        return
    
    # Mostrar ventanas
    print("\n📋 Ventanas disponibles:")
    print("-" * 40)
    ventanas = WindowsKeyboardPublisher.list_windows()
    youtube_ventanas = [v for v in ventanas if "youtube" in v.lower()]
    
    if youtube_ventanas:
        print("🎬 Ventanas con YouTube detectadas:")
        for v in youtube_ventanas:
            print(f"   ✓ {v}")
    else:
        print("⚠️  No se detectó YouTube abierto.")
        print("   Abre YouTube en tu navegador primero.")
    
    print("-" * 40)
    
    # Credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Fuente
    source = EmotivSource(credentials=credentials, streams=["com"])
    
    # Procesadores
    processors = [
        ThresholdProcessor(
            thresholds={
                "left": 0.6,
                "right": 0.6,
                "push":  0.5,
                "lift": 0.5,
            }
        ),
        # Evitar comandos repetidos muy rápido
        DebounceProcessor(cooldown=1.0)  # 1 segundo entre comandos
    ]
    
    # Mapeo de teclas para YouTube
    # K = Play/Pausa
    # J = Retroceder / Shift+P = Video anterior
    # L = Adelantar / Shift+N = Video siguiente  
    keyboard = WindowsKeyboardPublisher(
        window_name=nombre_navegador,
        command_mapping={
            MentalCommand. LEFT: "J",      # Retroceder 10 segundos
            MentalCommand.RIGHT: "L",     # Adelantar 10 segundos
            MentalCommand.PUSH: "UP",     # Subir volumen (flecha arriba)
            MentalCommand.LIFT: "K",      # Play/Pausa
        }
    )
    
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[keyboard]
    )
    
    # Instrucciones
    print("\n" + "=" * 50)
    print("📝 CONTROLES:")
    print("=" * 50)
    print("   • LEFT  → Retroceder 10 segundos")
    print("   • RIGHT → Adelantar 10 segundos")
    print("   • PUSH  → Subir volumen")
    print("   • LIFT  → Play / Pausa")
    print("\n   Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        with pipeline:
            print("\n🚀 ¡Control de YouTube activo!")
            print("   Asegúrate de que la ventana del navegador esté visible.\n")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Programa detenido.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
```

---

## Ejemplo 4: Jugar un Juego de Carreras

**¿Qué hace?** Controla un carro en juegos de carreras (funciona con muchos juegos que usen WASD o flechas).

| Comando Mental | Acción |
|----------------|--------|
| `left` | Girar a la izquierda |
| `right` | Girar a la derecha |
| `push` | Acelerar |
| `lift` | Frenar / Reversa |

### Pasos: 

1. Abre tu juego de carreras
2. Asegúrate de que use controles WASD o flechas
3. Copia el código en `juego_carreras.py`
4. Ejecuta: `python juego_carreras.py`

```python
"""
EJEMPLO 4: Jugar Juegos de Carreras con la Mente
================================================
Controla un carro en juegos usando comandos mentales.
Compatible con juegos que usen WASD o flechas. 
"""

# ============================================
# PASO 1: CONFIGURACIÓN - EDITA ESTA SECCIÓN
# ============================================

# Tus credenciales de Emotiv
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"

# Nombre EXACTO de la ventana del juego
# Ejecuta el programa una vez para ver las ventanas disponibles
nombre_juego = "Nombre de tu juego aquí"

# Tipo de controles del juego
# Opciones: "wasd" o "flechas"
tipo_controles = "wasd"

# ============================================
# PASO 2: CÓDIGO DEL PROGRAMA (NO MODIFICAR)
# ============================================

import time
from bcipydummies import BCIPipeline
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies. processors import ThresholdProcessor, DebounceProcessor
from bcipydummies.publishers.keyboard.windows import WindowsKeyboardPublisher
from bcipydummies.core. events import MentalCommand


def main():
    print("=" * 50)
    print("🏎️  CONTROL DE JUEGO DE CARRERAS")
    print("=" * 50)
    
    if client_id == "tu_client_id_aqui":
        print("\n❌ ERROR:  Configura tus credenciales primero!")
        return
    
    # Mostrar ventanas disponibles
    print("\n📋 Ventanas de juegos detectadas:")
    print("-" * 40)
    ventanas = WindowsKeyboardPublisher.list_windows()
    for v in ventanas[: 20]: 
        print(f"   • {v}")
    print("-" * 40)
    
    # Definir mapeo según tipo de controles
    if tipo_controles == "wasd": 
        mapeo = {
            MentalCommand.LEFT: "A",      # Izquierda
            MentalCommand.RIGHT: "D",     # Derecha
            MentalCommand.PUSH: "W",      # Acelerar
            MentalCommand. LIFT: "S",      # Frenar
        }
        print("\n🎮 Usando controles WASD")
    else: 
        mapeo = {
            MentalCommand.LEFT: "LEFT",   # Flecha izquierda
            MentalCommand.RIGHT: "RIGHT", # Flecha derecha
            MentalCommand.PUSH:  "UP",     # Flecha arriba
            MentalCommand.LIFT: "DOWN",   # Flecha abajo
        }
        print("\n🎮 Usando controles de FLECHAS")
    
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    source = EmotivSource(credentials=credentials, streams=["com"])
    
    processors = [
        ThresholdProcessor(
            thresholds={
                "left":  0.5,
                "right": 0.5,
                "push":  0.4,   # Acelerar más fácil
                "lift": 0.5,
            }
        ),
        DebounceProcessor(cooldown=0.2)  # Respuesta rápida para juegos
    ]
    
    keyboard = WindowsKeyboardPublisher(
        window_name=nombre_juego,
        command_mapping=mapeo
    )
    
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[keyboard]
    )
    
    print("\n" + "=" * 50)
    print("🎮 CONTROLES:")
    print("=" * 50)
    print("   • LEFT  → Girar izquierda")
    print("   • RIGHT → Girar derecha")
    print("   • PUSH  → Acelerar")
    print("   • LIFT  → Frenar")
    print("\n   Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        with pipeline:
            print("\n🚀 ¡A correr!  Controles activos.")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Juego pausado.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
```

---

## Ejemplo 5: Control de Presentaciones PowerPoint

**¿Qué hace?** Controla una presentación de PowerPoint sin usar las manos.

| Comando Mental | Acción |
|----------------|--------|
| `left` | Diapositiva anterior |
| `right` | Diapositiva siguiente |
| `push` | Iniciar presentación |
| `lift` | Terminar presentación |

### Pasos:

1. Abre PowerPoint con tu presentación
2. Copia el código en `controlar_powerpoint.py`
3. Ejecuta: `python controlar_powerpoint.py`

```python
"""
EJEMPLO 5: Controlar PowerPoint con la Mente
============================================
Navega por tus presentaciones usando comandos mentales. 
¡Perfecto para presentaciones manos libres!
"""

# ============================================
# PASO 1: CONFIGURACIÓN - EDITA ESTA SECCIÓN
# ============================================

# Tus credenciales de Emotiv
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"

# Nombre de la ventana de PowerPoint
# Generalmente es "Nombre del archivo - PowerPoint"
# Ejemplo: "Mi Presentación. pptx - PowerPoint"
nombre_powerpoint = "PowerPoint"

# ============================================
# PASO 2: CÓDIGO DEL PROGRAMA (NO MODIFICAR)
# ============================================

import time
from bcipydummies import BCIPipeline
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv.cortex_client import CortexCredentials
from bcipydummies. processors import ThresholdProcessor, DebounceProcessor
from bcipydummies.publishers.keyboard.windows import WindowsKeyboardPublisher
from bcipydummies.core. events import MentalCommand


def main():
    print("=" * 50)
    print("📊 CONTROL DE POWERPOINT CON LA MENTE")
    print("=" * 50)
    
    if client_id == "tu_client_id_aqui":
        print("\n❌ ERROR: Configura tus credenciales primero!")
        return
    
    # Buscar PowerPoint
    print("\n📋 Buscando PowerPoint...")
    ventanas = WindowsKeyboardPublisher. list_windows()
    ppt_ventanas = [v for v in ventanas if "powerpoint" in v.lower() or "pptx" in v.lower()]
    
    if ppt_ventanas:
        print("✅ PowerPoint detectado:")
        for v in ppt_ventanas:
            print(f"   • {v}")
        # Usar la primera ventana de PowerPoint encontrada
        nombre_powerpoint_final = ppt_ventanas[0]
    else:
        print("⚠️  No se detectó PowerPoint abierto.")
        print("   Abre una presentación en PowerPoint primero.")
        nombre_powerpoint_final = nombre_powerpoint
    
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    source = EmotivSource(credentials=credentials, streams=["com"])
    
    processors = [
        ThresholdProcessor(
            thresholds={
                "left": 0.6,
                "right": 0.6,
                "push": 0.7,   # Mayor potencia para iniciar presentación
                "lift": 0.7,   # Mayor potencia para terminar
            }
        ),
        DebounceProcessor(cooldown=1.5)  # 1.5 segundos entre comandos (evita cambios accidentales)
    ]
    
    # Atajos de teclado de PowerPoint
    keyboard = WindowsKeyboardPublisher(
        window_name=nombre_powerpoint_final,
        command_mapping={
            MentalCommand.LEFT: "LEFT",    # Diapositiva anterior
            MentalCommand.RIGHT: "RIGHT",  # Diapositiva siguiente
            MentalCommand.PUSH: "F5",      # Iniciar presentación
            MentalCommand.LIFT:  "ESCAPE",  # Terminar presentación
        }
    )
    
    pipeline = BCIPipeline(
        source=source,
        processors=processors,
        publishers=[keyboard]
    )
    
    print("\n" + "=" * 50)
    print("📝 CONTROLES:")
    print("=" * 50)
    print("   • LEFT  → Diapositiva anterior")
    print("   • RIGHT → Diapositiva siguiente")
    print("   • PUSH  → Iniciar presentación (F5)")
    print("   • LIFT  → Terminar presentación (ESC)")
    print("\n   ⏱️  Hay 1.5 segundos entre comandos para evitar")
    print("       cambios accidentales.")
    print("\n   Presiona Ctrl+C para detener")
    print("=" * 50)
    
    try:
        with pipeline:
            print("\n🚀 ¡Control de PowerPoint activo!")
            print("   Puedes empezar tu presentación.\n")
            while True: 
                time.sleep(1)
    except KeyboardInterrupt: 
        print("\n🛑 Control detenido.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
```

---

## 🆘 Solución de Problemas Comunes

### "No se encontró la ventana"

El nombre debe coincidir **EXACTAMENTE**.  Ejecuta cualquier ejemplo y mira la lista de ventanas disponibles.

### "Error de credenciales"

Asegúrate de: 
1. Poner tus credenciales entre comillas:  `client_id = "abc123"`
2. No dejar espacios extra
3. Copiar el Client ID y Client Secret correctos desde emotiv.com/developer

### "No se detectan comandos"

1. Verifica que Emotiv Cortex esté ejecutándose
2. Verifica que el headset esté conectado (luz verde)
3. Asegúrate de haber entrenado los comandos en EmotivBCI

### "Los comandos se disparan solos"

Aumenta el umbral de potencia en `ThresholdProcessor`. Cambia de `0.5` a `0.7` o `0.8`.

---

## Documentación Relacionada

- **[Deep Dive](../deep-dive/deep-dive.md)** - Arquitectura completa del sistema
- **[Instalación](../getting-started/installation.md)** - Cómo instalar BCIpyDummies
- **[Configuración Hardware](../hardware/emotiv-setup.md)** - Configurar tu headset Emotiv