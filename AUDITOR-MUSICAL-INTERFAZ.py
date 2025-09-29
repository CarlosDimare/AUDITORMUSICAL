import asyncio
import collections
import os
import sys
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import win32gui
import win32con
import ctypes
from datetime import datetime
import pytz
import numpy as np

# Ocultar la ventana de la consola en Windows
def hide_console():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
    except:
        pass

hide_console()

# Suprimir advertencia de pydub
with open(os.devnull, 'w') as f:
    old_stderr = sys.stderr
    sys.stderr = f
    from pydub import AudioSegment
    sys.stderr = old_stderr

import colorama
import pandas as pd
import requests
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

# 🔗 Tu URL de Google Apps Script (funcional)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxAiK-zsWv3YBBTubMNXcwxgYirKy2OtgwvSZW2PD6g01H790_myAa4GZnixTMvC1Bu5A/exec"

# ===== BANNER =====
def get_banner():
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
║                 		                 Dimare                   ║
╚═════════════════════════════════════════════════════════════╝
"""
    return banner

# ===== INICIALIZACIÓN =====
colorama.init()

AudioSegment.converter = FFMPEG_PATH
if FFMPEG_PATH not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + os.path.dirname(FFMPEG_PATH)

audio_buffer = collections.deque(maxlen=SAMPLERATE * (SEGUNDOS_GRABACION + 3))
stop_event = threading.Event()
ultimo_match = None
result_queue = queue.Queue()
audio_level_queue = queue.Queue()
is_processing = False

# ===== INTERFAZ GRÁFICA =====
class AuditorMusicalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("| AUDITOR MUSICAL |")
        self.root.geometry("700x700")  # Aumentado para acomodar el banner
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configurar estilo oscuro
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('TButton', background='#3c3c3c', foreground='#ffffff')
        style.map('TButton', background=[('active', '#4c4c4c')])
        
        # Banner ASCII
        banner_frame = ttk.Frame(root)
        banner_frame.pack(pady=10, padx=10, fill='x')
        
        self.banner_text = tk.Text(
            banner_frame,
            height=20,
            width=70,
            bg='#000000',
            fg='#ffff00',
            font=('Courier New', 8),
            state='disabled',
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        self.banner_text.pack()
        
        # Insertar banner
        self.banner_text.config(state='normal')
        self.banner_text.insert(tk.END, get_banner())
        self.banner_text.config(state='disabled')
        
        # Título
        title_frame = ttk.Frame(root)
        title_frame.pack(pady=5, fill='x')
        
        title_label = ttk.Label(
            title_frame, 
            font=('Arial', 16, 'bold')
        )
        title_label.pack()
        
        # Vúmetro
        vumeter_frame = ttk.Frame(root)
        vumeter_frame.pack(pady=5, padx=20, fill='x')
        
        vumeter_label = ttk.Label(
            vumeter_frame, 
            text="Nivel de audio:", 
            font=('Arial', 10)
        )
        vumeter_label.pack(anchor='w')
        
        self.vumeter_canvas = tk.Canvas(
            vumeter_frame, 
            height=20, 
            bg='#2d2d2d', 
            highlightthickness=0
        )
        self.vumeter_canvas.pack(fill='x', pady=5)
        
        # Mensaje de estado
        self.status_label = ttk.Label(
            root, 
            text="Detectando música...", 
            font=('Arial', 10),
            foreground='#00ff00'
        )
        self.status_label.pack(pady=5)
        
        # Lista de resultados
        results_frame = ttk.Frame(root)
        results_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=10,  # Reducido para dar espacio al banner
            bg='#2d2d2d',
            fg='#ffffff',
            font=('Consolas', 10),
            state='disabled'
        )
        self.results_text.pack(fill='both', expand=True)
        
        # Configurar etiquetas para resultados
        self.results_text.tag_config('time', foreground='#00ff00')
        self.results_text.tag_config('title', foreground='#00ffff')
        self.results_text.tag_config('artist', foreground='#ffff00')
        
        # Cartel de advertencia
        warning_frame = ttk.Frame(root)
        warning_frame.pack(pady=10, fill='x')
        
        warning_label = tk.Label(
            warning_frame, 
            text="¡ NO CERRAR !", 
            bg='white',
            fg='red',
            font=('Arial', 14, 'bold'),
            padx=20,
            pady=5
        )
        warning_label.pack()
        
        # Iniciar actualización de resultados y vúmetro
        self.update_results()
        self.update_vumeter()
        
        # Configurar evento de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        # Mostrar advertencia al intentar cerrar
        messagebox.showwarning("ADVERTENCIA", "¡NO LO CIERRES POR FAVOR! LEE BIEN!")
    
    def add_result(self, hora, titulo, artista):
        self.results_text.config(state='normal')
        
        # Formatear resultado
        result_text = f"[{hora}] {titulo} - {artista}\n"
        
        # Insertar texto con etiquetas
        self.results_text.insert(tk.END, "[", '')
        self.results_text.insert(tk.END, hora, 'time')
        self.results_text.insert(tk.END, "] ", '')
        self.results_text.insert(tk.END, titulo, 'title')
        self.results_text.insert(tk.END, " - ", '')
        self.results_text.insert(tk.END, artista, 'artist')
        self.results_text.insert(tk.END, "\n", '')
        
        # Auto-scroll al final
        self.results_text.see(tk.END)
        self.results_text.config(state='disabled')
    
    def update_results(self):
        global is_processing
        
        try:
            while not result_queue.empty():
                hora, titulo, artista = result_queue.get_nowait()
                self.add_result(hora, titulo, artista)
        except queue.Empty:
            pass
        
        # Actualizar estado
        if is_processing:
            self.status_label.config(text="Detectando canción...", foreground='#ffff00')
        else:
            self.status_label.config(text="Detectando canción...", foreground='#00ff00')
        
        # Actualizar cada 500ms
        self.root.after(500, self.update_results)
    
    def update_vumeter(self):
        try:
            while not audio_level_queue.empty():
                level = audio_level_queue.get_nowait()
                self.draw_vumeter(level)
        except queue.Empty:
            pass
        
        # Actualizar cada 50ms para mayor fluidez
        self.root.after(50, self.update_vumeter)
    
    def draw_vumeter(self, level):
        self.vumeter_canvas.delete("all")
        
        # Calcular nivel en dB
        if level < 1:
            level = 1
        dbfs = 20 * np.log10(level / 32767)
        min_db, max_db = -60, 0
        normalized_level = max(0.0, min(1.0, (dbfs - min_db) / (max_db - min_db)))
        
        # Obtener dimensiones del canvas
        width = self.vumeter_canvas.winfo_width()
        height = self.vumeter_canvas.winfo_height()
        
        # Dibujar fondo
        self.vumeter_canvas.create_rectangle(0, 0, width, height, fill='#2d2d2d', outline='')
        
        # Dibujar barra de nivel
        bar_width = int(width * normalized_level)
        color = self.get_vumeter_color(normalized_level)
        self.vumeter_canvas.create_rectangle(0, 0, bar_width, height, fill=color, outline='')
        
        # Dibujar marcas
        for i in range(0, width, width // 10):
            self.vumeter_canvas.create_line(i, height - 2, i, height, fill='#888888')
    
    def get_vumeter_color(self, level):
        if level < 0.5:
            # Verde a amarillo
            r = int(255 * (level * 2))
            g = 255
            b = 0
        else:
            # Amarillo a rojo
            r = 255
            g = int(255 * (2 - level * 2))
            b = 0
        
        return f'#{r:02x}{g:02x}{b:02x}'

# ===== FUNCIONES PRINCIPALES =====
def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    
    # Agregar datos al buffer
    audio_buffer.extend(indata[:, 0])
    
    # Calcular nivel de audio para el vúmetro
    rms = np.sqrt(np.mean(indata.astype(np.float64)**2))
    audio_level_queue.put(rms)

def audio_thread_func():
    try:
        with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=audio_callback):
            while not stop_event.is_set():
                time.sleep(0.5)
    except Exception as e:
        print(f"\n❌ Error crítico en el hilo de audio: {e}", file=sys.stderr)

def enviar_a_google_sheets(hora, titulo, artista):
    try:
        datos = {
            "hora": hora,
            "titulo": titulo,
            "artista": artista
        }
        response = requests.post(GOOGLE_SCRIPT_URL, json=datos, timeout=10)
        if response.status_code == 200:
            print("✅ Enviado a Google Sheets.")
        else:
            print(f"⚠️ Google Sheets respondió: {response.text}")
    except Exception as e:
        print(f"❌ Error al enviar a Google Sheets: {e}")

def guardar_en_excel_local(hora, titulo, artista):
    try:
        if os.path.exists(OUTPUT_FILE):
            df = pd.read_excel(OUTPUT_FILE)
        else:
            df = pd.DataFrame(columns=["Hora", "Título", "Artista"])
        
        nueva_fila = pd.DataFrame([{"Hora": hora, "Título": titulo, "Artista": artista}])
        df = pd.concat([df, nueva_fila], ignore_index=True)
        
        with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Auditoría")
            worksheet = writer.sheets["Auditoría"]
            worksheet.set_column("A:A", 20)  # Hora
            worksheet.set_column("B:B", 45)  # Título
            worksheet.set_column("C:C", 35)  # Artista
        print("💾 Copia local guardada.")
    except PermissionError:
        print("⚠️ No se pudo guardar: el archivo Excel está abierto. Se omitió la copia local.")
    except Exception as e:
        print(f"⚠️ Error al guardar copia local: {e}")

async def reconocer_en_bucle(shazam):
    global ultimo_match, is_processing

    while not stop_event.is_set():
        await asyncio.sleep(INTERVALO_RECONOCIMIENTO)

        if len(audio_buffer) < SAMPLERATE * SEGUNDOS_GRABACION:
            continue

        # Indicar que estamos procesando
        is_processing = True
        
        buffer_snapshot = list(audio_buffer)
        segmento = np.array(buffer_snapshot[-SAMPLERATE * SEGUNDOS_GRABACION:])
        sf.write(SEGMENT_FILE, segmento, SAMPLERATE)

        try:
            result_shazam = await shazam.recognize(SEGMENT_FILE)
        except Exception as e:
            print(f"\nError en Shazam: {e}", file=sys.stderr)
            is_processing = False
            continue

        if result_shazam.get("track"):
            track = result_shazam["track"]
            titulo = track.get("title", "Desconocido")
            artista = track.get("subtitle", "Desconocido")

            if ultimo_match != (titulo, artista):
                ultimo_match = (titulo, artista)
                hora_arg = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%H:%M:%S")
                hora_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Enviar a la cola para mostrar en GUI
                result_queue.put((hora_arg, titulo, artista))
                
                # Enviar a Google Sheets y guardar localmente
                enviar_a_google_sheets(hora_local, titulo, artista)
                guardar_en_excel_local(hora_local, titulo, artista)
        
        # Indicar que terminamos de procesar
        is_processing = False

# ===== EJECUCIÓN =====
if __name__ == "__main__":
    # Crear ventana principal
    root = tk.Tk()
    app = AuditorMusicalGUI(root)
    
    # Iniciar hilo de audio
    audio_thread = threading.Thread(target=audio_thread_func)
    audio_thread.daemon = True
    audio_thread.start()
    
    # Iniciar reconocimiento en un hilo separado
    def run_asyncio_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        shazam_instance = Shazam()
        loop.run_until_complete(reconocer_en_bucle(shazam_instance))
    
    recognition_thread = threading.Thread(target=run_asyncio_loop)
    recognition_thread.daemon = True
    recognition_thread.start()
    
    # Iniciar GUI
    root.mainloop()