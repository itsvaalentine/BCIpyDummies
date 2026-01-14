# Guía de Configuración de Hardware Emotiv

Esta guía cubre la configuración de tu headset EEG Emotiv para usar con BCIpyDummies. 

## Dispositivos Soportados

BCIpyDummies funciona con cualquier headset Emotiv soportado por la API Cortex: 

| Dispositivo | Canales | Conexión | Notas |
|-------------|---------|----------|-------|
| EPOC X | 14 | Dongle USB | Mejor para comandos mentales |
| EPOC+ | 14 | Bluetooth/USB | Buen balance de calidad y portabilidad |
| Insight | 5 | Bluetooth | Ligero, menos canales |
| EPOC Flex | 32 | USB | Grado investigación |

## Configuración Inicial

### 1. Crear Cuenta Emotiv

1. Ve a [emotiv.com](https://www.emotiv.com)
2. Crea una cuenta gratuita
3. Verifica tu email

### 2. Instalar Software Emotiv

Descarga e instala: 

1. **Emotiv Cortex** - Servicio en segundo plano que maneja la comunicación del dispositivo
   - Descarga de [emotiv.com/emotiv-cortex](https://www.emotiv.com/emotiv-cortex/)

2. **EmotivBCI** (opcional pero recomendado) - Para entrenar comandos mentales
   - Disponible en el sitio web de Emotiv o tiendas de apps

### 3. Emparejar Tu Headset

**Método Dongle USB (EPOC X, EPOC+):**
1. Inserta el dongle USB
2. Enciende el headset
3. Abre Emotiv Cortex
4. Espera el emparejamiento automático

**Método Bluetooth (Insight, EPOC+):**
1. Enciende el headset
2. Habilita Bluetooth en tu computadora
3. Abre Emotiv Cortex
4. Sigue las indicaciones de emparejamiento

## Entrenar Comandos Mentales

Los comandos mentales requieren entrenamiento en la app EmotivBCI antes de que BCIpyDummies pueda usarlos.

### Entrenamiento Requerido

| Comando | Descripción | Entrenamiento Recomendado |
|---------|-------------|---------------------------|
| `neutral` | Estado relajado | 30+ segundos, múltiples sesiones |
| `left` | Pensar "izquierda" | 8+ muestras de entrenamiento |
| `right` | Pensar "derecha" | 8+ muestras de entrenamiento |
| `lift` | Pensar "arriba/levantar" | 8+ muestras de entrenamiento |

### Tips de Entrenamiento

1. **Empieza con Neutral**
   - Entrena el estado neutral primero
   - Mantén tu mente calmada y relajada
   - Entrena en el mismo ambiente donde usarás el headset

2. **Imaginería Mental Consistente**
   - Usa la misma imagen mental cada vez
   - Para "left":  imagina tu mano moviéndose a la izquierda, o visualiza una flecha apuntando a la izquierda
   - Sé consistente entre sesiones de entrenamiento

3. **Sesiones Cortas**
   - Entrena por 10-15 minutos a la vez
   - Toma descansos para evitar fatiga
   - Calidad sobre cantidad

4. **Buena Calidad de Contacto**
   - Asegúrate de que todos los sensores muestren verde en Cortex
   - Usa solución salina en los sensores si es necesario
   - El cabello no debe bloquear los sensores

## Optimizar Calidad de Señal

### Colocación de Sensores

1. Posiciona el headset según el manual del dispositivo
2. Asegúrate de que los sensores estén planos contra el cuero cabelludo
3. Mueve el cabello lejos de las áreas de sensores
4. Aplica solución salina a los sensores de fieltro (dispositivos EPOC)

### Indicadores de Calidad de Contacto

En Emotiv Cortex:
- **Verde**: Buen contacto
- **Naranja**: Aceptable, puede tener ruido
- **Rojo**: Mal contacto, reposicionar
- **Negro**: Sin contacto

**Objetivo**: Todos los sensores en verde antes de iniciar BCIpyDummies. 

### Tips de Ambiente

- Minimiza interferencia eléctrica (aléjate de monitores)
- Evita iluminación fluorescente
- Mantente quieto durante el uso
- Evita movimientos excesivos de mandíbula o parpadeos

## Configuración de API Cortex

### Verificar que Cortex Está Ejecutándose

1. Abre Emotiv Cortex
2. Busca el estado "Cortex running"
3. Verifica que el headset muestre "Connected"

### Conexión por Defecto

BCIpyDummies se conecta a: 
```
wss://127.0.0.1:6868
```

Este es el endpoint WebSocket de Cortex por defecto.  Asegúrate de que ningún firewall bloquee conexiones locales.

### Obtener Credenciales API

1. Ve a [emotiv.com/developer](https://www.emotiv.com/developer/)
2. Inicia sesión con tu cuenta Emotiv
3. Haz clic en "Create Application"
4. Completa los detalles de la aplicación: 
   - Nombre: BCIpyDummies
   - Tipo: Desktop
5. Copia tu Client ID y Client Secret

## Consideraciones de Licencia

Emotiv ofrece diferentes niveles de licencia:

| Característica | Gratis | Pro | Enterprise |
|----------------|--------|-----|------------|
| Comandos Mentales | Limitado | Completo | Completo |
| Datos EEG Raw | No | Sí | Sí |
| Múltiples Headsets | No | Sí | Sí |

BCIpyDummies usa el stream de comandos mentales, que funciona con el nivel gratuito pero tiene limitaciones en precisión de detección.

## Solución de Problemas

### El Headset No Conecta

1. Verifica el nivel de batería (carga si está bajo)
2. Prueba un puerto USB diferente para el dongle
3. Reinicia Emotiv Cortex
4. Re-empareja el headset

### Mala Detección de Comandos

1. Re-entrena comandos con mejor calidad de contacto
2. Entrena más muestras
3. Reduce ruido ambiental
4. Asegura imaginería mental consistente

### Cortex No Ejecutándose

1. Verifica Servicios de Windows para "Emotiv Cortex"
2. Reinstala Cortex si falta el servicio
3. Ejecuta Cortex como administrador si es necesario

## Próximos Pasos

- [Guía de Inicio Rápido](../getting-started/quickstart.md) - Empieza a usar BCIpyDummies
- [Guía de Comandos Mentales](../user-guide/mental-commands.md) - Profundiza en entrenamiento de comandos