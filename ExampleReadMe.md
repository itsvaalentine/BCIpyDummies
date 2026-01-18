# 🧠 BCI Mouse Controller con Dwell Time

Control del mouse mediante **comandos mentales** usando un headset Emotiv EEG, con sistema de **Dwell Time** para clics automáticos y **Auto-Scroll** en los bordes de la pantalla.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Controles](#-controles)
- [Arquitectura](#-arquitectura)
- [Solución de Problemas](#-solución-de-problemas)
- [Contribuir](#-contribuir)

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 🧠 **Control Mental** | Mueve el cursor usando comandos mentales (LEFT, RIGHT, PUSH, PULL, LIFT) |
| ⏱️ **Dwell Time** | Clic automático al mantener el cursor sobre un elemento por tiempo configurable |
| 📜 **Auto-Scroll** | Scroll automático cuando el cursor llega a los bordes superior/inferior |
| 🎯 **Resaltado Visual** | Muestra el elemento actual con borde de color y etiqueta informativa |
| 🖱️ **Clic Exacto** | El clic se ejecuta exactamente donde está el cursor |

---

## 📦 Requisitos

### Hardware
- Headset EEG **Emotiv** (EPOC, EPOC+, EPOC X, Insight)
- Windows 10/11

### Software
- Python 3.9 o superior
- Emotiv Cortex instalado y ejecutándose
- Comandos mentales entrenados en EmotivBCI

### Dependencias Python
```bash
bcipydummies
selenium
webdriver-manager
```

---

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/tu-usuario/bci-mouse-dwell.git
cd bci-mouse-dwell
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias

```bash
pip install bcipydummies selenium webdriver-manager
```

### 4. Obtener credenciales de Emotiv

1. Ve a [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Crea una cuenta o inicia sesión
3. Crea una nueva aplicación
4. Copia tu **Client ID** y **Client Secret**

---

## ⚙️ Configuración

Edita las variables al inicio del archivo `bci_mouse_dwell.py`:

```python
# Credenciales de Emotiv (REQUERIDO)
CLIENT_ID = "tu_client_id_aqui"
CLIENT_SECRET = "tu_client_secret_aqui"

# Configuración del mouse
PIXELS = 30              # Píxeles por movimiento

# Configuración del Dwell Time
DWELL_TIME = 1.5         # Segundos para activar clic automático

# Configuración del Auto-Scroll
SCROLL_ZONE = 80         # Altura de la zona de scroll (píxeles desde el borde)
SCROLL_AMOUNT = 150      # Píxeles a scrollear por activación

# URL inicial
URL_INICIAL = "https://www.google.com"
```

### Descripción de parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `CLIENT_ID` | str | - | ID de cliente de Emotiv Developer |
| `CLIENT_SECRET` | str | - | Secret de cliente de Emotiv Developer |
| `PIXELS` | int | 30 | Distancia en píxeles que se mueve el cursor por cada comando |
| `DWELL_TIME` | float | 1.5 | Segundos que debe permanecer sobre un elemento para hacer clic |
| `SCROLL_ZONE` | int | 80 | Altura en píxeles de la zona de activación del scroll |
| `SCROLL_AMOUNT` | int | 150 | Píxeles que se desplaza por cada scroll |
| `URL_INICIAL` | str | google.com | URL que se abre al iniciar |

---

## 🎮 Uso

### 1. Preparación

1. Conecta tu headset Emotiv
2. Abre **Emotiv Cortex** y verifica la conexión
3. Asegúrate de tener los comandos mentales entrenados

### 2. Ejecutar

```bash
python bci_mouse_dwell.py
```

### 3. Salir

Presiona `Ctrl+C` en la terminal. 

---

## 🕹️ Controles

### Comandos Mentales

| Comando | Acción |
|---------|--------|
| `LEFT` | Mueve el cursor a la izquierda |
| `RIGHT` | Mueve el cursor a la derecha |
| `PUSH` | Mueve el cursor hacia arriba |
| `PULL` | Mueve el cursor hacia abajo |
| `LIFT` | Ejecuta clic manual |

### Dwell Time (Clic Automático)

```
┌─────────────────────────────────┐
│                                 │
│    Mantén el cursor sobre un    │
│    elemento durante 1.5s        │
│                                 │
│         ┌─────────┐             │
│         │ Botón   │ ← Resaltado │
│         └─────────┘             │
│         <button> Buscar         │ ← Etiqueta
│                                 │
│    Se ejecutará clic automático │
│                                 │
└─────────────────────────────────┘
```

### Auto-Scroll

```
┌──────��──────────────────────────┐
│ ▲▲▲ ZONA DE SCROLL ARRIBA ▲▲▲  │ ← 80px superiores
├─────────────────────────────────┤
│                                 │
│                                 │
│        Contenido normal         │
│                                 │
│                                 │
├─────────────────────────────────┤
│ ▼▼▼ ZONA DE SCROLL ABAJO ▼▼▼   │ ← 80px inferiores
└─────────────────────────────────┘
```

---

## 🏗️ Arquitectura

```
bci_mouse_dwell. py
│
├── Mouse                 # Control del cursor (Windows API)
│   ├── pos()            # Obtener posición actual
│   ├── move(x, y)       # Mover cursor
│   └── click()          # Ejecutar clic
│
├── DwellManager          # Gestión de Dwell Time y Scroll
│   ├── start()          # Iniciar monitoreo
│   ├── stop()           # Detener monitoreo
│   ├── _get_element()   # Detectar elemento bajo cursor
│   ├── _highlight_element()  # Resaltar elemento
│   ├── _clear_highlight()    # Limpiar resaltado
│   └── _scroll()        # Ejecutar scroll
│
├── BCIMouse              # Publisher para BCIpyDummies
│   ├── start()          # Iniciar publisher
│   ├── stop()           # Detener publisher
│   └── publish(event)   # Procesar comandos mentales
│
└── main()                # Punto de entrada
    ├── Configurar navegador (Selenium)
    ├── Iniciar DwellManager
    ├── Configurar pipeline BCI
    └── Loop principal
```

### Flujo de datos

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│ Emotiv       │────▶│ ThresholdProcessor│────▶│ BCIMouse    │
│ Headset      │     │ (filtro 30%)      │     │ (Publisher) │
└──────────────┘     └───────────────────┘     └─────────────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │ Mouse. move/ │
                                               │ Mouse.click │
                                               └─────────────┘

┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│ Cursor       │────▶│ DwellManager      │────▶│ Clic auto/  │
│ Position     │     │ (tracking)        │     │ Scroll      │
└──────────────┘     └───────────────────┘     └─────────────┘
```

---

## 🔧 Solución de Problemas

### "No se detectan comandos mentales"

1.  Verifica que Emotiv Cortex esté ejecutándose
2. Verifica que el headset esté conectado (luz verde)
3. Asegúrate de haber entrenado los comandos en EmotivBCI
4. Revisa que las credenciales sean correctas

### "El resaltado no aparece"

1. Asegúrate de que el cursor esté dentro del área de contenido del navegador
2. Algunas páginas con CSP estricto pueden bloquear la inyección de elementos

### "El scroll no funciona"

1. Verifica que el cursor esté en la zona de scroll (80px desde los bordes)
2. Algunas páginas tienen scroll personalizado que puede no responder

### "Los movimientos son muy lentos/rápidos"

Ajusta el valor de `PIXELS` en la configuración: 
- Más lento: `PIXELS = 15`
- Más rápido: `PIXELS = 50`

### "El dwell es muy lento/rápido"

Ajusta el valor de `DWELL_TIME`:
- Más rápido: `DWELL_TIME = 1.0`
- Más lento: `DWELL_TIME = 2.0`

---

## 📁 Archivos

```
bci-mouse-dwell/
├── bci_mouse_dwell. py      # Código principal
├── bci_mouse_dwell_docs.py # Código documentado
├── README.md               # Esta documentación
└── requirements.txt        # Dependencias
```

### requirements.txt

```
bcipydummies
selenium
webdriver-manager
```

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

Desarrollado con 🧠 usando [BCIpyDummies](https://github.com/itsvaalentine/BCIpyDummies)