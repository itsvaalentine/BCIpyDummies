# Guía de Inicio Rápido

Pon BCIpyDummies en funcionamiento en 5 minutos. 

## Lista de Verificación de Prerrequisitos

Antes de comenzar, asegúrate de tener:

- [ ] Python 3.9+ instalado
- [ ] BCIpyDummies instalado (`pip install -e .`)
- [ ] App Emotiv Cortex ejecutándose
- [ ] Headset Emotiv conectado a Cortex
- [ ] Comandos mentales entrenados en la app EmotivBCI
- [ ] Credenciales API establecidas como variables de entorno

## Paso 1: Encuentra Tu Ventana Objetivo

Primero, identifica el nombre exacto de la ventana que quieres controlar:

```python
from bcipydummies.emotiv_controller import EmotivController

# Listar todas las ventanas visibles
windows = EmotivController.list_windows()

for window in windows:
    print(window)
```

Salida de ejemplo: 
```
Google Chrome
Visual Studio Code
Notepad
... 
```

Copia el nombre exacto de la ventana que quieres controlar.

## Paso 2: Crea el Controlador

```python
from bcipydummies. emotiv_controller import EmotivController

# Reemplaza con el nombre real de tu ventana
controller = EmotivController("Notepad")
```

Esto hará: 
1. Buscar la ventana por nombre
2. Traerla al primer plano
3. Preparar para simulación de teclado

## Paso 3: Conecta a Emotiv

```python
# Iniciar la conexión (corre en hilo de fondo)
thread = controller.connect()

print("¡Conectado!  Usa comandos mentales para controlar la ventana.")
print("Presiona Ctrl+C para detener.")
```

## Paso 4: Usa Comandos Mentales

Una vez conectado, tus comandos mentales entrenados activarán entradas de teclado:

| Comando Mental | Acción de Teclado |
|----------------|-------------------|
| `left` (80%+ potencia) | Presionar tecla 'A' |
| `right` | Presionar tecla 'D' (mantenida 200ms) |
| `lift` | Presionar 'SPACE' + última dirección |

## Paso 5: Limpieza

Cuando termines: 

```python
controller.close()
```

## Ejemplo Completo

```python
from bcipydummies.emotiv_controller import EmotivController
import time

def main():
    # Encontrar ventanas disponibles
    print("Ventanas disponibles:")
    for window in EmotivController.list_windows()[:10]: 
        print(f"  - {window}")

    # Conectar a ventana objetivo
    window_name = input("\nIngresa nombre de ventana: ")
    controller = EmotivController(window_name)

    print(f"\nConectando a '{window_name}'...")
    thread = controller.connect()

    print("¡Conectado! Los comandos mentales ahora están activos.")
    print("Comandos:  left->A, right->D, lift->SPACE")
    print("Presiona Ctrl+C para detener.\n")

    try:
        # Mantener ejecutándose hasta interrupción
        while True: 
            time.sleep(1)
    except KeyboardInterrupt: 
        print("\nApagando...")
        controller.close()
        print("¡Listo!")

if __name__ == "__main__":
    main()
```

## Qué Está Pasando

1. **Conexión WebSocket**: BCIpyDummies se conecta a Emotiv Cortex en `wss://127.0.0.1:6868`
2. **Autenticación**: Intercambia credenciales por un token de sesión
3. **Creación de Sesión**: Crea una sesión con tu headset conectado
4. **Suscripción a Stream**: Se suscribe al stream `com` (comando mental)
5. **Procesamiento de Comandos**: Cuando llegan comandos, se traducen a pulsaciones de teclas

## Solución de Problemas

### "Ventana no encontrada"

El nombre de ventana debe coincidir exactamente (sensible a mayúsculas). Usa `list_windows()` para ver nombres exactos.

### No Se Detectan Comandos

1. Verifica que Emotiv Cortex muestre estado "Streaming"
2. Verifica que los comandos mentales estén entrenados en EmotivBCI
3. Asegúrate de que la calidad de contacto del headset sea buena (indicadores verdes)

### Los Comandos Se Disparan Muy Seguido/Poco

Los umbrales de potencia actuales son:
- `left`: 80% (solo se dispara con señal fuerte)
- `right`: 0% (se dispara fácilmente)
- `lift`: 0% (se dispara fácilmente)

Estos están hardcodeados en la versión actual.  La personalización requiere modificar `emotiv_controller.py`.

## Próximos Pasos

- [Guía de Configuración Emotiv](../hardware/emotiv-setup.md) - Optimiza la configuración de tu headset
- [Referencia API](../api/emotiv-controller.md) - Documentación completa de métodos
- [Solución de Problemas](../user-guide/troubleshooting. md) - Problemas comunes y soluciones