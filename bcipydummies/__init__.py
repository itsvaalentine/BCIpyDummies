"""
BCIPyDummies – Librería simple y moderna para conectar Emotiv BCI con videojuegos,
interfaces interactivas y sistemas de control.

Este paquete provee una arquitectura modular que incluye:

- Conexión WebSocket a Emotiv Cortex API (`cortex.websocket_client`)
- Manejo de sesión, tokens y subscripciones (`cortex.session_manager`)
- Mapeo de acciones mentales a controles (`control.action_mapper`)
- Control directo de ventanas por Win32 (`control.window_control`)
- Controlador unificado de alto nivel (`core.emotiv_controller`)
- CLI opcional para ejecutar el sistema desde terminal (`cli.main`)

La idea del proyecto es facilitar el uso de Emotiv BCI como middleware
en videojuegos, proyectos creativos, accesibilidad e interfaces neuronales.
"""

# Exponer la API pública del paquete
from .core.emotiv_controller import EmotivController

# Información del paquete
__all__ = ["EmotivController"]
__version__ = "0.1.0"
