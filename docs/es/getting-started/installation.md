# Guía de Instalación

Esta guía te lleva a través de la instalación de BCIpyDummies y sus dependencias.

## Requisitos del Sistema

| Requisito | Detalles |
|-----------|----------|
| **Sistema Operativo** | Windows 10 o Windows 11 |
| **Python** | 3.9 o superior |
| **Hardware** | Headset EEG Emotiv (EPOC X, EPOC+, Insight) |
| **Software** | App Emotiv Cortex instalada |

## Prerrequisitos

### 1. Instalación de Python

Asegúrate de que Python 3.9+ esté instalado:

```bash
python --version
```

Si no está instalado, descárgalo de [python.org](https://www.python.org/downloads/).

### 2. App Emotiv Cortex

Descarga e instala la app Emotiv Cortex:

1. Visita [emotiv.com/emotiv-cortex](https://www.emotiv.com/emotiv-cortex/)
2. Descarga el instalador para Windows
3. Ejecuta el instalador
4. Inicia Cortex e inicia sesión con tu cuenta Emotiv

### 3. Credenciales de Desarrollador Emotiv

Necesitas credenciales API para conectarte a Cortex:

1. Ve a [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Inicia sesión o crea una cuenta
3. Crea una nueva aplicación
4. Copia tu `Client ID` y `Client Secret`

## Métodos de Instalación

### Instalación de Desarrollo (Recomendado)

Clona e instala en modo editable:

```bash
# Clonar el repositorio
git clone https://github.com/itsvaalentine/BCIpyDummies. git
cd BCIpyDummies

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows

# Instalar en modo desarrollo
pip install -e . 
```

### Dependencias Instaladas

La instalación incluye:

| Paquete | Propósito |
|---------|-----------|
| `websocket-client` | Comunicación WebSocket con API Cortex |
| `pywin32` | API Windows para simulación de teclado |

## Configuración

### Establecer Credenciales API

**Opción 1: Variables de Entorno (Recomendado)**

```bash
# Windows Command Prompt
set EMOTIV_CLIENT_ID=tu_client_id
set EMOTIV_CLIENT_SECRET=tu_client_secret

# Windows PowerShell
$env: EMOTIV_CLIENT_ID="tu_client_id"
$env:EMOTIV_CLIENT_SECRET="tu_client_secret"
```

**Opción 2: Modificar Código Fuente (No Recomendado)**

Edita `bcipydummies/emotiv_controller.py` directamente.  Esto no se recomienda ya que las credenciales pueden ser accidentalmente commiteadas al control de versiones.

## Verificación

Verifica la instalación:

```python
python -c "from bcipydummies.emotiv_controller import EmotivController; print('¡Instalación exitosa!')"
```

Lista las ventanas disponibles para confirmar la integración Win32:

```python
from bcipydummies.emotiv_controller import EmotivController
windows = EmotivController.list_windows()
print(f"Se encontraron {len(windows)} ventanas")
```

## Solución de Problemas

### Error de Importación:  No module named 'win32gui'

El paquete pywin32 no se instaló correctamente: 

```bash
pip uninstall pywin32
pip install pywin32
python -c "import win32gui; print('OK')"
```

### Conexión WebSocket Rechazada

1. Asegúrate de que la app Emotiv Cortex esté ejecutándose
2. Verifica que Cortex esté escuchando en el puerto 6868
3. Verifica que tu firewall no esté bloqueando conexiones locales

### Headset No Detectado

1. Asegúrate de que tu headset Emotiv esté emparejado con la app Cortex
2. Verifica la conexión del dongle USB o Bluetooth
3. Verifica el nivel de batería del headset

## Próximos Pasos

- [Guía de Inicio Rápido](quickstart.md) - Empieza en 5 minutos
- [Configuración Emotiv](../hardware/emotiv-setup.md) - Configura tu headset