# 🧪 Ejemplos Prácticos

Esta guía contiene ejemplos de código prácticos para usar BCIpyDummies.  Cada ejemplo es independiente y puede ejecutarse por separado.

## 📋 Índice

1. [Ejemplo 1: Uso Básico con MockSource](#ejemplo-1-uso-básico-con-mocksource-sin-hardware)
2. [Ejemplo 2: Pipeline Completo con Procesadores](#ejemplo-2-pipeline-completo-con-procesadores)
3. [Ejemplo 3: Secuencia de Eventos Scripted](#ejemplo-3-secuencia-de-eventos-scripted)
4. [Ejemplo 4: Publicador Personalizado](#ejemplo-4-crear-un-publicador-personalizado)
5. [Ejemplo 5: Procesador Personalizado](#ejemplo-5-crear-un-procesador-personalizado)
6. [Ejemplo 6: Configuración con Factory](#ejemplo-6-uso-con-factory-configuración-simplificada)
7. [Ejemplo 7: Control de Ventana Real](#ejemplo-7-control-de-ventana-real-windows)
8. [Ejemplo 8: Hardware Real Emotiv](#ejemplo-8-uso-con-hardware-real-emotiv)

> 💡 **¿Nuevo en BCIpyDummies? ** Empieza con la [Guía Deep Dive](deep-dive.md) para entender la arquitectura primero.

---

## Ejemplo 1: Uso Básico con MockSource (Sin Hardware)

```python
"""
Este ejemplo funciona sin hardware Emotiv.
Perfecto para probar la librería. 
"""
import time
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher
from bcipydummies.core. events import MentalCommand

# Crear fuente simulada que genera eventos aleatorios
source = MockSource(
    source_id="test-source",
    random_interval=1.0,  # Un evento cada segundo
    random_commands=[
        MentalCommand.LEFT,
        MentalCommand. RIGHT,
        MentalCommand.PUSH,
        MentalCommand.NEUTRAL,
    ]
)

# Crear publicador de consola
console = ConsolePublisher(prefix="[BCI]")

# Crear y ejecutar el pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[console]
)

# Usar como context manager
with pipeline:
    print("Pipeline iniciado. Presiona Ctrl+C para detener.")
    try:
        time.sleep(10)  # Ejecutar por 10 segundos
    except KeyboardInterrupt: 
        pass

print("Pipeline detenido.")
print(f"Estadísticas: {pipeline.statistics}")
```

---

## Ejemplo 2: Pipeline Completo con Procesadores

```python
"""
Ejemplo con cadena de procesadores.
"""
from bcipydummies import (
    BCIPipeline,
    MockSource,
    ConsolePublisher,
    ThresholdProcessor,
    DebounceProcessor,
    CommandMapper
)

# Fuente simulada
source = MockSource()

# Cadena de procesadores
processors = [
    # 1. Filtrar por umbral de potencia
    ThresholdProcessor(
        thresholds={
            "left": 0.7,   # Solo left con 70%+ potencia
            "right": 0.6,  # Solo right con 60%+ potencia
        },
        default_threshold=0.5
    ),
    
    # 2. Evitar comandos repetidos
    DebounceProcessor(cooldown=0.3),  # 300ms entre comandos
    
    # 3. Mapear comandos a teclas
    CommandMapper(
        mapping={
            "left": "A",
            "right": "D",
            "push": "W",
            "lift": "SPACE"
        }
    )
]

# Publicadores
publishers = [ConsolePublisher(prefix="[EVENTO]")]

# Crear pipeline
pipeline = BCIPipeline(
    source=source,
    processors=processors,
    publishers=publishers
)

# Ejecutar
with pipeline:
    import time
    time.sleep(30)
```

---

## Ejemplo 3: Secuencia de Eventos Scripted

```python
"""
Ejemplo con secuencia predefinida de eventos. 
Útil para pruebas reproducibles.
"""
from bcipydummies. sources.mock import MockSource, ScriptedEvent, create_test_script
from bcipydummies.core.events import MentalCommand
from bcipydummies import BCIPipeline, ConsolePublisher

# Crear script de eventos
script = create_test_script(
    commands=["neutral", "left", "left", "right", "push", "neutral"],
    interval=0.5,  # 500ms entre eventos
    power=0.85
)

# Fuente con script
source = MockSource(script=script, loop_script=False)

# Pipeline
pipeline = BCIPipeline(
    source=source,
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time.sleep(5)  # Esperar que termine el script
```

---

## Ejemplo 4: Crear un Publicador Personalizado

```python
"""
Ejemplo de cómo crear tu propio publicador.
"""
from bcipydummies. publishers.base import Publisher
from bcipydummies.core.events import EEGEvent, MentalCommandEvent

class MiPublicador(Publisher):
    """Publicador personalizado que cuenta eventos por comando."""
    
    def __init__(self):
        self._is_ready = False
        self. contadores = {}
    
    def start(self) -> None:
        self._is_ready = True
        self.contadores = {}
        print("MiPublicador iniciado!")
    
    def stop(self) -> None:
        self._is_ready = False
        print(f"MiPublicador detenido. Contadores: {self.contadores}")
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event:  EEGEvent) -> None:
        if isinstance(event, MentalCommandEvent):
            cmd = event.command.name
            self.contadores[cmd] = self.contadores.get(cmd, 0) + 1
            print(f"Comando {cmd} detectado ({self.contadores[cmd]} veces)")


# Usar el publicador personalizado
from bcipydummies import BCIPipeline, MockSource

source = MockSource()
mi_pub = MiPublicador()

with BCIPipeline(source=source, publishers=[mi_pub]):
    import time
    time. sleep(10)
```

---

## Ejemplo 5: Crear un Procesador Personalizado

```python
"""
Ejemplo de procesador personalizado que filtra comandos NEUTRAL.
"""
from bcipydummies.processors.base import Processor
from bcipydummies. core.events import EEGEvent, MentalCommandEvent, MentalCommand
from typing import Optional

class FiltrarNeutral(Processor):
    """Filtra todos los eventos NEUTRAL."""
    
    def process(self, event: EEGEvent) -> Optional[EEGEvent]:
        if isinstance(event, MentalCommandEvent):
            if event.command == MentalCommand.NEUTRAL: 
                return None  # Filtrar
        return event  # Pasar el resto
    
    def reset(self) -> None:
        pass  # No tiene estado


# Usar el procesador
from bcipydummies import BCIPipeline, MockSource, ConsolePublisher

pipeline = BCIPipeline(
    source=MockSource(),
    processors=[FiltrarNeutral()],
    publishers=[ConsolePublisher()]
)

with pipeline:
    import time
    time. sleep(10)
```

---

## Ejemplo 6: Uso con Factory (Configuración Simplificada)

```python
"""
Uso de funciones factory para crear pipelines desde configuración.
"""
from bcipydummies import create_pipeline, Config, ThresholdConfig, KeyboardConfig, EmotivConfig

# Crear configuración
config = Config(
    emotiv=EmotivConfig(
        client_id="tu_client_id",
        client_secret="tu_client_secret"
    ),
    thresholds=ThresholdConfig(
        default=0.5,
        left=0.8,
        right=0.6
    ),
    keyboard=KeyboardConfig(
        left="a",
        right="d",
        lift="space"
    ),
    target_window="Notepad"
)

# Crear pipeline con factory
# Usa "simulated" en lugar de "emotiv" para pruebas sin hardware
pipeline = create_pipeline(config, source_type="simulated")

with pipeline:
    input("Presiona Enter para detener...")
```

---

## Ejemplo 7: Control de Ventana Real (Windows)

```python
"""
Ejemplo real controlando una ventana de Windows. 
NOTA: Requiere Windows y la aplicación target abierta.
"""
from bcipydummies import BCIPipeline, MockSource, ThresholdProcessor, CommandMapper
from bcipydummies. publishers.keyboard. windows import WindowsKeyboardPublisher
from bcipydummies.core.events import MentalCommand

# Listar ventanas disponibles
print("Ventanas disponibles:")
for window in WindowsKeyboardPublisher. list_windows()[: 20]:
    print(f"  - {window}")

# Configurar
target_window = "Notepad"  # Cambia esto por tu ventana

# Fuente simulada para pruebas
source = MockSource()

# Procesadores
processors = [
    ThresholdProcessor(thresholds={"left": 0.7, "right": 0.7}),
    CommandMapper(mapping={
        "left": "A",
        "right": "D", 
        "push": "W",
        "lift": "SPACE"
    })
]

# Publisher de teclado
keyboard = WindowsKeyboardPublisher(
    window_name=target_window,
    command_mapping={
        MentalCommand.LEFT: "A",
        MentalCommand. RIGHT: "D",
        MentalCommand.PUSH: "W",
        MentalCommand.LIFT: "SPACE"
    }
)

# Pipeline
pipeline = BCIPipeline(
    source=source,
    processors=processors,
    publishers=[keyboard]
)

try:
    with pipeline:
        print(f"Controlando '{target_window}'...")
        print("Presiona Ctrl+C para detener.")
        import time
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    print("\nDetenido.")
```

---

## Ejemplo 8: Uso con Hardware Real Emotiv

```python
"""
Ejemplo de uso con hardware REAL Emotiv.
Muestra los comandos mentales recibidos del dispositivo en tiempo real. 

REQUISITOS:
- Emotiv Cortex app ejecutándose
- Headset Emotiv conectado y configurado
- Comandos mentales entrenados en EmotivBCI
- Credenciales de desarrollador (client_id, client_secret)
"""
import os
import time
from datetime import datetime

from bcipydummies import BCIPipeline, ConsolePublisher
from bcipydummies.sources.emotiv import EmotivSource
from bcipydummies.sources.emotiv. cortex_client import CortexCredentials
from bcipydummies. core.events import MentalCommandEvent, ConnectionEvent, EEGEvent
from bcipydummies.publishers.base import Publisher


class MonitorPublisher(Publisher):
    """
    Publisher personalizado para mostrar información detallada
    de los comandos recibidos del hardware Emotiv.
    """
    
    def __init__(self):
        self._is_ready = False
        self.total_eventos = 0
        self.comandos_por_tipo = {}
        self.ultimo_comando = None
        self. hora_inicio = None
    
    def start(self) -> None:
        self._is_ready = True
        self.hora_inicio = datetime.now()
        print("=" * 60)
        print("🧠 MONITOR DE COMANDOS EMOTIV - INICIADO")
        print("=" * 60)
        print(f"⏰ Inicio: {self.hora_inicio. strftime('%H:%M:%S')}")
        print("-" * 60)
    
    def stop(self) -> None:
        self._is_ready = False
        duracion = datetime.now() - self.hora_inicio if self.hora_inicio else None
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE SESIÓN")
        print("=" * 60)
        print(f"⏱️  Duración: {duracion}")
        print(f"📈 Total eventos: {self.total_eventos}")
        print("\n📋 Comandos por tipo:")
        for cmd, count in sorted(self.comandos_por_tipo.items()):
            porcentaje = (count / self. total_eventos * 100) if self.total_eventos > 0 else 0
            print(f"   • {cmd}: {count} ({porcentaje:.1f}%)")
        print("=" * 60)
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    def publish(self, event: EEGEvent) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S. %f")[:-3]
        
        if isinstance(event, ConnectionEvent):
            estado = "✅ CONECTADO" if event.connected else "❌ DESCONECTADO"
            print(f"[{timestamp}] {estado}:  {event.message or ''}")
            
        elif isinstance(event, MentalCommandEvent):
            self.total_eventos += 1
            cmd_name = event.command.name
            self.comandos_por_tipo[cmd_name] = self.comandos_por_tipo.get(cmd_name, 0) + 1
            
            # Barra de potencia visual
            potencia_porcentaje = event.power * 100
            barras = int(potencia_porcentaje / 5)  # 20 barras máximo
            barra_visual = "█" * barras + "░" * (20 - barras)
            
            # Emoji según el comando
            emojis = {
                "NEUTRAL": "😐",
                "PUSH": "👊",
                "PULL": "🤚",
                "LIFT": "⬆️",
                "DROP": "⬇️",
                "LEFT": "⬅️",
                "RIGHT": "➡️",
                "ROTATE_LEFT": "↪️",
                "ROTATE_RIGHT": "↩️",
                "DISAPPEAR": "👻"
            }
            emoji = emojis.get(cmd_name, "🧠")
            
            print(f"[{timestamp}] {emoji} {cmd_name: 12} [{barra_visual}] {potencia_porcentaje: 5.1f}%")
            
            # Guardar último comando no-neutral
            if cmd_name != "NEUTRAL":
                self.ultimo_comando = (cmd_name, event.power)


def main():
    """
    Función principal para conectar con hardware Emotiv real.
    """
    print("\n🔧 Configurando conexión con Emotiv...")
    
    # Obtener credenciales de variables de entorno
    client_id = os.environ.get("EMOTIV_CLIENT_ID")
    client_secret = os.environ.get("EMOTIV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERROR: Configura las variables de entorno:")
        print("   export EMOTIV_CLIENT_ID='tu_client_id'")
        print("   export EMOTIV_CLIENT_SECRET='tu_client_secret'")
        return
    
    # Crear credenciales
    credentials = CortexCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Crear fuente Emotiv
    source = EmotivSource(
        credentials=credentials,
        streams=["com"]  # Solo comandos mentales
    )
    
    # Crear publisher monitor
    monitor = MonitorPublisher()
    
    # Crear pipeline
    pipeline = BCIPipeline(
        source=source,
        publishers=[monitor]
    )
    
    print("🚀 Iniciando pipeline...")
    print("💡 Tip:  Asegúrate de que tu headset está conectado en Emotiv Cortex")
    print()
    
    try:
        with pipeline:
            print("Pipeline ejecutándose.  Presiona Ctrl+C para detener.\n")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo...")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
```

---

## Documentación Relacionada

- **[Guía Deep Dive](deep-dive.md)** - Explicación completa de la arquitectura
- **[Inicio Rápido](../getting-started/quickstart.md)** - Guía de configuración rápida
- **[Referencia API](../api/emotiv-controller.md)** - Documentación de la API
- **[Configuración Hardware](../hardware/emotiv-setup.md)** - Configuración de Emotiv