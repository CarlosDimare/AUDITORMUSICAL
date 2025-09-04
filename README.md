╔═════════════════════════════════════════════════════════════╗
║                                                             ║
║     █████╗ ██╗   ██╗██████╗ ██╗████████╗ ██████╗ ██████╗    ║
║    ██╔══██╗██║   ██║██╔══██╗██║╚══██╔══╝██╔═══██╗██╔══██╗   ║
║    ███████║██║   ██║██║  ██║██║   ██║   ██║   ██║██████╔╝   ║
║    ██╔══██║██║   ██║██║  ██║██║   ██║   ██║   ██║██╔══██╗   ║
║    ██║  ██║╚██████╔╝██████╔╝██║   ██║   ╚██████╔╝██║  ██║   ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ║
║                                                             ║
║    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗ █████╗ ██╗       ║
║    ████╗ ████║██║   ██║██╔════╝██║██╔════╝██╔══██╗██║       ║
║    ██╔████╔██║██║   ██║███████╗██║██║     ███████║██║       ║
║    ██║╚██╔╝██║██║   ██║╚════██║██║██║     ██╔══██║██║       ║
║    ██║ ╚═╝ ██║╚██████╔╝███████╗██║╚██████╗██║  ██║███████╗  ║
║    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝  ║
║                                                             ║
║                 		                 🎶Dimare.           ║
╚═════════════════════════════════════════════════════════════╝

# Auditor Musical

`Auditor Musical` es un script de Python diseñado para monitorear un stream de audio por internet, reconocer las canciones que se están reproduciendo usando el motor de Shazam y registrar cada canción en una hoja de cálculo de Google Sheets, manteniendo también un backup local en un archivo Excel.

El script muestra la información en tiempo real en la consola, con un banner distintivo y salida coloreada para una fácil lectura.

## Características

-   **Monitoreo de Stream**: Graba periódicamente un segmento de cualquier stream de audio en vivo (radio por internet).
-   **Reconocimiento de Canciones**: Utiliza la biblioteca `shazamio` para identificar el título y el artista de la canción.
-   **Registro en la Nube**: Se conecta a la API de Google Sheets para guardar un registro histórico de todas las canciones reconocidas, con su respectiva marca de tiempo.
-   **Backup Local**: Guarda una copia de seguridad de todos los registros en un archivo `.xlsx` en la misma carpeta del script.
-   **Evita Duplicados**: El script es lo suficientemente inteligente como para no registrar la misma canción dos veces seguidas.
-   **Interfaz de Consola**: Muestra un banner y registra la actividad en tiempo real con colores para una mejor visualización.

## Requisitos

Para que el script funcione, necesitas tener lo siguiente:

### 1. Dependencias del Sistema

-   **FFmpeg**: Es una dependencia crucial que el script utiliza para grabar el segmento del stream de audio. Debes tenerlo instalado y accesible en el PATH de tu sistema.
    -   Puedes descargarlo desde [el sitio oficial de FFmpeg](https://ffmpeg.org/download.html).

### 2. Credenciales de Google

-   **Cuenta de Servicio de Google Cloud**: Para que el script pueda escribir en una Google Sheet, necesita un archivo de credenciales.
    1.  Sigue la [guía oficial de Google](https://docs.gspread.org/en/latest/oauth2.html) para crear una cuenta de servicio.
    2.  Descarga el archivo JSON con las credenciales y renómbralo a `credentials.json`.
    3.  Coloca el archivo `credentials.json` en la misma carpeta que el script.
    4.  **Importante**: No olvides compartir tu Google Sheet con el email de la cuenta de servicio (`client_email` que aparece en tu `credentials.json`) y darle permisos de "Editor".

### 3. Bibliotecas de Python

Las siguientes bibliotecas son necesarias. Puedes instalarlas todas juntas usando el archivo `requirements.txt` proporcionado.

-   `nest_asyncio`
-   `aiohttp`
-   `ffmpeg-python`
-   `shazamio`
-   `pandas`
-   `openpyxl` (necesario para que pandas escriba archivos .xlsx)
-   `pytz`
-   `pydub`
-   `gspread`
-   `google-oauth2-service-account`

## Instalación

1.  **Clona o descarga este repositorio.**

2.  **Instala FFmpeg**: Asegúrate de que FFmpeg esté instalado en tu sistema y que el ejecutable esté en el PATH.

3.  **Configura las credenciales**: Coloca tu archivo `credentials.json` en el directorio raíz del proyecto.

4.  **Instala las dependencias de Python**: Abre una terminal en el directorio del proyecto y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

Antes de ejecutar el script, puedes ajustar las siguientes variables en la sección `===== CONFIGURACIÓN =====` del archivo `AUDITOR-MUSICAL.py`:

-   `STREAM_URL`: La URL del stream de radio que quieres monitorear.
-   `INTERVALO_SEG`: El tiempo en segundos entre cada reconocimiento de canción.
-   `OUTPUT_FILE`: El nombre del archivo Excel que se usará como backup local.
-   `GOOGLE_SHEET_NAME`: El nombre exacto de la hoja de cálculo en tu Google Drive donde se guardarán los registros.

## Uso

Una vez que hayas completado la instalación y configuración, simplemente ejecuta el script desde tu terminal:

```bash
python AUDITOR-MUSICAL.py
```

El script comenzará a ejecutarse, mostrará el banner y empezará a monitorear el stream. Verás en la consola cada vez que una nueva canción sea reconocida y registrada. Para detener el script, presiona `Ctrl + C`.

## Salida

El script genera dos archivos de registro:

1.  **Google Sheet**: Una hoja de cálculo en tu Google Drive con las columnas `Hora`, `Título` y `Artista`.
2.  **Archivo Excel Local**: Un archivo (por defecto `resultados.xlsx`) con la misma estructura, que sirve como respaldo.

---

*Este README fue generado por Gemini.*