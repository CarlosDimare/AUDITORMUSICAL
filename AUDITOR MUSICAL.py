import asyncio
import collections
import os
import sys
import threading
import time
from datetime import datetime

# Suprimir advertencia de pydub
with open(os.devnull, 'w') as f:
    old_stderr = sys.stderr
    sys.stderr = f
    from pydub import AudioSegment
    sys.stderr = old_stderr

import colorama
import numpy as np
import pandas as pd
import pytz
import sounddevice as sd
import soundfile as sf
from shazamio import Shazam

# ===== CONFIGURACIÓN =====
INTERVALO_RECONOCIMIENTO = 30  # En segundos
SEGUNDOS_GRABACION = 12        # Duración del audio a analizar
SAMPLERATE = 44100

SEGMENT_FILE = "segment.wav"
OUTPUT_FILE = "resultados.xlsx"
FFMPEG_PATH = r"C:\Users\AUXILIARPB\AppData\Local\ffmpeg\bin\ffmpeg.exe"

# ===== INICIALIZACIÓN =====
colorama.init()

# Configurar pydub para que encuentre ffmpeg
AudioSegment.converter = FFMPEG_PATH
if FFMPEG_PATH not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + os.path.dirname(FFMPEG_PATH)

# Buffer de audio compartido
audio_buffer = collections.deque(maxlen=SAMPLERATE * (SEGUNDOS_GRABACION + 3))
stop_event = threading.Event()
ultimo_match = None

def mostrar_banner():
   """Muestra el banner de Auditor Musical al iniciar el programa"""
   banner = """
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
║                 		                 🎶Dimare.    ║
╚═════════════════════════════════════════════════════════════╝
"""
   
   YELLOW = '\033[93m'
   RESET = '\033[0m'
   print(f"{YELLOW}{banner}{RESET}")
 
# ===== FUNCIONES DE AUDIO Y VÚMETRO =====

def print_vumetro(rms_level, width=40):
    """Imprime una barra de vúmetro ASCII en la consola."""
    if rms_level < 1:
        rms_level = 1

    dbfs = 20 * np.log10(rms_level / 32767)
    min_db, max_db = -60, 0
    level = max(0.0, min(1.0, (dbfs - min_db) / (max_db - min_db)))

    bar_length = int(level * width)
    bar = '█' * bar_length
    empty_bar = ' ' * (width - bar_length)
    
    color = '\033[91m' # Rojo
    RESET = '\033[0m'
        
    print(f'Vol: |{color}{bar}{RESET}{empty_bar}|', end='\r', flush=True)

def audio_callback(indata, frames, time, status):
    """Función llamada por sounddevice para cada bloque de audio."""
    if status:
        print(status, file=sys.stderr)
    
    audio_buffer.extend(indata[:, 0])
    rms = np.sqrt(np.mean(indata.astype(np.float64)**2))
    print_vumetro(rms)

def audio_thread_func():
    """Hilo que gestiona la captura de audio y el vúmetro."""
    try:
        with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=audio_callback):
            while not stop_event.is_set():
                time.sleep(0.5)
    except Exception as e:
        print(f"\n❌ Error crítico en el hilo de audio: {e}", file=sys.stderr)

# ===== FUNCIÓN PRINCIPAL DE RECONOCIMIENTO =====
async def reconocer_en_bucle(shazam):
    global ultimo_match

    while not stop_event.is_set():
        await asyncio.sleep(INTERVALO_RECONOCIMIENTO)

        if len(audio_buffer) < SAMPLERATE * SEGUNDOS_GRABACION:
            continue

        buffer_snapshot = list(audio_buffer)
        segmento = np.array(buffer_snapshot[-SAMPLERATE * SEGUNDOS_GRABACION:])
        sf.write(SEGMENT_FILE, segmento, SAMPLERATE)

        try:
            result_shazam = await shazam.recognize(SEGMENT_FILE)
        except Exception as e:
            print(f"\nError en Shazam: {e}", file=sys.stderr)
            continue

        if result_shazam.get("track"):
            track = result_shazam["track"]
            titulo = track.get("title", "Desconocido")
            artista = track.get("subtitle", "Desconocido")

            if ultimo_match != (titulo, artista):
                ultimo_match = (titulo, artista)
                hora_arg = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%H:%M:%S")

                GREEN = '\033[92m'
                RESET = '\033[0m'

                print(' ' * 60, end='\r')
                print(f"{GREEN}🎵 {hora_arg} - {titulo} - {artista}{RESET}")

                try:
                    df_existing = pd.read_excel(OUTPUT_FILE)
                    df_new = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), titulo, artista]], columns=["Hora", "Título", "Artista"])
                    pd.concat([df_existing, df_new], ignore_index=True).to_excel(OUTPUT_FILE, index=False)
                except Exception as e:
                    print(f"\nError al guardar en Excel: {e}", file=sys.stderr)

# ===== EJECUCIÓN =====
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FILE):
        pd.DataFrame(columns=["Hora", "Título", "Artista"]).to_excel(OUTPUT_FILE, index=False)

    mostrar_banner()
    
    audio_thread = threading.Thread(target=audio_thread_func)
    audio_thread.daemon = True
    audio_thread.start()

    try:
        shazam_instance = Shazam()
        asyncio.run(reconocer_en_bucle(shazam_instance))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ Error inesperado en el bucle principal: {e}", file=sys.stderr)
    finally:
        print("\nFinalizando...", end='')
        stop_event.set()
        audio_thread.join(timeout=2)
        print(" ¡Hasta luego!")
        sys.exit(0)
