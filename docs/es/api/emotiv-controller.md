# Referencia API de EmotivController

Documentación completa de la API para la clase `EmotivController`.

## Módulo

```python
from bcipydummies. emotiv_controller import EmotivController
```

## Clase: EmotivController

La clase controladora principal que gestiona las conexiones del headset Emotiv y la simulación de teclado.

### Constructor

```python
EmotivController(window_name: str)
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `window_name` | `str` | Nombre exacto de la ventana objetivo |

**Excepciones:**

- `RuntimeError`: Si la ventana especificada no se encuentra

**Comportamiento:**

1. Busca una ventana que coincida con `window_name`
2. Almacena el handle de la ventana (`hwnd`)
3. Trae la ventana al primer plano
4. Inicializa los parámetros de conexión WebSocket

**Ejemplo:**

```python
# Lanzará RuntimeError si la ventana "Notepad" no existe
controller = EmotivController("Notepad")
```

### Métodos Estáticos

#### list_windows()

```python
@staticmethod
list_windows() -> List[str]
```

Enumera todas las ventanas visibles en el sistema.

**Retorna:** Lista de strings con títulos de ventanas

**Ejemplo:**

```python
windows = EmotivController.list_windows()
for window in windows:
    print(window)
```

**Notas:**

- Solo retorna ventanas que son visibles
- Solo retorna ventanas con títulos no vacíos
- Usa la API Win32 `EnumWindows`

### Métodos de Instancia

#### connect()

```python
connect() -> threading.Thread
```

Establece una conexión WebSocket a la API Emotiv Cortex.

**Retorna:** El hilo en segundo plano ejecutando la conexión WebSocket

**Comportamiento:**

1. Crea conexión WebSocket a `wss://127.0.0.1:6868`
2. Inicia el flujo de autenticación
3. Crea sesión con el headset conectado
4. Se suscribe al stream de comandos mentales
5. Comienza a procesar comandos

**Ejemplo:**

```python
controller = EmotivController("Mi App")
thread = controller.connect()

# La conexión corre en segundo plano
# El hilo principal puede continuar
```

**Notas:**

- Retorna inmediatamente; la conexión ocurre asincrónicamente
- El hilo retornado no es un hilo daemon
- Usa `close()` para detener la conexión

#### close()

```python
close() -> None
```

Cierra la conexión WebSocket. 

**Comportamiento:**

1. Llama a `ws_app.close()` para terminar el WebSocket
2. El hilo en segundo plano terminará

**Ejemplo:**

```python
controller. connect()
# ...  usar el controlador ...
controller.close()
```

### Atributos de Instancia

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `window_name` | `str` | Nombre de la ventana objetivo |
| `hwnd` | `int` | Handle de ventana Win32 |
| `cortex_token` | `str` | Token de autenticación (establecido después de connect) |
| `headset_id` | `str` | ID del headset conectado (establecido después de connect) |
| `session_id` | `str` | ID de sesión activa (establecido después de connect) |
| `ws_app` | `WebSocketApp` | Instancia de aplicación WebSocket |
| `lastMove` | `str` | Último comando direccional ('A' o 'D') |

### Procesamiento de Comandos Mentales

El controlador procesa estos comandos mentales:

| Comando | Umbral de Potencia | Acción de Tecla |
|---------|-------------------|-----------------|
| `left` | >= 0.80 | Presionar 'A' (50ms) |
| `right` | >= 0.00 | Presionar 'D' (200ms) |
| `lift` | >= 0.00 | Presionar 'SPACE' (450ms) + última dirección (20ms) |

### Códigos de Teclas Virtuales Soportados

El controlador soporta estas teclas: 

```python
VK_CODES = {
    'A': 0x41,
    'S': 0x53,
    'D': 0x44,
    'W': 0x57,
    'SPACE': 0x20
}
```

### Manejo de Errores

El controlador imprime errores a stdout pero no lanza excepciones durante la operación: 

- Errores WebSocket:  Impresos vía `_on_error`
- Cierre de conexión: Registrado vía `_on_close`
- Teclas inválidas: Advertencia impresa, operación omitida

### Seguridad de Hilos

- El controlador usa un único hilo en segundo plano para operaciones WebSocket
- La simulación de teclado ocurre en el hilo WebSocket
- El handle de ventana se almacena en el momento de construcción
- No se usan locks; evita modificar el estado del controlador desde múltiples hilos

## Ejemplo Completo

```python
from bcipydummies.emotiv_controller import EmotivController
import time
import signal
import sys

def main():
    # Configuración
    controller = EmotivController("Aplicación Objetivo")

    # Manejador de apagado elegante
    def shutdown(sig, frame):
        print("Apagando...")
        controller.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Conectar y ejecutar
    thread = controller.connect()
    print(f"Conectado a ventana: {controller.window_name}")
    print(f"Handle de ventana: {controller.hwnd}")

    # Mantener ejecutándose
    while True: 
        time.sleep(1)

if __name__ == "__main__":
    main()
```

## Limitaciones Conocidas

1. **Solo Windows**: Usa `win32gui` y `win32con`
2. **Umbrales Hardcodeados**: Los umbrales de potencia no pueden configurarse
3. **Teclas Limitadas**: Solo 5 teclas soportadas
4. **Sin Reconexión**:  Fallos de conexión requieren reinicio
5. **Credenciales Placeholder**: Las credenciales por defecto en el código deben reemplazarse

## Relacionado

- [Guía de Instalación](../getting-started/installation.md)
- [Inicio Rápido](../getting-started/quickstart.md)
- [Arquitectura](../architecture/system-design.md) 