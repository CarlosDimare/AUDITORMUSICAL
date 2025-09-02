import os
os.environ["PATH"] += os.pathsep + r"C:\Program Files\ffmpeg-2025-08-25-git-1b62f9d3ae-full_build\bin"

from pydub import AudioSegment
AudioSegment.converter = r"C:\Program Files\ffmpeg-2025-08-25-git-1b62f9d3ae-full_build\bin\ffmpeg.exe"

import nest_asyncio, asyncio, aiohttp, time, os, ffmpeg
from shazamio import Shazam
import pandas as pd
from datetime import datetime
import pytz
from pydub import AudioSegment
import gspread
from google.oauth2.service_account import Credentials

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
║    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗██║  ██║███████╗  ║
║    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝  ║
║                                                             ║
║                🎶 🎶				    ::Dimare::║
╚═════════════════════════════════════════════════════════════╝
"""
   
   # Colores ANSI para terminal
   RED = '\033[91m'
   MAGENTA = '\033[95m'
   YELLOW = '\033[93m'
   GREEN = '\033[92m'
   RESET = '\033[0m'
   BOLD = '\033[1m'
   
   print(YELLOW + banner + RESET)
   print(f"{BOLD}{GREEN}🚀 Reconociendo Música...{RESET}")
   print(f"{GREEN}📻 Del Streaming: {MAGENTA}https://cdn.instream.audio:9288/stream{RESET}")
   print(f"{GREEN}⏰ Cada: {MAGENTA}30 segundos{RESET}")
   print(f"{GREEN}☁️ Google Sheet: {MAGENTA}AUDITOR MUSICAL{RESET}")
   print(f"{GREEN}💾 Backup Local: {MAGENTA}resultados.xlsx{RESET}")
   print("=" * 64)

# ===== CONFIGURACIÓN =====
STREAM_URL = "https://cdn.instream.audio:9288/stream"
INTERVALO_SEG = 30
SEGMENT_FILE = "segment.wav"
OUTPUT_FILE = "resultados.xlsx"
GOOGLE_SHEET_NAME = "AUDITOR MUSICAL"
ultimo_match = None

# Ruta completa a tu ffmpeg.exe
FFMPEG_PATH = r"C:\Program Files\ffmpeg-2025-08-25-git-1b62f9d3ae-full_build\bin\ffmpeg.exe"

# ===== INICIALIZACIÓN =====
mostrar_banner()
AudioSegment.converter = FFMPEG_PATH
os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_PATH)
nest_asyncio.apply()
shazam = Shazam()

# Crear archivo Excel de backup si no existe
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Hora", "Título", "Artista"]).to_excel(OUTPUT_FILE, index=False)

# --- Definición de Colores ---
GREEN, CYAN, YELLOW, RESET, BOLD, RED, MAGENTA = '\033[92m', '\033[96m', '\033[93m', '\033[0m', '\033[1m', '\033[91m', '\033[95m'

# Conexión a Google Sheets
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    google_sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    print(f"{BOLD}{GREEN}✅ Conectado a Google Sheet '{GOOGLE_SHEET_NAME}' exitosamente.{RESET}")
except Exception as e:
    google_sheet = None
    print(f"{BOLD}{RED}❌ No se pudo conectar a Google Sheets: {e}{RESET}")
    print(f"{BOLD}{YELLOW}ℹ️  El programa continuará guardando solo el backup local en '{OUTPUT_FILE}'.{RESET}")

# ===== FUNCIÓN PRINCIPAL =====
async def reconocer_stream(url, intervalo=30):
    global ultimo_match
    global google_sheet

    while True:
        try:
            # 1) Grabar 12s del stream como WAV temporal
            (
                ffmpeg
                .input(url, t=12)
                .output(SEGMENT_FILE, ar=44100, ac=2, format='wav', loglevel="error")
                .overwrite_output()
                .run()
            )

            # 2) Reconocer con Shazamio
            result_shazam = await shazam.recognize(SEGMENT_FILE)

            if result_shazam.get("track"):
                track = result_shazam["track"]
                hora_arg = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d %H:%M:%S")
                titulo = track.get("title", "Desconocido")
                artista = track.get("subtitle", "Desconocido")

                if ultimo_match != (titulo, artista):
                    ultimo_match = (titulo, artista)
                    
                    print(f"{BOLD}{GREEN}🎵 [{YELLOW}{hora_arg}{GREEN}] {CYAN}{titulo}{RESET} - {CYAN}{artista}{RESET}")

                    # 3) Guardar en Google Sheets
                    if google_sheet:
                        try:
                            google_sheet.append_row([hora_arg, titulo, artista])
                            print(f"  {GREEN}✔️ Fila agregada a Google Sheets.{RESET}")
                        except Exception as gs_e:
                            print(f"  {RED}❌ Error al escribir en Google Sheets: {gs_e}{RESET}")

                    # 4) Guardar en Excel (Backup)
                    try:
                        df_existing = pd.read_excel(OUTPUT_FILE)
                        df_new = pd.DataFrame([[hora_arg, titulo, artista]], columns=["Hora", "Título", "Artista"])
                        pd.concat([df_existing, df_new], ignore_index=True).to_excel(OUTPUT_FILE, index=False)
                        print(f"  {GREEN}✔️ Backup local en '{OUTPUT_FILE}' actualizado.{RESET}")
                    except Exception as xl_e:
                        print(f"  {RED}❌ Error al escribir en el backup local: {xl_e}{RESET}")


        except Exception as e:
            print(f"{RED}❌ Error en el ciclo principal: {e}{RESET}")

        await asyncio.sleep(intervalo)

# ===== EJECUCIÓN =====
asyncio.run(reconocer_stream(STREAM_URL, INTERVALO_SEG))