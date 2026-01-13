# Documentación de BCIpyDummies

**Librería middleware para conectar headsets EEG Emotiv con aplicaciones de Windows mediante comandos mentales.**

## ¿Qué es BCIpyDummies?

BCIpyDummies actúa como un traductor entre tu cerebro y tu computadora.  Se conecta a headsets EEG Emotiv a través de la API Cortex y convierte comandos mentales en entradas de teclado para cualquier aplicación de Windows.

**Casos de uso:**
- Controlar juegos con tu mente
- Control de aplicaciones manos libres
- Investigación y experimentación BCI
- Soluciones de accesibilidad

## Enlaces Rápidos

| Sección | Descripción |
|---------|-------------|
| [Instalación](getting-started/installation.md) | Requisitos del sistema y configuración |
| [Inicio Rápido](getting-started/quickstart.md) | Empieza a funcionar en 5 minutos |
| [Configuración Emotiv](hardware/emotiv-setup.md) | Guía de configuración del hardware |
| [Referencia API](api/emotiv-controller.md) | Documentación de clases y métodos |
| [Diseño del Sistema](architecture/system-design.md) | Vista general del diseño del sistema |
| [Deep Dive](deep-dive/deep-dive.md) | 🧠 Documentación completa de arquitectura |

## Características Actuales

- Conexión WebSocket a la API Emotiv Cortex
- Procesamiento de comandos mentales (left, right, lift)
- Simulación de teclado para aplicaciones de Windows
- Utilidad de enumeración de ventanas

## Requisitos

- Windows 10/11
- Python 3.9+
- Headset EEG Emotiv
- App Emotiv Cortex

## Primeros Pasos

```python
from bcipydummies. emotiv_controller import EmotivController

# Encontrar tu ventana objetivo
windows = EmotivController.list_windows()
print(windows)

# Empezar a controlar
controller = EmotivController("Nombre de tu Ventana")
controller.connect()
```

## Estado del Proyecto

BCIpyDummies está en desarrollo activo (v0.1.0). Enfoque actual:
- Mejoras de documentación
- Refactorización de arquitectura para extensibilidad
- Planificación de soporte multiplataforma

## Contribuir

¡Damos la bienvenida a contribuciones!  Consulta nuestra [Guía de Contribución](contributing/index.md) para más detalles.

## Soporte

- [GitHub Issues](https://github.com/itsvaalentine/BCIpyDummies/issues) - Reportes de bugs y solicitudes de funciones
- [GitHub Discussions](https://github.com/itsvaalentine/BCIpyDummies/discussions) - Preguntas y comunidad