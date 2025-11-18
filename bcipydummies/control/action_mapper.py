class ActionMapper:
    """
    Convierte acciones mentales en teclas.
    Solo asigna teclas, no maneja potencia.
    """

    MAP = {
        "left": "A",
        "right": "D",
        "lift": "SPACE"
    }

    @staticmethod
    def map(action: str):
        """Devuelve la tecla asociada o None si la acción no existe."""
        return ActionMapper.MAP.get(action, None)
