# pip install PyPDF2

import json
import os
import random
import re
import tempfile
import time
import tkinter as tk
import unicodedata
import uuid
from datetime import date, datetime
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from backend import AppServices

try:
    import winsound
except ImportError:
    winsound = None

class PdfRenamerApp:
    def __init__(self, root):
        self.root = root
        self.base_window_title = "Renombrador de PDF por NCF y Razon Social Cliente"
        self.root.title(self.base_window_title)
        self.root.geometry("1100x760")
        self.root.minsize(980, 700)
        self.root.configure(bg="#f4f1ea")
        self.logo_image = None
        self.pomodoro_icon_image = None
        self.pomodoro_icon_last_text = None
        self.pomodoro_icon_path = os.path.join(tempfile.gettempdir(), "renombrar_pomodoro_taskbar.ico")
        self.taskbar_overlay_ready = False
        self.taskbar_overlay_active = False
        self.taskbar_overlay_ptr = None
        self.taskbar_overlay_hicon = None

        self.pdf_path = ""
        self.pdf_paths = []
        self.output_folder = ""
        self.saved_folders = []
        self.company_route_mappings = []
        self.copy_source_pdf = ""
        self.copy_name_var = tk.StringVar()
        self.copy_proposal_type_var = tk.StringVar(value="mensual")
        self.message_client_name_var = tk.StringVar()
        self.message_type_var = tk.StringVar(value="Plantilla fiscal")
        self.message_fiscal_buyer_var = tk.StringVar()
        self.client_search_var = tk.StringVar()
        self.client_name_var = tk.StringVar()
        self.client_rnc_var = tk.StringVar()
        self.client_pc_location_var = tk.StringVar()
        self.client_cedula_var = tk.StringVar()
        self.client_tss_class_var = tk.StringVar()
        self.client_resource_path_var = tk.StringVar()
        self.fiscal_version_var = tk.StringVar()
        self.fiscal_version_date_var = tk.StringVar(value=date.today().isoformat())
        self.fiscal_version_change_type_var = tk.StringVar(value="Lanzamiento")
        self.fiscal_version_description_var = tk.StringVar()
        self.fiscal_version_affects_macros_var = tk.StringVar(value="Si")
        self.fiscal_version_requires_manual_var = tk.StringVar(value="No")
        self.fiscal_buyer_name_var = tk.StringVar()
        self.fiscal_buyer_purchase_date_var = tk.StringVar(value=date.today().isoformat())
        self.fiscal_buyer_expiration_date_var = tk.StringVar()
        self.fiscal_buyer_email_var = tk.StringVar()
        self.fiscal_buyer_price_var = tk.StringVar(value="3,000")
        self.fiscal_buyer_channel_var = tk.StringVar(value="desconocido")
        self.company_name_var = tk.StringVar()
        self.company_route_var = tk.StringVar()
        self.pomodoro_work_seconds = 25 * 60
        self.pomodoro_short_break_seconds = 5 * 60
        self.pomodoro_long_break_seconds = 15 * 60
        self.pomodoro_warning_seconds = 10 * 60
        self.pomodoro_state = self.get_default_pomodoro_state()
        self.pomodoro_after_id = None
        self.pomodoro_auto_start_break_var = tk.BooleanVar(value=True)
        self.pomodoro_auto_start_work_var = tk.BooleanVar(value=True)
        self.pomodoro_task_title_var = tk.StringVar()
        self.pomodoro_flow_name_var = tk.StringVar()
        self.refreshing_pomodoro_task_lists = False
        self.pomodoro_sound_aliases = {}
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")
        self.services = AppServices(self.db_path, self.config_path)
        self.client_default_base_folder = r"C:\Users\kalil\OneDrive\Documentos\igualas"
        self.processed_count = 0
        self.clients = []
        self.pomodoro_tasks = []
        self.pomodoro_flows = []
        self.fiscal_versions = []
        self.fiscal_buyers = []
        self.message_fiscal_buyer_map = {}
        self.selected_fiscal_buyer_id = None
        self.selected_client_id = None
        self.client_extra_visible = False
        self.notebook = None
        self.tab_frames = {}
        self.home_icon_images = {}

        self.colors = {
            "bg": "#f4f1ea",
            "card": "#fffdfa",
            "card_alt": "#f8f3eb",
            "text": "#2d221a",
            "muted": "#7a6859",
            "accent": "#d65245",
            "accent_dark": "#ab3f35",
            "accent_soft": "#f5d9d3",
            "line": "#eadfce",
            "success": "#1f7a52",
            "log_bg": "#fffdf8",
            "clients_bg": "#111b21",
            "clients_card": "#202c33",
            "clients_hover": "#2a3942",
            "clients_active": "#334d5c",
            "clients_search": "#2a2f32",
            "clients_text": "#e9edef",
            "clients_muted": "#9fb0b9",
            "clients_accent": "#25d366",
        }

        # Ejemplo valido: E310000000001
        self.ncf_pattern = re.compile(r"\b[A-Z]\d{12}\b")

        # Ejemplo esperado en PDF: Razon Social Cliente: 40225661210 kalil
        self.razon_social_pattern = re.compile(
            r"R[aá]z[oó]n\s+Social\s+Cliente\s*[:\-]?\s*(.+)",
            re.IGNORECASE,
        )


        self.init_database()
        self.load_config()
        self.load_pomodoro_tasks_from_db()
        self.load_pomodoro_flows_from_db()
        self.load_fiscal_versions_from_db()
        self.load_fiscal_buyers_from_db()
        self.pomodoro_auto_start_break_var.trace_add("write", self._on_pomodoro_setting_change)
        self.pomodoro_auto_start_work_var.trace_add("write", self._on_pomodoro_setting_change)
        self._configure_app_icon()
        self._configure_styles()
        self._build_ui()
        self._maximize_window()
        self.update_summary()
        self.update_flow_preview()
        self.start_pomodoro_tick()
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def _configure_app_icon(self):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_logo.png")
        if not os.path.exists(logo_path):
            return

        try:
            self.logo_image = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(True, self.logo_image)
        except tk.TclError:
            pass

    def set_window_icon(self, image, icon_path=None):
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                pass
        try:
            self.root.iconphoto(True, image)
        except tk.TclError:
            pass

    def _maximize_window(self):
        try:
            self.root.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.root.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "App.TFrame",
            background=self.colors["bg"],
        )
        style.configure(
            "Card.TFrame",
            background=self.colors["card"],
            relief="flat",
        )
        style.configure(
            "AltCard.TFrame",
            background=self.colors["card_alt"],
            relief="flat",
        )
        style.configure(
            "Title.TLabel",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "Section.TLabel",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Body.TLabel",
            background=self.colors["card"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardValue.TLabel",
            background=self.colors["card_alt"],
            foreground=self.colors["text"],
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "PomodoroTimer.TLabel",
            background=self.colors["card_alt"],
            foreground=self.colors["success"],
            font=("Segoe UI Semibold", 58),
        )
        style.configure(
            "PomodoroMetric.TLabel",
            background=self.colors["card"],
            foreground=self.colors["success"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "PomodoroCount.TLabel",
            background=self.colors["card_alt"],
            foreground=self.colors["success"],
            font=("Segoe UI Semibold", 20),
        )
        style.configure(
            "Muted.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 10),
            foreground="white",
            background=self.colors["accent"],
            borderwidth=0,
            padding=(14, 10),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.colors["accent_dark"])],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI Semibold", 10),
            foreground=self.colors["text"],
            background=self.colors["card_alt"],
            borderwidth=1,
            bordercolor=self.colors["line"],
            padding=(12, 9),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", self.colors["accent_soft"])],
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI Semibold", 10),
            foreground=self.colors["accent_dark"],
            background="#fff1ef",
            borderwidth=1,
            bordercolor="#f0c9c3",
            padding=(12, 9),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#fde1dc")],
        )
        style.configure(
            "Modern.TCombobox",
            fieldbackground="white",
            background="white",
            foreground=self.colors["text"],
            bordercolor=self.colors["line"],
            arrowcolor=self.colors["accent_dark"],
            padding=8,
        )

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        outer = ttk.Frame(self.root, style="App.TFrame", padding=22)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(outer)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        home_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        home_tab.grid_rowconfigure(1, weight=1)
        home_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(home_tab, text="Inicio")
        self.tab_frames["home"] = home_tab

        rename_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        rename_tab.grid_rowconfigure(2, weight=1)
        rename_tab.grid_columnconfigure(0, weight=1)
        rename_tab.grid_columnconfigure(1, weight=1)
        self.notebook.add(rename_tab, text="Renombrar PDF")
        self.tab_frames["rename"] = rename_tab

        copy_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        copy_tab.grid_rowconfigure(1, weight=1)
        copy_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(copy_tab, text="Copiar propuesta")
        self.tab_frames["copy"] = copy_tab

        clients_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        clients_tab.grid_rowconfigure(1, weight=1)
        clients_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(clients_tab, text="Clientes")
        self.tab_frames["clients"] = clients_tab

        fiscal_template_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        fiscal_template_tab.grid_rowconfigure(1, weight=1)
        fiscal_template_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(fiscal_template_tab, text="Plantilla fiscal")
        self.tab_frames["fiscal_template"] = fiscal_template_tab

        pomodoro_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        pomodoro_tab.grid_rowconfigure(1, weight=1)
        pomodoro_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(pomodoro_tab, text="Pomodoro")
        self.tab_frames["pomodoro"] = pomodoro_tab

        self._build_home_tab(home_tab)
        self._build_header(rename_tab)
        self._build_company_routes(rename_tab)
        self._build_destinations(rename_tab)
        self._build_copy_tab(copy_tab)
        self._build_clients_tab(clients_tab)
        self._build_fiscal_template_tab(fiscal_template_tab)
        self._build_pomodoro_tab(pomodoro_tab)

    def _build_home_tab(self, parent):
        header = ttk.Frame(parent, style="Card.TFrame", padding=26)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=2)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="nw")

        ttk.Label(
            title_block,
            text="Centro de control",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Usa este menu principal para entrar rapido a cada modulo de la aplicacion.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.home_pdf_summary = self._create_info_card(header, 0, 1, "PDF listo", "Ningun archivo")
        self.home_folder_summary = self._create_info_card(header, 0, 2, "Destino", "Sin carpeta")

        content = ttk.Frame(parent, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        modules_panel = ttk.Frame(content, style="Card.TFrame", padding=22)
        modules_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        modules_panel.grid_columnconfigure(0, weight=1)
        modules_panel.grid_columnconfigure(1, weight=1)

        ttk.Label(modules_panel, text="Modulos", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            modules_panel,
            text="Cada tarjeta abre una pestaña distinta para que puedas ir directo a la tarea que necesitas.",
            style="Body.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))

        cards = [
            ("Renombrar PDF", "Extrae datos del archivo y lo mueve al destino elegido.", "rename"),
            ("Copiar propuesta", "Genera nuevas copias de propuestas base con nombre automatico.", "copy"),
            ("Clientes", "Consulta y actualiza la ficha de cada cliente.", "clients"),
            ("Plantilla fiscal", "Lleva versiones, compradores y mensajes de la plantilla fiscal.", "fiscal_template"),
        ]

        for index, (title, description, tab_key) in enumerate(cards):
            row = 2 + (index // 2)
            column = index % 2
            card = ttk.Frame(modules_panel, style="AltCard.TFrame", padding=18)
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (12, 0), pady=(0, 12))
            card.grid_columnconfigure(0, weight=1)
            ttk.Label(card, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(
                card,
                text=description,
                style="Body.TLabel",
                wraplength=300,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(8, 14))
            ttk.Button(
                card,
                text="Abrir modulo",
                style="Primary.TButton",
                command=lambda value=tab_key: self.open_tab(value),
            ).grid(row=2, column=0, sticky="w")

        summary_panel = ttk.Frame(content, style="Card.TFrame", padding=22)
        summary_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        summary_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(summary_panel, text="Resumen rapido", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            summary_panel,
            text="Una vista simple del estado actual antes de entrar a cada herramienta.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        self.home_clients_summary = self._create_info_card(summary_panel, 2, 0, "Clientes guardados", "0")
        ttk.Button(
            summary_panel,
            text="Ir a Renombrar PDF",
            style="Secondary.TButton",
            command=lambda: self.open_tab("rename"),
        ).grid(row=3, column=0, sticky="ew", pady=(18, 0))

    def open_tab(self, tab_key):
        if self.notebook is None:
            return
        target = self.tab_frames.get(tab_key)
        if target is not None:
            self.notebook.select(target)

    def _build_home_tab(self, parent):
        header = ttk.Frame(parent, style="Card.TFrame", padding=26)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=2)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="nw")

        ttk.Label(
            title_block,
            text="Centro de control",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Usa este menu principal para entrar rapido a cada modulo de la aplicacion.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.home_pdf_summary = self._create_info_card(header, 0, 1, "PDF listo", "Ningun archivo")
        self.home_folder_summary = self._create_info_card(header, 0, 2, "Destino", "Sin carpeta")

        content = ttk.Frame(parent, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=3)
        content.grid_rowconfigure(1, weight=2)

        primary_panel = ttk.Frame(content, style="Card.TFrame", padding=22)
        primary_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        primary_panel.grid_columnconfigure(0, weight=1)
        primary_panel.grid_columnconfigure(1, weight=1)

        ttk.Label(primary_panel, text="Modulos principales", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            primary_panel,
            text="Las pestañas con icono aparecen aqui como accesos principales del centro de control.",
            style="Body.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 18))

        primary_cards = [
            ("Renombrar PDF", "Extrae datos del archivo y lo mueve al destino elegido.", "rename", "renombrar PDF.png"),
            ("Copiar propuesta", "Genera nuevas copias de propuestas base con nombre automatico.", "copy", "COPIAR PROPUESTA.png"),
            ("Clientes", "Consulta y actualiza la ficha de cada cliente.", "clients", "CLIENTES.png"),
        ]

        for index, (title, description, tab_key, icon_name) in enumerate(primary_cards):
            row = 2 + (index // 2)
            column = index % 2
            card = ttk.Frame(primary_panel, style="AltCard.TFrame", padding=18)
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (12, 0), pady=(0, 12))
            card.grid_columnconfigure(0, weight=1)

            icon = self._load_home_icon(icon_name)
            if icon is not None:
                icon_label = ttk.Label(card, image=icon, style="Body.TLabel")
                icon_label.image = icon
                icon_label.grid(row=0, column=0, sticky="w", pady=(0, 12))

            ttk.Label(card, text=title, style="Section.TLabel").grid(row=1, column=0, sticky="w")
            ttk.Label(
                card,
                text=description,
                style="Body.TLabel",
                wraplength=300,
                justify="left",
            ).grid(row=2, column=0, sticky="w", pady=(8, 14))
            ttk.Button(
                card,
                text="Abrir modulo",
                style="Primary.TButton",
                command=lambda value=tab_key: self.open_tab(value),
            ).grid(row=3, column=0, sticky="w")

        secondary_panel = ttk.Frame(content, style="Card.TFrame", padding=22)
        secondary_panel.grid(row=1, column=0, sticky="nsew")
        secondary_panel.grid_columnconfigure(0, weight=1)
        secondary_panel.grid_columnconfigure(1, weight=1)

        ttk.Label(secondary_panel, text="Modulos secundarios", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            secondary_panel,
            text="Estas herramientas siguen disponibles y se abren desde aqui cuando las necesites.",
            style="Body.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))

        secondary_cards = [
            ("Plantilla fiscal", "Lleva versiones, compradores y mensajes de la plantilla fiscal.", "fiscal_template"),
            ("Pomodoro", "Controla ciclos de 25 minutos y descansos automaticos por dia.", "pomodoro"),
        ]

        for index, (title, description, tab_key) in enumerate(secondary_cards):
            row = 2 + (index // 2)
            column = index % 2
            card = ttk.Frame(secondary_panel, style="AltCard.TFrame", padding=16)
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (12, 0), pady=(0, 12))
            card.grid_columnconfigure(0, weight=1)
            ttk.Label(card, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(
                card,
                text=description,
                style="Body.TLabel",
                wraplength=300,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(6, 12))
            ttk.Button(
                card,
                text="Abrir modulo",
                style="Secondary.TButton",
                command=lambda value=tab_key: self.open_tab(value),
            ).grid(row=2, column=0, sticky="w")

    def _load_home_icon(self, file_name, target_size=56):
        if file_name in self.home_icon_images:
            return self.home_icon_images[file_name]

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
        if not os.path.exists(icon_path):
            return None

        try:
            image = tk.PhotoImage(file=icon_path)
        except tk.TclError:
            return None

        width = max(1, image.width())
        scale = max(1, round(width / target_size))
        if scale > 1:
            image = image.subsample(scale, scale)

        self.home_icon_images[file_name] = image
        return image

    def _build_pomodoro_tab(self, parent):
        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Pomodoro", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Ciclos de 25 minutos con descansos automaticos y conteo diario.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        metrics = ttk.Frame(header, style="Card.TFrame")
        metrics.grid(row=0, column=1, rowspan=2, sticky="e")
        self.pomodoro_minutes_label = ttk.Label(metrics, text="MINUTOS: 0", style="PomodoroMetric.TLabel")
        self.pomodoro_minutes_label.grid(row=0, column=0, sticky="e", padx=(0, 18))
        self.pomodoro_hours_label = ttk.Label(metrics, text="HORAS: 0:00", style="PomodoroMetric.TLabel")
        self.pomodoro_hours_label.grid(row=0, column=1, sticky="e", padx=(0, 18))
        self.pomodoro_completed_label = ttk.Label(metrics, text="POMODOROS: 0", style="PomodoroMetric.TLabel")
        self.pomodoro_completed_label.grid(row=0, column=2, sticky="e")

        pomodoro_notebook = ttk.Notebook(parent)
        pomodoro_notebook.grid(row=1, column=0, sticky="nsew")

        timer_page = ttk.Frame(pomodoro_notebook, style="App.TFrame", padding=0)
        timer_page.grid_rowconfigure(0, weight=1)
        timer_page.grid_columnconfigure(0, weight=1)
        pomodoro_notebook.add(timer_page, text="Temporizador")

        settings_page = ttk.Frame(pomodoro_notebook, style="App.TFrame", padding=0)
        settings_page.grid_rowconfigure(0, weight=1)
        settings_page.grid_columnconfigure(0, weight=1)
        pomodoro_notebook.add(settings_page, text="Configuracion")

        tasks_page = ttk.Frame(pomodoro_notebook, style="App.TFrame", padding=0)
        tasks_page.grid_rowconfigure(0, weight=1)
        tasks_page.grid_columnconfigure(0, weight=1)
        pomodoro_notebook.add(tasks_page, text="Tareas")

        flows_page = ttk.Frame(pomodoro_notebook, style="App.TFrame", padding=0)
        flows_page.grid_rowconfigure(0, weight=1)
        flows_page.grid_columnconfigure(0, weight=1)
        pomodoro_notebook.add(flows_page, text="Flujos")

        stage = ttk.Frame(timer_page, style="Card.TFrame", padding=28)
        stage.grid(row=0, column=0, sticky="nsew")
        stage.grid_columnconfigure(0, weight=1)
        stage.grid_columnconfigure(1, weight=0)
        stage.grid_rowconfigure(0, weight=1)

        timer_card = ttk.Frame(stage, style="AltCard.TFrame", padding=26)
        timer_card.grid(row=0, column=0)
        timer_card.grid_columnconfigure(0, weight=1)

        self.pomodoro_phase_label = ttk.Label(
            timer_card,
            text="Pomodoro",
            style="CardValue.TLabel",
            anchor="center",
        )
        self.pomodoro_phase_label.grid(row=0, column=0, sticky="ew")

        self.pomodoro_timer_label = ttk.Label(
            timer_card,
            text="25:00",
            style="PomodoroTimer.TLabel",
            anchor="center",
            width=6,
        )
        self.pomodoro_timer_label.grid(row=1, column=0, sticky="ew", pady=(10, 8))

        actions = ttk.Frame(timer_card, style="AltCard.TFrame")
        actions.grid(row=2, column=0)
        self.pomodoro_toggle_button = ttk.Button(
            actions,
            text="Iniciar",
            style="Primary.TButton",
            command=self.toggle_pomodoro_running,
        )
        self.pomodoro_toggle_button.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            actions,
            text="Siguiente",
            style="Secondary.TButton",
            command=self.skip_pomodoro_phase,
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            actions,
            text="Reiniciar dia",
            style="Danger.TButton",
            command=self.reset_pomodoro_day,
        ).grid(row=0, column=2)

        self.pomodoro_count_label = ttk.Label(
            timer_card,
            text="#1",
            style="PomodoroCount.TLabel",
            anchor="center",
        )
        self.pomodoro_count_label.grid(row=3, column=0, sticky="ew", pady=(14, 0))

        active_task_row = ttk.Frame(timer_card, style="AltCard.TFrame")
        active_task_row.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        active_task_row.grid_columnconfigure(0, weight=1)
        self.pomodoro_active_task_label = ttk.Label(
            active_task_row,
            text="Sin tarea seleccionada",
            style="Section.TLabel",
            anchor="center",
            wraplength=300,
            justify="center",
        )
        self.pomodoro_active_task_label.grid(row=0, column=0, sticky="ew")
        self.pomodoro_clear_active_task_button = ttk.Button(
            active_task_row,
            text="Quitar",
            style="Secondary.TButton",
            command=self.clear_active_pomodoro_task,
            state="disabled",
            width=8,
        )
        self.pomodoro_clear_active_task_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
        self.pomodoro_active_task_count_label = ttk.Label(
            timer_card,
            text="Pomodoros en esta tarea: 0",
            style="Body.TLabel",
            anchor="center",
        )
        self.pomodoro_active_task_count_label.grid(row=5, column=0, sticky="ew", pady=(6, 0))

        self.pomodoro_active_flow_tasks_frame = ttk.Frame(timer_card, style="AltCard.TFrame")
        self.pomodoro_active_flow_tasks_frame.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        self.pomodoro_active_flow_tasks_frame.grid_columnconfigure(0, weight=1)

        timer_tasks_panel = ttk.Frame(stage, style="AltCard.TFrame", padding=18)
        timer_tasks_panel.grid(row=0, column=1, sticky="ns", padx=(24, 0))
        timer_tasks_panel.grid_columnconfigure(0, weight=1)
        timer_tasks_panel.grid_rowconfigure(1, weight=1)

        ttk.Label(
            timer_tasks_panel,
            text="Tareas y flujos",
            style="Section.TLabel",
            anchor="center",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 14))

        self.pomodoro_timer_tasks_canvas = tk.Canvas(
            timer_tasks_panel,
            bg=self.colors["card_alt"],
            highlightthickness=0,
            relief="flat",
            borderwidth=0,
        )
        self.pomodoro_timer_tasks_canvas.grid(row=1, column=0, sticky="nsew")
        self.pomodoro_timer_tasks_rows_frame = ttk.Frame(self.pomodoro_timer_tasks_canvas, style="AltCard.TFrame")
        self.pomodoro_timer_tasks_rows_window = self.pomodoro_timer_tasks_canvas.create_window(
            (0, 0),
            window=self.pomodoro_timer_tasks_rows_frame,
            anchor="nw",
        )
        timer_tasks_scroll = ttk.Scrollbar(
            timer_tasks_panel,
            orient="vertical",
            command=self.pomodoro_timer_tasks_canvas.yview,
        )
        timer_tasks_scroll.grid(row=1, column=1, sticky="ns")
        self.pomodoro_timer_tasks_canvas.configure(yscrollcommand=timer_tasks_scroll.set, width=170, height=260)
        self.pomodoro_timer_tasks_rows_frame.bind(
            "<Configure>",
            lambda _event: self.pomodoro_timer_tasks_canvas.configure(
                scrollregion=self.pomodoro_timer_tasks_canvas.bbox("all")
            ),
        )
        self.pomodoro_timer_tasks_canvas.bind(
            "<Configure>",
            lambda event: self.pomodoro_timer_tasks_canvas.itemconfigure(
                self.pomodoro_timer_tasks_rows_window,
                width=event.width,
            ),
        )

        self._build_pomodoro_settings_tab(settings_page)
        self._build_pomodoro_tasks_tab(tasks_page)
        self._build_pomodoro_flows_tab(flows_page)

        self.refresh_pomodoro_ui()

    def _build_pomodoro_tasks_tab(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=28)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ttk.Label(panel, text="Tareas", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        form_row = ttk.Frame(panel, style="Card.TFrame")
        form_row.grid(row=1, column=0, sticky="ew", pady=(14, 16))
        form_row.grid_columnconfigure(0, weight=1)

        self.pomodoro_task_entry = ttk.Entry(
            form_row,
            textvariable=self.pomodoro_task_title_var,
            font=("Segoe UI", 11),
        )
        self.pomodoro_task_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.pomodoro_task_entry.bind("<Return>", self.add_pomodoro_task)
        ttk.Button(
            form_row,
            text="Agregar",
            style="Primary.TButton",
            command=self.add_pomodoro_task,
        ).grid(row=0, column=1, sticky="ew")

        list_panel = ttk.Frame(panel, style="AltCard.TFrame", padding=16)
        list_panel.grid(row=2, column=0, sticky="nsew")
        list_panel.grid_columnconfigure(0, weight=1)
        list_panel.grid_rowconfigure(0, weight=1)

        self.pomodoro_tasks_canvas = tk.Canvas(
            list_panel,
            bg=self.colors["card_alt"],
            highlightthickness=0,
            relief="flat",
            borderwidth=0,
        )
        self.pomodoro_tasks_canvas.grid(row=0, column=0, sticky="nsew")
        self.pomodoro_tasks_rows_frame = ttk.Frame(self.pomodoro_tasks_canvas, style="AltCard.TFrame")
        self.pomodoro_tasks_rows_window = self.pomodoro_tasks_canvas.create_window(
            (0, 0),
            window=self.pomodoro_tasks_rows_frame,
            anchor="nw",
        )

        tasks_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.pomodoro_tasks_canvas.yview)
        tasks_scroll.grid(row=0, column=1, sticky="ns")
        self.pomodoro_tasks_canvas.configure(yscrollcommand=tasks_scroll.set)
        self.pomodoro_tasks_rows_frame.bind(
            "<Configure>",
            lambda _event: self.pomodoro_tasks_canvas.configure(
                scrollregion=self.pomodoro_tasks_canvas.bbox("all")
            ),
        )
        self.pomodoro_tasks_canvas.bind(
            "<Configure>",
            lambda event: self.pomodoro_tasks_canvas.itemconfigure(
                self.pomodoro_tasks_rows_window,
                width=event.width,
            ),
        )

        self.refresh_pomodoro_tasks_list()

    def _build_pomodoro_flows_tab(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=28)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ttk.Label(panel, text="Flujos", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        form_row = ttk.Frame(panel, style="Card.TFrame")
        form_row.grid(row=1, column=0, sticky="ew", pady=(14, 16))
        form_row.grid_columnconfigure(0, weight=1)
        flow_entry = ttk.Entry(form_row, textvariable=self.pomodoro_flow_name_var, font=("Segoe UI", 11))
        flow_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        flow_entry.bind("<Return>", self.add_pomodoro_flow)
        ttk.Button(
            form_row,
            text="Crear flujo",
            style="Primary.TButton",
            command=self.add_pomodoro_flow,
        ).grid(row=0, column=1, sticky="ew")

        list_panel = ttk.Frame(panel, style="AltCard.TFrame", padding=16)
        list_panel.grid(row=2, column=0, sticky="nsew")
        list_panel.grid_columnconfigure(0, weight=1)
        list_panel.grid_rowconfigure(0, weight=1)
        self.pomodoro_flows_canvas = tk.Canvas(
            list_panel, bg=self.colors["card_alt"], highlightthickness=0, relief="flat", borderwidth=0
        )
        self.pomodoro_flows_canvas.grid(row=0, column=0, sticky="nsew")
        self.pomodoro_flows_rows_frame = ttk.Frame(self.pomodoro_flows_canvas, style="AltCard.TFrame")
        self.pomodoro_flows_rows_window = self.pomodoro_flows_canvas.create_window(
            (0, 0), window=self.pomodoro_flows_rows_frame, anchor="nw"
        )
        flows_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.pomodoro_flows_canvas.yview)
        flows_scroll.grid(row=0, column=1, sticky="ns")
        self.pomodoro_flows_canvas.configure(yscrollcommand=flows_scroll.set)
        self.pomodoro_flows_rows_frame.bind(
            "<Configure>",
            lambda _event: self.pomodoro_flows_canvas.configure(scrollregion=self.pomodoro_flows_canvas.bbox("all")),
        )
        self.pomodoro_flows_canvas.bind(
            "<Configure>",
            lambda event: self.pomodoro_flows_canvas.itemconfigure(self.pomodoro_flows_rows_window, width=event.width),
        )
        self.refresh_pomodoro_flow_rows()

    def _build_pomodoro_settings_tab(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=28)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        ttk.Label(panel, text="Configuracion", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Elige si el siguiente tramo del ciclo inicia solo o queda esperando en pausa.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        options = ttk.Frame(panel, style="AltCard.TFrame", padding=18)
        options.grid(row=2, column=0, sticky="ew")
        options.grid_columnconfigure(0, weight=1)

        ttk.Checkbutton(
            options,
            text="Comenzar el descanso automaticamente al finalizar la pomodoro",
            variable=self.pomodoro_auto_start_break_var,
            command=self.save_config,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Checkbutton(
            options,
            text="Comenzar la pomodoro automaticamente al acabar el descanso",
            variable=self.pomodoro_auto_start_work_var,
            command=self.save_config,
        ).grid(row=1, column=0, sticky="w")

    def normalize_pomodoro_task_record(self, task):
        if not isinstance(task, dict):
            return None

        title = str(task.get("title", "")).strip()
        if not title:
            return None

        try:
            completed_pomodoros = max(0, int(task.get("completed_pomodoros", 0)))
        except (TypeError, ValueError):
            completed_pomodoros = 0

        return {
            "id": str(task.get("id") or uuid.uuid4()),
            "title": title,
            "completed_pomodoros": completed_pomodoros,
        }

    def load_pomodoro_flows_from_db(self):
        try:
            self.pomodoro_flows = self.services.pomodoro.flows()
        except Exception as exc:
            self.pomodoro_flows = []
            self.log(f"[ERROR] No se pudieron cargar los flujos de Pomodoro. Detalle: {exc}")

    def get_pomodoro_flow_progress(self, flow):
        tasks = flow.get("tasks", []) if flow else []
        completed = sum(1 for task in tasks if task.get("completed"))
        percentage = round((completed / len(tasks)) * 100) if tasks else 0
        return completed, len(tasks), percentage

    def add_pomodoro_flow(self, _event=None):
        name = self.pomodoro_flow_name_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Escribe un nombre para el flujo.")
            return "break"
        try:
            self.services.pomodoro.save_flow({"name": name})
        except ValueError as exc:
            messagebox.showerror("Error", f"No se pudo crear el flujo.\n{exc}")
            return "break"
        self.pomodoro_flow_name_var.set("")
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.log(f"[INFO] Flujo de Pomodoro creado: {name}")
        return "break"

    def set_task_in_pomodoro_flow(self, flow_id, task_id, assigned):
        self.services.pomodoro.assign(flow_id, task_id, assigned)
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()

    def set_pomodoro_flow_task_completed(self, flow_id, task_id, completed):
        self.services.pomodoro.complete(flow_id, task_id, completed)
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()

    def get_active_pomodoro_flow(self):
        flow_id = self.pomodoro_state.get("selected_flow_id")
        return next((flow for flow in self.pomodoro_flows if flow.get("id") == flow_id), None)

    def select_pomodoro_flow_by_id(self, flow_id):
        if not any(flow.get("id") == flow_id for flow in self.pomodoro_flows):
            return
        self.pomodoro_state["selected_flow_id"] = flow_id
        self.pomodoro_state["selected_task_id"] = None
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()
        self.save_config()

    def delete_pomodoro_flow_by_id(self, flow_id):
        flow = next((item for item in self.pomodoro_flows if item.get("id") == flow_id), None)
        if not flow:
            return
        self.services.pomodoro.delete_flow(flow_id)
        if self.pomodoro_state.get("selected_flow_id") == flow_id:
            self.pomodoro_state["selected_flow_id"] = None
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()
        self.save_config()

    def refresh_pomodoro_flow_rows(self):
        if not hasattr(self, "pomodoro_flows_rows_frame"):
            return
        for child in self.pomodoro_flows_rows_frame.winfo_children():
            child.destroy()
        if not self.pomodoro_flows:
            ttk.Label(self.pomodoro_flows_rows_frame, text="No hay flujos.", style="Body.TLabel").grid(
                row=0, column=0, sticky="w", padx=6, pady=6
            )
            return
        self.pomodoro_flows_rows_frame.grid_columnconfigure(0, weight=1)
        for index, flow in enumerate(self.pomodoro_flows):
            completed, total, percentage = self.get_pomodoro_flow_progress(flow)
            card = ttk.Frame(self.pomodoro_flows_rows_frame, style="AltCard.TFrame", padding=14)
            card.grid(row=index, column=0, sticky="ew", pady=(0, 12))
            card.grid_columnconfigure(0, weight=1)
            ttk.Label(card, text=flow["name"], style="Section.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(
                card, text=f"{total} tareas · {completed}/{total} completadas · {percentage}%", style="Body.TLabel"
            ).grid(row=1, column=0, sticky="w", pady=(3, 8))
            ttk.Button(
                card, text="Usar en Pomodoro", style="Primary.TButton",
                command=lambda flow_id=flow["id"]: self.select_pomodoro_flow_by_id(flow_id),
            ).grid(row=0, column=1, rowspan=2, padx=(10, 8))
            ttk.Button(
                card, text="Eliminar", style="Danger.TButton",
                command=lambda flow_id=flow["id"]: self.delete_pomodoro_flow_by_id(flow_id),
            ).grid(row=0, column=2, rowspan=2)
            assigned_ids = {task["id"] for task in flow["tasks"]}
            tasks_box = ttk.Frame(card, style="AltCard.TFrame")
            tasks_box.grid(row=2, column=0, columnspan=3, sticky="ew")
            if not self.pomodoro_tasks:
                ttk.Label(tasks_box, text="Crea tareas para poder asignarlas.", style="Body.TLabel").grid(row=0, column=0, sticky="w")
            for task_index, task in enumerate(self.pomodoro_tasks):
                assigned_var = tk.BooleanVar(value=task["id"] in assigned_ids)
                ttk.Checkbutton(
                    tasks_box,
                    text=task["title"],
                    variable=assigned_var,
                    command=lambda f=flow["id"], t=task["id"], v=assigned_var: self.set_task_in_pomodoro_flow(f, t, v.get()),
                ).grid(row=task_index, column=0, sticky="w", pady=2)

    def load_pomodoro_tasks_from_db(self):
        try:
            self.pomodoro_tasks = self.services.pomodoro.tasks()
        except Exception as exc:
            self.pomodoro_tasks = []
            self.log(f"[ERROR] No se pudieron cargar las tareas de Pomodoro. Detalle: {exc}")

    def save_pomodoro_task_to_db(self, payload):
        normalized = self.normalize_pomodoro_task_record(payload)
        if not normalized:
            return False
        try:
            self.services.pomodoro.save_task(normalized)
            return True
        except ValueError as exc:
            self.log(f"[ERROR] No se pudo guardar la tarea de Pomodoro. Detalle: {exc}")
            return False

    def delete_pomodoro_task_from_db(self, task_id):
        return self.services.pomodoro.delete_task(task_id)

    def increment_pomodoro_task_count_in_db(self, task_id):
        if task_id:
            self.services.pomodoro.increment_task(task_id)

    def add_pomodoro_task(self, _event=None):
        title = self.pomodoro_task_title_var.get().strip()
        if not title:
            messagebox.showwarning("Aviso", "Escribe una tarea para agregarla.")
            return "break"

        task_id = str(uuid.uuid4())
        if not self.save_pomodoro_task_to_db({"id": task_id, "title": title}):
            messagebox.showerror("Error", "No se pudo guardar la tarea.")
            return "break"

        self.pomodoro_state["selected_task_id"] = task_id
        self.pomodoro_state["selected_flow_id"] = None
        self.pomodoro_task_title_var.set("")
        self.load_pomodoro_tasks_from_db()
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()
        self.save_config()
        self.log(f"[INFO] Tarea de Pomodoro agregada: {title}")
        return "break"

    def format_pomodoro_task_label(self, task):
        title = task.get("title", "")
        count = int(task.get("completed_pomodoros", 0) or 0)
        return f"{title}  ({count})"

    def refresh_pomodoro_task_rows(self):
        if not hasattr(self, "pomodoro_tasks_rows_frame"):
            return

        for child in self.pomodoro_tasks_rows_frame.winfo_children():
            child.destroy()

        selected_task_id = self.pomodoro_state.get("selected_task_id")
        if not self.pomodoro_tasks:
            ttk.Label(
                self.pomodoro_tasks_rows_frame,
                text="No hay tareas.",
                style="Body.TLabel",
            ).grid(row=0, column=0, sticky="w", padx=6, pady=6)
            return

        self.pomodoro_tasks_rows_frame.grid_columnconfigure(0, weight=1)
        for row_index, task in enumerate(self.pomodoro_tasks):
            is_active = task.get("id") == selected_task_id
            row = ttk.Frame(self.pomodoro_tasks_rows_frame, style="Card.TFrame" if is_active else "AltCard.TFrame", padding=12)
            row.grid(row=row_index, column=0, sticky="ew", pady=(0, 10))
            row.grid_columnconfigure(0, weight=1)

            task_text = task.get("title", "")
            count = int(task.get("completed_pomodoros", 0) or 0)
            if is_active:
                task_text = f"{task_text}  - activa"
            ttk.Label(
                row,
                text=task_text,
                style="Section.TLabel",
                wraplength=520,
                justify="left",
            ).grid(row=0, column=0, sticky="w")
            ttk.Label(
                row,
                text=f"Pomodoros: {count}",
                style="Body.TLabel",
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))
            ttk.Button(
                row,
                text="Agregar a Pomodoro",
                style="Primary.TButton",
                command=lambda task_id=task.get("id"): self.select_pomodoro_task_by_id(task_id),
            ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 8))
            ttk.Button(
                row,
                text="Eliminar",
                style="Danger.TButton",
                command=lambda task_id=task.get("id"): self.delete_pomodoro_task_by_id(task_id),
            ).grid(row=0, column=2, rowspan=2, sticky="e")

    def refresh_pomodoro_timer_task_rows(self):
        if not hasattr(self, "pomodoro_timer_tasks_rows_frame"):
            return

        for child in self.pomodoro_timer_tasks_rows_frame.winfo_children():
            child.destroy()

        selected_task_id = self.pomodoro_state.get("selected_task_id")
        if not self.pomodoro_tasks and not self.pomodoro_flows:
            ttk.Label(
                self.pomodoro_timer_tasks_rows_frame,
                text="No hay tareas ni flujos.",
                style="Body.TLabel",
            ).grid(row=0, column=0, sticky="w", padx=4, pady=4)
            return

        self.pomodoro_timer_tasks_rows_frame.grid_columnconfigure(0, weight=1)
        row_index = 0
        for flow in self.pomodoro_flows:
            is_active = flow.get("id") == self.pomodoro_state.get("selected_flow_id")
            _completed, total, percentage = self.get_pomodoro_flow_progress(flow)
            row = ttk.Frame(
                self.pomodoro_timer_tasks_rows_frame,
                style="Card.TFrame" if is_active else "AltCard.TFrame",
                padding=(6, 5),
            )
            row.grid(row=row_index, column=0, sticky="ew", pady=(0, 7))
            row.grid_columnconfigure(0, weight=1)
            ttk.Label(
                row, text=f"FLUJO\n{flow['name']}\n{total} tareas · {percentage}%", style="Body.TLabel",
                anchor="center", justify="center", wraplength=100,
            ).grid(row=0, column=0, sticky="ew")
            ttk.Button(
                row, text="+", style="Primary.TButton", width=3,
                command=lambda flow_id=flow["id"]: self.select_pomodoro_flow_by_id(flow_id),
            ).grid(row=0, column=1, sticky="e", padx=(6, 3))
            row_index += 1

        for task in self.pomodoro_tasks:
            is_active = task.get("id") == selected_task_id
            row = ttk.Frame(
                self.pomodoro_timer_tasks_rows_frame,
                style="Card.TFrame" if is_active else "AltCard.TFrame",
                padding=(6, 5),
            )
            row.grid(row=row_index, column=0, sticky="ew", pady=(0, 7))
            row.grid_columnconfigure(0, weight=1)

            title = task.get("title", "")
            count = int(task.get("completed_pomodoros", 0) or 0)
            ttk.Label(
                row,
                text=f"{title}\n{count}",
                style="Body.TLabel",
                width=12,
                anchor="center",
                justify="center",
                wraplength=78,
            ).grid(row=0, column=0, sticky="ew")
            ttk.Button(
                row,
                text="+",
                style="Primary.TButton",
                width=3,
                command=lambda task_id=task.get("id"): self.select_pomodoro_task_by_id(task_id),
            ).grid(row=0, column=1, sticky="e", padx=(6, 3))
            ttk.Button(
                row,
                text="X",
                style="Danger.TButton",
                width=3,
                command=lambda task_id=task.get("id"): self.delete_pomodoro_task_by_id(task_id),
            ).grid(row=0, column=2, sticky="e")
            row_index += 1

    def refresh_pomodoro_tasks_list(self):
        self.refreshing_pomodoro_task_lists = True
        try:
            self.refresh_pomodoro_task_rows()
            self.refresh_pomodoro_timer_task_rows()
            self.refresh_pomodoro_flow_rows()
        finally:
            self.refreshing_pomodoro_task_lists = False

    def get_active_pomodoro_task(self):
        selected_task_id = self.pomodoro_state.get("selected_task_id")
        return next((task for task in self.pomodoro_tasks if task.get("id") == selected_task_id), None)

    def select_pomodoro_task(self, task):
        if not task:
            return
        if self.pomodoro_state.get("selected_task_id") == task.get("id"):
            return
        self.pomodoro_state["selected_task_id"] = task.get("id")
        self.pomodoro_state["selected_flow_id"] = None
        self.sync_pomodoro_task_selection()
        self.refresh_pomodoro_ui()
        self.save_config()

    def select_pomodoro_task_by_id(self, task_id):
        if self.pomodoro_state.get("selected_task_id") == task_id:
            return
        task = next((item for item in self.pomodoro_tasks if item.get("id") == task_id), None)
        self.select_pomodoro_task(task)
        self.refresh_pomodoro_task_rows()
        self.refresh_pomodoro_timer_task_rows()

    def sync_pomodoro_task_selection(self):
        self.refresh_pomodoro_timer_task_rows()

    def clear_active_pomodoro_task(self):
        if not self.pomodoro_state.get("selected_task_id") and not self.pomodoro_state.get("selected_flow_id"):
            return

        self.pomodoro_state["selected_task_id"] = None
        self.pomodoro_state["selected_flow_id"] = None
        self.refresh_pomodoro_task_rows()
        self.refresh_pomodoro_timer_task_rows()
        self.refresh_pomodoro_ui()
        self.save_config()

    def delete_pomodoro_task_by_id(self, task_id):
        selected_task = next((task for task in self.pomodoro_tasks if task.get("id") == task_id), None)
        if not selected_task:
            return "break"

        self.delete_pomodoro_task_from_db(selected_task["id"])
        if self.pomodoro_state.get("selected_task_id") == selected_task.get("id"):
            self.pomodoro_state["selected_task_id"] = None
        self.load_pomodoro_tasks_from_db()
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()
        self.save_config()
        self.log(f"[INFO] Tarea de Pomodoro eliminada: {selected_task['title']}")
        return "break"

    def delete_selected_pomodoro_task(self, _event=None):
        selected_task = self.get_active_pomodoro_task()
        if not selected_task:
            return "break"
        return self.delete_pomodoro_task_by_id(selected_task["id"])

    def get_default_pomodoro_state(self):
        return {
            "date": date.today().isoformat(),
            "completed_count": 0,
            "phase": "work",
            "remaining_seconds": self.pomodoro_work_seconds,
            "running": False,
            "phase_end_at": None,
            "ten_minute_alert_played": False,
            "selected_task_id": None,
            "selected_flow_id": None,
        }

    def normalize_pomodoro_state(self, data):
        state = self.get_default_pomodoro_state()
        if not isinstance(data, dict):
            return state
        if data.get("date") != date.today().isoformat():
            return state

        completed_count = data.get("completed_count", 0)
        try:
            completed_count = max(0, int(completed_count))
        except (TypeError, ValueError):
            completed_count = 0

        phase = data.get("phase", "work")
        if phase not in {"work", "break"}:
            phase = "work"

        default_duration = self.get_pomodoro_phase_duration(phase, completed_count)
        remaining_seconds = data.get("remaining_seconds", default_duration)
        try:
            remaining_seconds = int(remaining_seconds)
        except (TypeError, ValueError):
            remaining_seconds = default_duration
        remaining_seconds = max(1, min(remaining_seconds, default_duration))
        default_alert_played = phase == "work" and remaining_seconds <= self.pomodoro_warning_seconds
        ten_minute_alert_played = bool(data.get("ten_minute_alert_played", default_alert_played))
        selected_task_id = data.get("selected_task_id")
        selected_task_id = str(selected_task_id) if selected_task_id else None
        selected_flow_id = data.get("selected_flow_id")
        selected_flow_id = str(selected_flow_id) if selected_flow_id else None

        state.update(
            {
                "completed_count": completed_count,
                "phase": phase,
                "remaining_seconds": remaining_seconds,
                "running": False,
                "phase_end_at": None,
                "ten_minute_alert_played": ten_minute_alert_played,
                "selected_task_id": selected_task_id,
                "selected_flow_id": selected_flow_id,
            }
        )
        return state

    def get_pomodoro_settings(self):
        return {
            "auto_start_break": bool(self.pomodoro_auto_start_break_var.get()),
            "auto_start_work": bool(self.pomodoro_auto_start_work_var.get()),
        }

    def load_pomodoro_settings(self, data):
        if not isinstance(data, dict):
            return
        self.pomodoro_auto_start_break_var.set(self.parse_config_bool(data.get("auto_start_break"), True))
        self.pomodoro_auto_start_work_var.set(self.parse_config_bool(data.get("auto_start_work"), True))

    def parse_config_bool(self, value, default=False):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "si", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def _on_pomodoro_setting_change(self, *_args):
        if hasattr(self, "config_path"):
            self.save_config()

    def get_pomodoro_phase_duration(self, phase=None, completed_count=None):
        phase = phase or self.pomodoro_state.get("phase", "work")
        completed_count = self.pomodoro_state.get("completed_count", 0) if completed_count is None else completed_count
        if phase == "work":
            return self.pomodoro_work_seconds
        return self.pomodoro_long_break_seconds if completed_count and completed_count % 4 == 0 else self.pomodoro_short_break_seconds

    def get_pomodoro_remaining_seconds(self):
        if self.pomodoro_state.get("running") and self.pomodoro_state.get("phase_end_at"):
            return max(0, int(self.pomodoro_state["phase_end_at"] - time.time() + 0.999))
        return max(0, int(self.pomodoro_state.get("remaining_seconds", self.pomodoro_work_seconds)))

    def get_serializable_pomodoro_state(self):
        self.ensure_pomodoro_today()
        state = dict(self.pomodoro_state)
        state["remaining_seconds"] = self.get_pomodoro_remaining_seconds()
        state.pop("phase_end_at", None)
        return state

    def ensure_pomodoro_today(self):
        if self.pomodoro_state.get("date") == date.today().isoformat():
            return
        self.pomodoro_state = self.get_default_pomodoro_state()

    def start_pomodoro_tick(self):
        if self.pomodoro_after_id is not None:
            try:
                self.root.after_cancel(self.pomodoro_after_id)
            except tk.TclError:
                pass
        self.pomodoro_tick()

    def pomodoro_tick(self):
        self.ensure_pomodoro_today()
        if self.pomodoro_state.get("running"):
            remaining = self.get_pomodoro_remaining_seconds()
            if (
                self.pomodoro_state.get("phase") == "work"
                and 0 < remaining <= self.pomodoro_warning_seconds
                and not self.pomodoro_state.get("ten_minute_alert_played")
            ):
                self.pomodoro_state["ten_minute_alert_played"] = True
                self.play_pomodoro_sound("faltan 10 minutos")
                self.save_config()
            guard = 0
            while self.get_pomodoro_remaining_seconds() <= 0 and guard < 8:
                self.complete_pomodoro_phase()
                guard += 1
            self.pomodoro_state["remaining_seconds"] = self.get_pomodoro_remaining_seconds()
        self.refresh_pomodoro_ui()
        self.pomodoro_after_id = self.root.after(1000, self.pomodoro_tick)

    def toggle_pomodoro_running(self):
        self.ensure_pomodoro_today()
        if self.pomodoro_state.get("running"):
            self.pomodoro_state["remaining_seconds"] = self.get_pomodoro_remaining_seconds()
            self.pomodoro_state["running"] = False
            self.pomodoro_state["phase_end_at"] = None
        else:
            remaining = self.get_pomodoro_remaining_seconds()
            if remaining <= 0:
                remaining = self.get_pomodoro_phase_duration()
            self.pomodoro_state["remaining_seconds"] = remaining
            if self.pomodoro_state.get("phase") == "work" and remaining > self.pomodoro_warning_seconds:
                self.pomodoro_state["ten_minute_alert_played"] = False
            self.pomodoro_state["running"] = True
            self.pomodoro_state["phase_end_at"] = time.time() + remaining
        self.save_config()
        self.refresh_pomodoro_ui()

    def complete_pomodoro_phase(self):
        phase = self.pomodoro_state.get("phase", "work")
        if phase == "work":
            self.pomodoro_state["completed_count"] = self.pomodoro_state.get("completed_count", 0) + 1
            selected_task_id = self.pomodoro_state.get("selected_task_id")
            if selected_task_id:
                self.increment_pomodoro_task_count_in_db(selected_task_id)
                self.load_pomodoro_tasks_from_db()
                self.refresh_pomodoro_tasks_list()
            self.pomodoro_state["phase"] = "break"
            should_continue = bool(self.pomodoro_auto_start_break_var.get())
            sound_name = "finalizo"
        else:
            self.pomodoro_state["phase"] = "work"
            should_continue = bool(self.pomodoro_auto_start_work_var.get())
            sound_name = None

        duration = self.get_pomodoro_phase_duration()
        self.pomodoro_state["remaining_seconds"] = duration
        self.pomodoro_state["running"] = should_continue
        self.pomodoro_state["phase_end_at"] = time.time() + duration if should_continue else None
        self.pomodoro_state["ten_minute_alert_played"] = False
        if sound_name:
            self.play_pomodoro_sound(sound_name)
        else:
            self.play_pomodoro_bell()
        self.save_config()

    def skip_pomodoro_phase(self):
        self.ensure_pomodoro_today()
        was_running = bool(self.pomodoro_state.get("running"))
        self.complete_pomodoro_phase()
        if not was_running:
            self.pomodoro_state["running"] = False
            self.pomodoro_state["phase_end_at"] = None
        self.save_config()
        self.refresh_pomodoro_ui()

    def reset_pomodoro_day(self):
        confirmed = messagebox.askyesno(
            "Reiniciar Pomodoro",
            "Deseas reiniciar los pomodoros, minutos y horas de hoy?",
        )
        if not confirmed:
            return
        self.pomodoro_state = self.get_default_pomodoro_state()
        self.save_config()
        self.refresh_pomodoro_ui()

    def format_pomodoro_time(self, total_seconds):
        total_seconds = max(0, int(total_seconds))
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def format_total_hours(self, total_minutes):
        hours, minutes = divmod(max(0, int(total_minutes)), 60)
        return f"{hours}:{minutes:02d}"

    def refresh_pomodoro_ui(self):
        if not hasattr(self, "pomodoro_timer_label"):
            return
        self.ensure_pomodoro_today()
        remaining = self.get_pomodoro_remaining_seconds()
        completed_count = int(self.pomodoro_state.get("completed_count", 0))
        total_minutes = completed_count * 25
        phase = self.pomodoro_state.get("phase", "work")
        running = bool(self.pomodoro_state.get("running"))
        current_work_number = completed_count + 1

        self.pomodoro_timer_label.config(text=self.format_pomodoro_time(remaining))
        self.pomodoro_minutes_label.config(text=f"MINUTOS: {total_minutes}")
        self.pomodoro_hours_label.config(text=f"HORAS: {self.format_total_hours(total_minutes)}")
        self.pomodoro_completed_label.config(text=f"POMODOROS: {completed_count}")
        self.pomodoro_count_label.config(text=f"#{current_work_number}")
        self.pomodoro_toggle_button.config(text="Pausar" if running else "Reanudar" if remaining < self.get_pomodoro_phase_duration() else "Iniciar")

        for child in self.pomodoro_active_flow_tasks_frame.winfo_children():
            child.destroy()

        active_task = self.get_active_pomodoro_task()
        active_flow = self.get_active_pomodoro_flow()
        if active_task:
            self.pomodoro_active_task_label.config(text=active_task.get("title", ""))
            self.pomodoro_active_task_count_label.config(
                text=f"Pomodoros en esta tarea: {int(active_task.get('completed_pomodoros', 0) or 0)}"
            )
            if hasattr(self, "pomodoro_clear_active_task_button"):
                self.pomodoro_clear_active_task_button.config(state="normal")
        elif active_flow:
            completed, total, percentage = self.get_pomodoro_flow_progress(active_flow)
            self.pomodoro_active_task_label.config(text=f"Flujo: {active_flow['name']}")
            self.pomodoro_active_task_count_label.config(
                text=f"{total} tareas - {completed}/{total} completadas - {percentage}%"
            )
            for task_index, task in enumerate(active_flow.get("tasks", [])):
                completed_var = tk.BooleanVar(value=bool(task.get("completed")))
                ttk.Checkbutton(
                    self.pomodoro_active_flow_tasks_frame,
                    text=task.get("title", ""),
                    variable=completed_var,
                    command=lambda f=active_flow["id"], t=task["id"], v=completed_var: self.set_pomodoro_flow_task_completed(f, t, v.get()),
                ).grid(row=task_index, column=0, sticky="w", pady=2)
            if not active_flow.get("tasks"):
                ttk.Label(
                    self.pomodoro_active_flow_tasks_frame,
                    text="Este flujo aun no tiene tareas.",
                    style="Body.TLabel",
                ).grid(row=0, column=0, sticky="w")
            self.pomodoro_clear_active_task_button.config(state="normal")
        else:
            self.pomodoro_active_task_label.config(text="Sin tarea seleccionada")
            self.pomodoro_active_task_count_label.config(text="Pomodoros en esta tarea: 0")
            if hasattr(self, "pomodoro_clear_active_task_button"):
                self.pomodoro_clear_active_task_button.config(state="disabled")

        if phase == "work":
            self.pomodoro_phase_label.config(text=f"Pomodoro #{current_work_number}")
        else:
            break_name = "Descanso largo" if self.get_pomodoro_phase_duration() == self.pomodoro_long_break_seconds else "Descanso"
            self.pomodoro_phase_label.config(text=break_name)
        self.update_pomodoro_taskbar_icon(remaining, running)

    def update_pomodoro_taskbar_icon(self, remaining_seconds, running=True):
        if not running:
            if self.taskbar_overlay_active or self.pomodoro_icon_last_text is not None:
                self.clear_pomodoro_taskbar_overlay()
                self.pomodoro_icon_last_text = None
            self.root.title(self.base_window_title)
            return

        text = self.format_pomodoro_icon_text(remaining_seconds)
        if text == self.pomodoro_icon_last_text and self.pomodoro_icon_image is not None:
            return

        self.pomodoro_icon_image = self.build_pomodoro_icon_image(text)
        self.write_pomodoro_ico_file(text)
        if self.set_pomodoro_taskbar_overlay(text):
            self.pomodoro_icon_last_text = text
        self.root.title(f"Pomodoro {self.format_pomodoro_time(remaining_seconds)} - {self.base_window_title}")

    def format_pomodoro_icon_text(self, total_seconds):
        total_seconds = max(0, int(total_seconds))
        minutes = min(99, total_seconds // 60)
        return f"{minutes}m"

    def build_pomodoro_icon_image(self, text):
        size = 64
        image = tk.PhotoImage(width=size, height=size)
        pixels = self.build_pomodoro_icon_pixels(text, size)
        for y, row in enumerate(pixels):
            for x, color in enumerate(row):
                image.put(self.rgb_to_hex(color), to=(x, y, x + 1, y + 1))
        return image

    def draw_icon_badge(self, image, text, badge_color, text_color):
        scale = 2
        glyph_width = 3 * scale
        gap = scale
        text_width = len(text) * glyph_width + max(0, len(text) - 1) * gap
        badge_width = max(30, text_width + 10)
        badge_height = 24
        left = 64 - badge_width
        top = 0
        image.put(badge_color, to=(left + 4, top, 64 - 4, top + badge_height))
        image.put(badge_color, to=(left, top + 4, 64, top + badge_height - 4))
        image.put(badge_color, to=(left + 2, top + 2, 64 - 2, top + badge_height - 2))

        x = left + max(4, (badge_width - text_width) // 2)
        y = top + 7
        for char in text:
            self.draw_icon_glyph(image, char, x, y, scale, text_color)
            x += glyph_width + gap

    def write_pomodoro_ico_file(self, text):
        size = 32
        pixels = self.build_pomodoro_overlay_pixels(text, size)
        xor = bytearray()
        for y in range(size - 1, -1, -1):
            for x in range(size):
                red, green, blue, alpha = pixels[y][x]
                xor.extend((blue, green, red, alpha))

        mask_row_bytes = ((size + 31) // 32) * 4
        and_mask = bytes(mask_row_bytes * size)
        image_bytes = bytes(xor) + and_mask

        header = bytearray()
        header.extend((0).to_bytes(2, "little"))
        header.extend((1).to_bytes(2, "little"))
        header.extend((1).to_bytes(2, "little"))
        header.extend(bytes((size, size, 0, 0)))
        header.extend((1).to_bytes(2, "little"))
        header.extend((32).to_bytes(2, "little"))
        header.extend((40 + len(image_bytes)).to_bytes(4, "little"))
        header.extend((22).to_bytes(4, "little"))

        dib = bytearray()
        dib.extend((40).to_bytes(4, "little"))
        dib.extend((size).to_bytes(4, "little", signed=True))
        dib.extend((size * 2).to_bytes(4, "little", signed=True))
        dib.extend((1).to_bytes(2, "little"))
        dib.extend((32).to_bytes(2, "little"))
        dib.extend((0).to_bytes(4, "little"))
        dib.extend((len(image_bytes)).to_bytes(4, "little"))
        dib.extend((0).to_bytes(4, "little", signed=True))
        dib.extend((0).to_bytes(4, "little", signed=True))
        dib.extend((0).to_bytes(4, "little"))
        dib.extend((0).to_bytes(4, "little"))

        try:
            with open(self.pomodoro_icon_path, "wb") as icon_file:
                icon_file.write(header + dib + image_bytes)
        except OSError:
            pass

    def set_pomodoro_taskbar_overlay(self, text):
        if not self.ensure_taskbar_overlay_ready():
            return False

        hicon = self.load_overlay_hicon()
        if not hicon:
            return False

        try:
            import ctypes

            set_overlay = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_wchar_p,
            )(self.taskbar_overlay_vtbl[18])
            hwnd = self.get_taskbar_window_handle()
            result = set_overlay(self.taskbar_overlay_ptr, hwnd, hicon, f"Pomodoro {text}")
            if result != 0:
                ctypes.windll.user32.DestroyIcon(hicon)
                return False

            if self.taskbar_overlay_hicon:
                ctypes.windll.user32.DestroyIcon(self.taskbar_overlay_hicon)
            self.taskbar_overlay_hicon = hicon
            self.taskbar_overlay_active = True
            return True
        except Exception:
            try:
                import ctypes

                ctypes.windll.user32.DestroyIcon(hicon)
            except Exception:
                pass
            return False

    def ensure_taskbar_overlay_ready(self):
        if self.taskbar_overlay_ready:
            return True

        try:
            import ctypes

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", ctypes.c_ulong),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8),
                ]

            clsid_taskbar = GUID()
            iid_taskbar_list3 = GUID()
            ctypes.windll.ole32.CoInitialize(None)
            ctypes.windll.ole32.CLSIDFromString(
                "{56FDF344-FD6D-11d0-958A-006097C9A090}",
                ctypes.byref(clsid_taskbar),
            )
            ctypes.windll.ole32.CLSIDFromString(
                "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEA84}",
                ctypes.byref(iid_taskbar_list3),
            )

            taskbar_ptr = ctypes.c_void_p()
            ctypes.windll.ole32.CoCreateInstance.restype = ctypes.c_long
            result = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(clsid_taskbar),
                None,
                1,
                ctypes.byref(iid_taskbar_list3),
                ctypes.byref(taskbar_ptr),
            )
            if result != 0 or not taskbar_ptr.value:
                return False

            vtbl = ctypes.cast(taskbar_ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            hr_init = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(vtbl[3])
            if hr_init(taskbar_ptr) != 0:
                return False

            self.taskbar_overlay_ptr = taskbar_ptr
            self.taskbar_overlay_vtbl = vtbl
            self.taskbar_overlay_ready = True
            return True
        except Exception:
            return False

    def load_overlay_hicon(self):
        try:
            import ctypes

            image_icon = 1
            load_from_file = 0x00000010
            ctypes.windll.user32.LoadImageW.restype = ctypes.c_void_p
            return ctypes.windll.user32.LoadImageW(
                None,
                self.pomodoro_icon_path,
                image_icon,
                32,
                32,
                load_from_file,
            )
        except Exception:
            return None

    def get_taskbar_window_handle(self):
        try:
            import ctypes

            self.root.update_idletasks()
            hwnd = int(self.root.winfo_id())
            get_ancestor = ctypes.windll.user32.GetAncestor
            get_ancestor.restype = ctypes.c_void_p
            root_hwnd = get_ancestor(ctypes.c_void_p(hwnd), 2)
            return root_hwnd or hwnd
        except Exception:
            return self.root.winfo_id()

    def clear_pomodoro_taskbar_overlay(self):
        if not self.taskbar_overlay_active and self.taskbar_overlay_hicon is None:
            return
        if not self.taskbar_overlay_ready:
            self.taskbar_overlay_active = False
            return
        try:
            import ctypes

            set_overlay = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_wchar_p,
            )(self.taskbar_overlay_vtbl[18])
            set_overlay(self.taskbar_overlay_ptr, self.get_taskbar_window_handle(), None, None)
            if self.taskbar_overlay_hicon:
                ctypes.windll.user32.DestroyIcon(self.taskbar_overlay_hicon)
                self.taskbar_overlay_hicon = None
            self.taskbar_overlay_active = False
        except Exception:
            self.taskbar_overlay_active = False
            pass

    def build_pomodoro_overlay_pixels(self, text, size):
        transparent = (0, 0, 0, 0)
        badge_fill = (*self.hex_to_rgb("#bfe4ff"), 255)
        badge_border = (*self.hex_to_rgb("#5d9bd8"), 255)
        badge_text = (*self.hex_to_rgb("#6f96ad"), 255)
        pixels = [[transparent for _x in range(size)] for _y in range(size)]

        self.draw_rounded_rect(pixels, 0, 4, 32, 26, 11, badge_border)
        self.draw_rounded_rect(pixels, 2, 6, 30, 24, 9, badge_fill)

        scale = 2
        glyph_width = 3 * scale
        gap = scale
        text_width = len(text) * glyph_width + max(0, len(text) - 1) * gap
        x = max(2, (size - text_width) // 2)
        y = 12
        for char in text:
            self.draw_pixel_glyph(pixels, char, x, y, scale, badge_text)
            x += glyph_width + gap
        return pixels

    def build_pomodoro_icon_pixels(self, text, size):
        background = self.hex_to_rgb("#f8fafc")
        shadow = self.hex_to_rgb("#dfe3e8")
        card = self.hex_to_rgb("#ffffff")
        blue = self.hex_to_rgb("#4d96e8")
        badge_fill = self.hex_to_rgb("#bfe4ff")
        badge_border = self.hex_to_rgb("#5d9bd8")
        badge_text = self.hex_to_rgb("#7ea6bf")
        green = self.hex_to_rgb("#58c979")
        gray = self.hex_to_rgb("#9aa9b3")
        white = self.hex_to_rgb("#ffffff")
        pixels = [[background for _x in range(size)] for _y in range(size)]

        self.draw_rounded_rect(pixels, 5, 17, 50, 63, 10, shadow)
        self.draw_rounded_rect(pixels, 4, 14, 49, 60, 10, card)

        self.draw_filled_ellipse(pixels, 11, 29, 25, 43, blue)
        self.draw_filled_ellipse(pixels, 7, 39, 31, 58, blue)
        self.fill_pixel_rect(pixels, 9, 44, 29, 56, blue)

        for top in (28, 39, 50):
            self.draw_thick_line(pixels, 32, top + 5, 36, top + 9, green, 3)
            self.draw_thick_line(pixels, 36, top + 9, 44, top, green, 3)
            self.draw_thick_line(pixels, 47, top + 5, 60, top + 5, gray, 3)

        self.draw_rounded_rect(pixels, 29, 1, 64, 25, 12, badge_border)
        self.draw_rounded_rect(pixels, 31, 3, 62, 23, 10, badge_fill)

        scale = 2
        glyph_width = 3 * scale
        gap = scale
        text_width = len(text) * glyph_width + max(0, len(text) - 1) * gap
        x = 31 + max(3, (31 - text_width) // 2)
        y = 9

        for char in text:
            self.draw_pixel_glyph(pixels, char, x, y, scale, badge_text)
            x += glyph_width + gap
        return pixels

    def hex_to_rgb(self, value):
        value = value.lstrip("#")
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))

    def rgb_to_hex(self, color):
        return "#{:02x}{:02x}{:02x}".format(*color)

    def fill_pixel_rect(self, pixels, left, top, right, bottom, color):
        height = len(pixels)
        width = len(pixels[0]) if height else 0
        for y in range(max(0, top), min(height, bottom)):
            for x in range(max(0, left), min(width, right)):
                pixels[y][x] = color

    def draw_rounded_rect(self, pixels, left, top, right, bottom, radius, color):
        for y in range(top, bottom):
            if y < top + radius:
                offset = radius - int((radius * radius - (top + radius - y) ** 2) ** 0.5)
            elif y >= bottom - radius:
                offset = radius - int((radius * radius - (y - (bottom - radius - 1)) ** 2) ** 0.5)
            else:
                offset = 0
            self.fill_pixel_rect(pixels, left + offset, y, right - offset, y + 1, color)

    def draw_filled_ellipse(self, pixels, left, top, right, bottom, color):
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2
        radius_x = max(1, (right - left) / 2)
        radius_y = max(1, (bottom - top) / 2)
        for y in range(top, bottom):
            for x in range(left, right):
                if ((x + 0.5 - center_x) / radius_x) ** 2 + ((y + 0.5 - center_y) / radius_y) ** 2 <= 1:
                    self.fill_pixel_rect(pixels, x, y, x + 1, y + 1, color)

    def draw_thick_line(self, pixels, x1, y1, x2, y2, color, thickness=1):
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        radius = max(0, thickness // 2)
        for step in range(steps + 1):
            x = round(x1 + (x2 - x1) * step / steps)
            y = round(y1 + (y2 - y1) * step / steps)
            self.fill_pixel_rect(pixels, x - radius, y - radius, x + radius + 1, y + radius + 1, color)

    def draw_pixel_glyph(self, pixels, char, x, y, scale, color):
        glyphs = {
            "0": ("111", "101", "101", "101", "111"),
            "1": ("010", "110", "010", "010", "111"),
            "2": ("111", "001", "111", "100", "111"),
            "3": ("111", "001", "111", "001", "111"),
            "4": ("101", "101", "111", "001", "001"),
            "5": ("111", "100", "111", "001", "111"),
            "6": ("111", "100", "111", "101", "111"),
            "7": ("111", "001", "010", "010", "010"),
            "8": ("111", "101", "111", "101", "111"),
            "9": ("111", "101", "111", "001", "111"),
            "m": ("000", "101", "111", "111", "101"),
        }
        pattern = glyphs.get(char.lower())
        if not pattern:
            return
        for row_index, row in enumerate(pattern):
            for column_index, value in enumerate(row):
                if value == "1":
                    self.fill_pixel_rect(
                        pixels,
                        x + column_index * scale,
                        y + row_index * scale,
                        x + (column_index + 1) * scale,
                        y + (row_index + 1) * scale,
                        color,
                    )

    def draw_icon_colon(self, image, x, y, scale, color):
        dot = max(1, scale)
        image.put(color, to=(x, y + 4 * scale, x + dot, y + 4 * scale + dot))
        image.put(color, to=(x, y + 10 * scale, x + dot, y + 10 * scale + dot))

    def draw_icon_glyph(self, image, char, x, y, scale, color):
        glyphs = {
            "0": ("111", "101", "101", "101", "111"),
            "1": ("010", "110", "010", "010", "111"),
            "2": ("111", "001", "111", "100", "111"),
            "3": ("111", "001", "111", "001", "111"),
            "4": ("101", "101", "111", "001", "001"),
            "5": ("111", "100", "111", "001", "111"),
            "6": ("111", "100", "111", "101", "111"),
            "7": ("111", "001", "010", "010", "010"),
            "8": ("111", "101", "111", "101", "111"),
            "9": ("111", "101", "111", "001", "111"),
            "m": ("000", "101", "111", "111", "101"),
        }
        pattern = glyphs.get(char.lower())
        if not pattern:
            return

        for row_index, row in enumerate(pattern):
            for column_index, value in enumerate(row):
                if value == "1":
                    left = x + column_index * scale
                    top = y + row_index * scale
                    image.put(color, to=(left, top, left + scale, top + scale))

    def get_pomodoro_sound_path(self, sound_name):
        sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonidos")
        for extension in (".wav", ".mp3", ".m4a", ".wma"):
            path = os.path.join(sounds_dir, f"{sound_name}{extension}")
            if os.path.isfile(path):
                return path
        return ""

    def play_pomodoro_sound(self, sound_name):
        sound_path = self.get_pomodoro_sound_path(sound_name)
        if not sound_path:
            self.play_pomodoro_bell()
            return

        extension = os.path.splitext(sound_path)[1].lower()
        try:
            if extension == ".wav" and winsound is not None:
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            if self.play_pomodoro_media_file(sound_path, sound_name):
                return
        except Exception:
            pass
        self.play_pomodoro_bell()

    def play_pomodoro_media_file(self, sound_path, sound_name):
        if os.name != "nt":
            return False
        try:
            import ctypes

            alias = "pomodoro_" + re.sub(r"[^a-zA-Z0-9_]", "_", sound_name)
            mci_send = ctypes.windll.winmm.mciSendStringW
            mci_send.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
            mci_send.restype = ctypes.c_uint

            mci_send(f"close {alias}", None, 0, None)
            open_result = mci_send(f'open "{sound_path}" alias {alias}', None, 0, None)
            if open_result != 0:
                return False
            play_result = mci_send(f"play {alias}", None, 0, None)
            if play_result != 0:
                mci_send(f"close {alias}", None, 0, None)
                return False
            self.pomodoro_sound_aliases[alias] = True
            return True
        except Exception:
            return False

    def close_pomodoro_sounds(self):
        if os.name != "nt":
            return
        try:
            import ctypes

            mci_send = ctypes.windll.winmm.mciSendStringW
            for alias in list(self.pomodoro_sound_aliases):
                mci_send(f"close {alias}", None, 0, None)
            self.pomodoro_sound_aliases.clear()
        except Exception:
            pass

    def play_pomodoro_bell(self):
        try:
            if winsound is not None:
                winsound.Beep(880, 350)
                winsound.Beep(660, 350)
            else:
                self.root.bell()
        except Exception:
            try:
                self.root.bell()
            except tk.TclError:
                pass

    def on_app_close(self):
        if self.pomodoro_after_id is not None:
            try:
                self.root.after_cancel(self.pomodoro_after_id)
            except tk.TclError:
                pass
            self.pomodoro_after_id = None

        if self.pomodoro_state.get("running"):
            self.pomodoro_state["remaining_seconds"] = self.get_pomodoro_remaining_seconds()
            self.pomodoro_state["phase_end_at"] = None
            confirmed = messagebox.askyesno(
                "Pomodoro corriendo",
                "Hay un Pomodoro activo. Si cierras, se guardara el minuto actual para continuar al abrir. Deseas cerrar?",
            )
            if not confirmed:
                self.pomodoro_state["phase_end_at"] = time.time() + self.pomodoro_state["remaining_seconds"]
                self.start_pomodoro_tick()
                return

        self.save_config()
        self.close_pomodoro_sounds()
        self.clear_pomodoro_taskbar_overlay()
        self.root.destroy()

    def _build_header(self, parent):
        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_block,
            text="Renombrador inteligente de PDFs",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Extrae NCF y razon social, renombra el archivo y lo mueve a la carpeta elegida.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.pdf_summary = self._create_info_card(header, 0, 1, "PDF seleccionado", "Ningun archivo")
        self.folder_summary = self._create_info_card(header, 0, 2, "Destino activo", "Sin carpeta")

    def _create_info_card(self, parent, row, column, title, value):
        card = ttk.Frame(parent, style="AltCard.TFrame", padding=16)
        card.grid(row=row, column=column, sticky="nsew", padx=(14, 0))
        card.grid_columnconfigure(0, weight=1)

        ttk.Label(card, text=title, style="Body.TLabel").grid(row=0, column=0, sticky="w")
        value_label = ttk.Label(card, text=value, style="CardValue.TLabel", wraplength=220, justify="left")
        value_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
        return value_label

    def _build_company_routes(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(panel, style="Card.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Mapeo de rutas por empresa", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Configura empresas emisoras y sus carpetas de destino. El procesador detecta el nombre en la factura.",
            style="Body.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 14))

        form = ttk.Frame(panel, style="AltCard.TFrame", padding=14)
        form.grid(row=2, column=0, sticky="ew", padx=(0, 10))
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        ttk.Label(form, text="Empresa", style="CardValue.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(form, textvariable=self.company_name_var, font=("Segoe UI", 10)).grid(
            row=0, column=1, sticky="ew", padx=(0, 12)
        )
        ttk.Label(form, text="Ruta", style="CardValue.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 8))
        ttk.Entry(form, textvariable=self.company_route_var, font=("Segoe UI", 10)).grid(
            row=0, column=3, sticky="ew", padx=(0, 8)
        )
        ttk.Button(
            form,
            text="Buscar",
            style="Secondary.TButton",
            command=self.choose_company_route_for_form,
        ).grid(row=0, column=4, padx=(0, 8))
        ttk.Button(
            form,
            text="Guardar",
            style="Primary.TButton",
            command=self.save_company_route_from_form,
        ).grid(row=0, column=5)

        list_box = ttk.Frame(panel, style="AltCard.TFrame", padding=12)
        list_box.grid(row=2, column=1, sticky="nsew", padx=(10, 0))
        list_box.grid_rowconfigure(0, weight=1)
        list_box.grid_columnconfigure(0, weight=1)

        self.company_routes_tree = ttk.Treeview(
            list_box,
            columns=("company", "folder"),
            show="headings",
            height=5,
        )
        self.company_routes_tree.heading("company", text="Empresa")
        self.company_routes_tree.heading("folder", text="Ruta de destino")
        self.company_routes_tree.column("company", width=210, anchor="w")
        self.company_routes_tree.column("folder", width=395, anchor="w")
        self.company_routes_tree.grid(row=0, column=0, sticky="nsew")
        self.company_routes_tree.bind("<<TreeviewSelect>>", self.load_selected_company_route_into_form)

        scrollbar = ttk.Scrollbar(list_box, orient="vertical", command=self.company_routes_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.company_routes_tree.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)
        ttk.Button(
            actions,
            text="Nueva empresa",
            style="Secondary.TButton",
            command=self.clear_company_route_form,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            actions,
            text="Cambiar ruta seleccionada",
            style="Secondary.TButton",
            command=self.choose_company_route_for_selected,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(
            actions,
            text="Borrar seleccionada",
            style="Danger.TButton",
            command=self.delete_company_route,
        ).grid(row=0, column=2, sticky="ew")

        self.refresh_company_routes_ui()

    def _build_destinations(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        panel.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        panel.grid_columnconfigure(0, weight=1)

        ttk.Label(panel, text="Procesador de Archivos", style="Section.TLabel").grid(row=0, column=0)
        ttk.Label(
            panel,
            text="Seleccione los documentos PDF originales para iniciar el proceso de renombrado inteligente basado en el mapeo configurado arriba.",
            style="Body.TLabel",
            wraplength=520,
            justify="center",
        ).grid(row=1, column=0, pady=(8, 20))

        # El procesador usa el mapeo empresa-ruta configurado arriba.

        selector_row = ttk.Frame(panel, style="Card.TFrame")
        selector_row.grid(row=3, column=0, sticky="ew", pady=(6, 12))
        selector_row.grid_remove()
        selector_row.grid_columnconfigure(0, weight=1)

        self.folder_var = tk.StringVar(value=self.output_folder)
        self.folder_selector = ttk.Combobox(
            selector_row,
            textvariable=self.folder_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.folder_selector.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.folder_selector.bind("<<ComboboxSelected>>", self.on_folder_selected)

        ttk.Button(
            selector_row,
            text="＋ Agregar",
            style="Secondary.TButton",
            command=self.add_output_folder,
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            selector_row,
            text="✎ Cambiar",
            style="Secondary.TButton",
            command=self.edit_output_folder,
        ).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(
            selector_row,
            text="🗑 Borrar",
            style="Danger.TButton",
            command=self.delete_output_folder,
        ).grid(row=0, column=3)

        self.output_label = ttk.Label(panel, text="", style="Body.TLabel", wraplength=470, justify="left")
        self.output_label.grid(row=4, column=0, sticky="w", pady=(0, 18))
        self.output_label.grid_remove()

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=2, column=0)

        ttk.Button(
            actions,
            text="Seleccionar PDF",
            style="Secondary.TButton",
            command=self.select_pdf,
        ).grid(row=0, column=0, ipadx=22, ipady=4, padx=(0, 12))
        ttk.Button(
            actions,
            text="Procesar",
            style="Primary.TButton",
            command=self.process_pdf,
        ).grid(row=0, column=1, ipadx=28, ipady=4)

        self.refresh_folder_selector()

    def _build_activity(self, parent):
        status_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        status_panel.grid(row=3, column=0, columnspan=2, sticky="ew")
        status_panel.grid_rowconfigure(1, weight=1)
        status_panel.grid_columnconfigure(0, weight=1)
        status_panel.grid_columnconfigure(1, weight=1)

        ttk.Label(status_panel, text="Estado", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status_panel, text="Actividad", style="Section.TLabel").grid(row=0, column=1, sticky="w")

        status_box = ttk.Frame(status_panel, style="AltCard.TFrame", padding=16)
        status_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))
        status_box.grid_columnconfigure(0, weight=1)

        self.current_file_label = ttk.Label(
            status_box,
            text="Archivo actual: -",
            style="CardValue.TLabel",
            wraplength=420,
            justify="left",
        )
        self.current_file_label.grid(row=0, column=0, sticky="w")

        self.counter_label = ttk.Label(
            status_box,
            text="Procesados: 0 / 1",
            style="CardValue.TLabel",
        )
        self.counter_label.grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.progress_canvas = tk.Canvas(
            status_box,
            width=420,
            height=12,
            bg=self.colors["card_alt"],
            highlightthickness=0,
        )
        self.progress_canvas.grid(row=2, column=0, sticky="ew", pady=(14, 0))

        log_box = ttk.Frame(status_panel, style="AltCard.TFrame", padding=16)
        log_box.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
        log_box.grid_rowconfigure(0, weight=1)
        log_box.grid_columnconfigure(0, weight=1)

        self.log_text = ScrolledText(
            log_box,
            wrap=tk.WORD,
            height=14,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state="disabled")

        self.update_progress(0, 1)

    def _build_copy_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_block,
            text="Copiar propuesta PDF",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Selecciona un PDF base, escribe el nombre variable y crea una copia renombrada en la misma carpeta.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.copy_source_summary = self._create_info_card(header, 0, 1, "PDF base guardado", "Sin archivo")

        form_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        form_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        form_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(form_panel, text="Archivo base", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_panel,
            text="La ruta queda guardada para reutilizarla. Puedes cambiarla o borrarla cuando quieras.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        self.copy_source_label = ttk.Label(
            form_panel,
            text="PDF actual: (no seleccionado)",
            style="Body.TLabel",
            wraplength=470,
            justify="left",
        )
        self.copy_source_label.grid(row=2, column=0, sticky="w", pady=(0, 12))

        source_actions = ttk.Frame(form_panel, style="Card.TFrame")
        source_actions.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        source_actions.grid_columnconfigure(0, weight=1)
        source_actions.grid_columnconfigure(1, weight=1)
        source_actions.grid_columnconfigure(2, weight=1)

        ttk.Button(
            source_actions,
            text="Seleccionar PDF base",
            style="Secondary.TButton",
            command=self.select_copy_source_pdf,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            source_actions,
            text="Cambiar PDF base",
            style="Secondary.TButton",
            command=self.change_copy_source_pdf,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(
            source_actions,
            text="Borrar ruta guardada",
            style="Danger.TButton",
            command=self.clear_copy_source_pdf,
        ).grid(row=0, column=2, sticky="ew")

        ttk.Label(form_panel, text="Nombre variable", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        self.copy_name_entry = ttk.Entry(form_panel, textvariable=self.copy_name_var, font=("Segoe UI", 11))
        self.copy_name_entry.grid(row=5, column=0, sticky="ew", pady=(6, 10))

        ttk.Label(form_panel, text="Tipo de propuesta", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        self.copy_proposal_type_selector = ttk.Combobox(
            form_panel,
            textvariable=self.copy_proposal_type_var,
            values=("mensual", "renta"),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.copy_proposal_type_selector.grid(row=7, column=0, sticky="ew", pady=(6, 10))

        ttk.Label(
            form_panel,
            text='Resultado: "PROPUESTA DE ASESORIA PARA NOMBRE.pdf"',
            style="Body.TLabel",
        ).grid(row=8, column=0, sticky="w")

        ttk.Button(
            form_panel,
            text="Crear copia renombrada",
            style="Primary.TButton",
            command=self.create_proposal_copy,
        ).grid(row=9, column=0, sticky="ew", pady=(18, 0))

        preview_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        preview_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        preview_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(preview_panel, text="Vista previa", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            preview_panel,
            text="La copia se genera en la misma carpeta del PDF base y luego se abre esa carpeta.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.copy_preview_label = ttk.Label(
            preview_panel,
            text="Archivo nuevo: PROPUESTA DE ASESORIA PARA NOMBRE.pdf",
            style="CardValue.TLabel",
            wraplength=420,
            justify="left",
        )
        self.copy_preview_label.grid(row=2, column=0, sticky="w")

        self.copy_folder_label = ttk.Label(
            preview_panel,
            text="Carpeta: (sin carpeta)",
            style="Body.TLabel",
            wraplength=420,
            justify="left",
        )
        self.copy_folder_label.grid(row=3, column=0, sticky="w", pady=(12, 18))

        copy_log_box = ttk.Frame(preview_panel, style="AltCard.TFrame", padding=16)
        copy_log_box.grid(row=4, column=0, sticky="nsew")
        copy_log_box.grid_rowconfigure(0, weight=1)
        copy_log_box.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(4, weight=1)

        self.copy_log_text = ScrolledText(
            copy_log_box,
            wrap=tk.WORD,
            height=12,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.copy_log_text.grid(row=0, column=0, sticky="nsew")
        self.copy_log_text.configure(state="disabled")

        self.copy_name_var.trace_add("write", self._on_copy_name_change)
        self.copy_proposal_type_var.trace_add("write", self._on_copy_name_change)
        self.update_copy_summary()


    def _build_fiscal_template_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=1)
        header.grid_columnconfigure(4, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_block,
            text="Plantilla fiscal",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Lleva el control de versiones, compradores y mensajes en sub-pestañas separadas dentro de este modulo.",
            style="Body.TLabel",
            wraplength=540,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.fiscal_versions_summary = self._create_info_card(header, 0, 1, "Versiones", "0")
        self.fiscal_buyers_summary = self._create_info_card(header, 0, 2, "Compradores", "0")
        self.fiscal_net_profit_summary = self._create_info_card(header, 0, 3, "Ganancia neta", "RD$0.00")
        self.fiscal_gross_profit_summary = self._create_info_card(header, 0, 4, "Ganancia bruta", "RD$0.00")

        sub_notebook = ttk.Notebook(parent)
        sub_notebook.grid(row=1, column=0, sticky="nsew")

        versions_tab = ttk.Frame(sub_notebook, style="App.TFrame", padding=0)
        versions_tab.grid_rowconfigure(0, weight=1)
        versions_tab.grid_columnconfigure(0, weight=2)
        versions_tab.grid_columnconfigure(1, weight=3)
        sub_notebook.add(versions_tab, text="Versiones")

        buyers_tab = ttk.Frame(sub_notebook, style="App.TFrame", padding=0)
        buyers_tab.grid_rowconfigure(0, weight=1)
        buyers_tab.grid_columnconfigure(0, weight=2)
        buyers_tab.grid_columnconfigure(1, weight=3)
        sub_notebook.add(buyers_tab, text="Compradores")

        messages_tab = ttk.Frame(sub_notebook, style="App.TFrame", padding=0)
        messages_tab.grid_rowconfigure(1, weight=1)
        messages_tab.grid_columnconfigure(0, weight=1)
        messages_tab.grid_columnconfigure(1, weight=1)
        sub_notebook.add(messages_tab, text="Mensajes")

        self._build_fiscal_versions_subtab(versions_tab)
        self._build_fiscal_buyers_subtab(buyers_tab)
        self._build_messages_tab(messages_tab)
        self.refresh_fiscal_template_summary()

    def _build_fiscal_versions_subtab(self, parent):
        form_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(form_panel, text="Nueva version", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_panel,
            text="Llena el formulario y al guardar la version se agregara a la lista historica.",
            style="Body.TLabel",
            wraplength=420,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(form_panel, text="Version", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_version_var, font=("Segoe UI", 11)).grid(
            row=3, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Fecha", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_version_date_var, font=("Segoe UI", 11)).grid(
            row=5, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Tipo de cambio", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        ttk.Combobox(
            form_panel,
            textvariable=self.fiscal_version_change_type_var,
            values=("Lanzamiento", "Correccion", "Mejora", "Actualizacion", "Hotfix"),
            state="readonly",
            style="Modern.TCombobox",
        ).grid(row=7, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(form_panel, text="Descripcion", style="Body.TLabel").grid(row=8, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_version_description_var, font=("Segoe UI", 11)).grid(
            row=9, column=0, sticky="ew", pady=(6, 12)
        )

        options_row = ttk.Frame(form_panel, style="Card.TFrame")
        options_row.grid(row=10, column=0, sticky="ew", pady=(0, 12))
        options_row.grid_columnconfigure(0, weight=1)
        options_row.grid_columnconfigure(1, weight=1)

        ttk.Label(options_row, text="Afecta macros", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(options_row, text="Requiere actualizacion manual", style="Body.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )
        ttk.Combobox(
            options_row,
            textvariable=self.fiscal_version_affects_macros_var,
            values=("Si", "No"),
            state="readonly",
            style="Modern.TCombobox",
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0), padx=(0, 6))
        ttk.Combobox(
            options_row,
            textvariable=self.fiscal_version_requires_manual_var,
            values=("Si", "No"),
            state="readonly",
            style="Modern.TCombobox",
        ).grid(row=1, column=1, sticky="ew", pady=(6, 0), padx=(6, 0))

        buttons = ttk.Frame(form_panel, style="Card.TFrame")
        buttons.grid(row=11, column=0, sticky="ew", pady=(18, 0))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        ttk.Button(
            buttons,
            text="Limpiar",
            style="Secondary.TButton",
            command=self.reset_fiscal_version_form,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            buttons,
            text="Guardar version",
            style="Primary.TButton",
            command=self.save_fiscal_version,
        ).grid(row=0, column=1, sticky="ew")

        list_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        list_panel.grid_rowconfigure(1, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(list_panel, text="Historial de versiones", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        tree_container = ttk.Frame(list_panel, style="Card.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.fiscal_versions_tree = ttk.Treeview(
            tree_container,
            columns=("version", "fecha", "tipo", "descripcion", "macros", "manual"),
            show="headings",
            height=16,
        )
        self.fiscal_versions_tree.grid(row=0, column=0, sticky="nsew")
        self.fiscal_versions_tree.heading("version", text="Version")
        self.fiscal_versions_tree.heading("fecha", text="Fecha")
        self.fiscal_versions_tree.heading("tipo", text="Tipo de cambio")
        self.fiscal_versions_tree.heading("descripcion", text="Descripcion")
        self.fiscal_versions_tree.heading("macros", text="Afecta macros")
        self.fiscal_versions_tree.heading("manual", text="Actualizacion manual")
        self.fiscal_versions_tree.column("version", width=110, anchor="center")
        self.fiscal_versions_tree.column("fecha", width=110, anchor="center")
        self.fiscal_versions_tree.column("tipo", width=130, anchor="center")
        self.fiscal_versions_tree.column("descripcion", width=320, anchor="w")
        self.fiscal_versions_tree.column("macros", width=110, anchor="center")
        self.fiscal_versions_tree.column("manual", width=150, anchor="center")

        versions_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.fiscal_versions_tree.yview)
        versions_scroll.grid(row=0, column=1, sticky="ns")
        self.fiscal_versions_tree.configure(yscrollcommand=versions_scroll.set)
        self.fiscal_versions_tree.bind("<Double-Button-1>", self.copy_fiscal_version_description)

        self.fiscal_version_copy_button = ttk.Button(
            list_panel,
            text="Copiar descripcion",
            style="Secondary.TButton",
            command=self.copy_fiscal_version_description,
        )
        self.fiscal_version_copy_button.grid(row=2, column=0, sticky="e", pady=(12, 0))
        self.fiscal_version_copy_button_default_text = "Copiar descripcion"

        self.refresh_fiscal_versions_tree()

    def _build_fiscal_buyers_subtab(self, parent):
        form_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(form_panel, text="Nuevo comprador", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_panel,
            text="Agrega el comprador en el formulario y se guardara para verse luego en la lista.",
            style="Body.TLabel",
            wraplength=420,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(form_panel, text="Nombre", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_buyer_name_var, font=("Segoe UI", 11)).grid(
            row=3, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Fecha de compra", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_buyer_purchase_date_var, font=("Segoe UI", 11)).grid(
            row=5, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Vencimiento", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_buyer_expiration_date_var, font=("Segoe UI", 11)).grid(
            row=7, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Correo electronico", style="Body.TLabel").grid(row=8, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_buyer_email_var, font=("Segoe UI", 11)).grid(
            row=9, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Precio de venta", style="Body.TLabel").grid(row=10, column=0, sticky="w")
        ttk.Entry(form_panel, textvariable=self.fiscal_buyer_price_var, font=("Segoe UI", 11)).grid(
            row=11, column=0, sticky="ew", pady=(6, 12)
        )

        ttk.Label(form_panel, text="Canal", style="Body.TLabel").grid(row=12, column=0, sticky="w")
        ttk.Combobox(
            form_panel,
            textvariable=self.fiscal_buyer_channel_var,
            values=("instagram", "youtube", "pagina web", "desconocido"),
            state="readonly",
            style="Modern.TCombobox",
        ).grid(row=13, column=0, sticky="ew", pady=(6, 12))

        buttons = ttk.Frame(form_panel, style="Card.TFrame")
        buttons.grid(row=14, column=0, sticky="ew", pady=(18, 0))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        ttk.Button(
            buttons,
            text="Nuevo",
            style="Secondary.TButton",
            command=self.reset_fiscal_buyer_form,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.fiscal_buyer_save_button = ttk.Button(
            buttons,
            text="Guardar comprador",
            style="Primary.TButton",
            command=self.save_fiscal_buyer,
        )
        self.fiscal_buyer_save_button.grid(row=0, column=1, sticky="ew")

        list_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        list_panel.grid_rowconfigure(1, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(list_panel, text="Compradores registrados", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        tree_container = ttk.Frame(list_panel, style="Card.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.fiscal_buyers_tree = ttk.Treeview(
            tree_container,
            columns=("nombre", "compra", "vence", "correo", "precio", "canal"),
            show="headings",
            height=16,
        )
        self.fiscal_buyers_tree.grid(row=0, column=0, sticky="nsew")
        self.fiscal_buyers_tree.heading("nombre", text="Nombre")
        self.fiscal_buyers_tree.heading("compra", text="Fecha de compra")
        self.fiscal_buyers_tree.heading("vence", text="Vencimiento")
        self.fiscal_buyers_tree.heading("correo", text="Correo electronico")
        self.fiscal_buyers_tree.heading("precio", text="Precio")
        self.fiscal_buyers_tree.heading("canal", text="Canal")
        self.fiscal_buyers_tree.column("nombre", width=180, anchor="w")
        self.fiscal_buyers_tree.column("compra", width=120, anchor="center")
        self.fiscal_buyers_tree.column("vence", width=120, anchor="center")
        self.fiscal_buyers_tree.column("correo", width=220, anchor="w")
        self.fiscal_buyers_tree.column("precio", width=100, anchor="e")
        self.fiscal_buyers_tree.column("canal", width=110, anchor="center")

        buyers_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.fiscal_buyers_tree.yview)
        buyers_scroll.grid(row=0, column=1, sticky="ns")
        self.fiscal_buyers_tree.configure(yscrollcommand=buyers_scroll.set)
        self.fiscal_buyers_tree.bind("<<TreeviewSelect>>", self.load_selected_fiscal_buyer_into_form)

        buyer_actions = ttk.Frame(list_panel, style="Card.TFrame")
        buyer_actions.grid(row=2, column=0, sticky="e", pady=(12, 0))
        buyer_actions.grid_columnconfigure(0, weight=1)
        buyer_actions.grid_columnconfigure(1, weight=1)

        self.fiscal_buyer_copy_name_button = ttk.Button(
            buyer_actions,
            text="Copiar nombre",
            style="Secondary.TButton",
            command=self.copy_fiscal_buyer_name,
        )
        self.fiscal_buyer_copy_name_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.fiscal_buyer_copy_name_button_default_text = "Copiar nombre"

        self.fiscal_buyer_copy_email_button = ttk.Button(
            buyer_actions,
            text="Copiar correo",
            style="Secondary.TButton",
            command=self.copy_fiscal_buyer_email,
        )
        self.fiscal_buyer_copy_email_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.fiscal_buyer_copy_email_button_default_text = "Copiar correo"

        self.refresh_fiscal_buyers_tree()

    def _build_messages_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_block,
            text="Mensajes automáticos",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Escribe el nombre del cliente, elige el tipo de mensaje y copia el texto completo listo para enviar.",
            style="Body.TLabel",
            wraplength=540,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.message_type_summary = self._create_info_card(header, 0, 1, "Mensaje activo", "Plantilla fiscal")
        self.message_client_summary = self._create_info_card(header, 0, 2, "Cliente", "Sin nombre")

        form_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        form_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        form_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(form_panel, text="Tipo de mensaje", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_panel,
            text="Por ahora está disponible la plantilla fiscal. Luego puedes seguir agregando más opciones aquí.",
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.message_type_selector = ttk.Combobox(
            form_panel,
            textvariable=self.message_type_var,
            values=("Plantilla fiscal",),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.message_type_selector.grid(row=2, column=0, sticky="ew", pady=(0, 18))

        ttk.Label(form_panel, text="Comprador guardado", style="Body.TLabel").grid(row=3, column=0, sticky="w")
        self.message_fiscal_buyer_selector = ttk.Combobox(
            form_panel,
            textvariable=self.message_fiscal_buyer_var,
            values=(),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.message_fiscal_buyer_selector.grid(row=4, column=0, sticky="ew", pady=(6, 10))

        ttk.Label(
            form_panel,
            text="Selecciona un comprador de la plantilla fiscal o escribe el nombre manualmente.",
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=5, column=0, sticky="w", pady=(0, 18))

        ttk.Label(form_panel, text="Nombre del cliente", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        self.message_client_name_entry = ttk.Entry(
            form_panel,
            textvariable=self.message_client_name_var,
            font=("Segoe UI", 11),
        )
        self.message_client_name_entry.grid(row=7, column=0, sticky="ew", pady=(6, 10))

        ttk.Label(
            form_panel,
            text='El nombre se coloca automáticamente en el saludo inicial.',
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=8, column=0, sticky="w", pady=(0, 18))

        self.copy_message_button = ttk.Button(
            form_panel,
            text="Copiar mensaje",
            style="Primary.TButton",
            command=self.copy_generated_message,
        )
        self.copy_message_button.grid(row=9, column=0, sticky="ew")
        self.copy_message_button_default_text = "Copiar mensaje"

        preview_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        preview_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(2, weight=1)

        ttk.Label(preview_panel, text="Vista previa", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            preview_panel,
            text="Puedes revisar el texto antes de copiarlo. Se actualiza al instante cuando cambias el nombre.",
            style="Body.TLabel",
            wraplength=430,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        preview_box = ttk.Frame(preview_panel, style="AltCard.TFrame", padding=16)
        preview_box.grid(row=2, column=0, sticky="nsew")
        preview_box.grid_rowconfigure(0, weight=1)
        preview_box.grid_columnconfigure(0, weight=1)

        self.message_preview_text = ScrolledText(
            preview_box,
            wrap=tk.WORD,
            height=14,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.message_preview_text.grid(row=0, column=0, sticky="nsew")
        self.message_preview_text.configure(state="disabled")

        self.message_client_name_var.trace_add("write", self._on_message_input_change)
        self.message_type_var.trace_add("write", self._on_message_input_change)
        self.message_fiscal_buyer_var.trace_add("write", self._on_message_fiscal_buyer_change)
        self.refresh_message_fiscal_buyer_selector()
        self.update_message_preview()


    def _build_clients_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_block,
            text="Manejador de clientes",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Busca, revisa y administra los datos basicos de cada cliente desde una vista tipo mensajeria.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.clients_total_summary = self._create_info_card(header, 0, 1, "Clientes guardados", "0")

        list_panel = tk.Frame(parent, bg=self.colors["clients_bg"], bd=0, highlightthickness=0)
        list_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        list_panel.grid_rowconfigure(2, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            list_panel,
            text="Clientes",
            bg=self.colors["clients_bg"],
            fg=self.colors["clients_text"],
            font=("Segoe UI Semibold", 16),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))

        search_shell = tk.Frame(
            list_panel,
            bg=self.colors["clients_search"],
            highlightthickness=0,
            bd=0,
            padx=14,
            pady=8,
        )
        search_shell.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        search_shell.grid_columnconfigure(1, weight=1)

        tk.Label(
            search_shell,
            text="⌕",
            bg=self.colors["clients_search"],
            fg=self.colors["clients_muted"],
            font=("Segoe UI Symbol", 16),
        ).grid(row=0, column=0, padx=(0, 8))

        self.client_search_entry = tk.Entry(
            search_shell,
            textvariable=self.client_search_var,
            bg=self.colors["clients_search"],
            fg=self.colors["clients_text"],
            insertbackground=self.colors["clients_text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 11),
        )
        self.client_search_entry.grid(row=0, column=1, sticky="ew")

        list_container = tk.Frame(list_panel, bg=self.colors["clients_bg"], bd=0, highlightthickness=0)
        list_container.grid(row=2, column=0, sticky="nsew", padx=(0, 4), pady=(0, 8))
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        self.client_list_canvas = tk.Canvas(
            list_container,
            bg=self.colors["clients_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.client_list_canvas.grid(row=0, column=0, sticky="nsew")

        client_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.client_list_canvas.yview)
        client_scrollbar.grid(row=0, column=1, sticky="ns")
        self.client_list_canvas.configure(yscrollcommand=client_scrollbar.set)

        self.client_list_inner = tk.Frame(self.client_list_canvas, bg=self.colors["clients_bg"], bd=0, highlightthickness=0)
        self.client_list_window = self.client_list_canvas.create_window((0, 0), window=self.client_list_inner, anchor="nw")
        self.client_list_inner.bind("<Configure>", self._update_client_list_scrollregion)
        self.client_list_canvas.bind("<Configure>", self._resize_client_list_inner)

        detail_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        detail_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        detail_panel.grid_columnconfigure(0, weight=1)
        detail_panel.grid_rowconfigure(2, weight=1)

        detail_header = ttk.Frame(detail_panel, style="Card.TFrame")
        detail_header.grid(row=0, column=0, sticky="ew")
        detail_header.grid_columnconfigure(0, weight=1)
        ttk.Label(detail_header, text="Ficha del cliente", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.client_close_button = ttk.Button(
            detail_header,
            text="X",
            style="Secondary.TButton",
            width=3,
            command=lambda: self.prepare_new_client(show_form=False),
        )
        self.client_close_button.grid(row=0, column=1, sticky="e")
        ttk.Label(
            detail_panel,
            text="Selecciona un cliente existente o crea uno nuevo. Los cambios se guardan en tu configuracion local.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        self.client_empty_state = ttk.Frame(detail_panel, style="Card.TFrame")
        self.client_empty_state.grid(row=2, column=0, sticky="nsew")
        self.client_empty_state.grid_columnconfigure(0, weight=1)
        ttk.Label(
            self.client_empty_state,
            text="No hay ningun cliente seleccionado.",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.client_empty_state,
            text="Presiona el boton para abrir una ficha vacia y registrar un cliente nuevo.",
            style="Body.TLabel",
            wraplength=420,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 16))
        ttk.Button(
            self.client_empty_state,
            text="Anadir cliente",
            style="Primary.TButton",
            command=lambda: self.prepare_new_client(show_form=True),
        ).grid(row=2, column=0, sticky="w")

        self.client_detail_content = ttk.Frame(detail_panel, style="Card.TFrame")
        self.client_detail_content.grid(row=2, column=0, sticky="nsew")
        self.client_detail_content.grid_columnconfigure(0, weight=1)
        self.client_detail_content.grid_rowconfigure(2, weight=1)

        form = ttk.Frame(self.client_detail_content, style="Card.TFrame")
        form.grid(row=0, column=0, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)

        ttk.Label(form, text="Nombre", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.client_name_entry = ttk.Entry(form, textvariable=self.client_name_var, font=("Segoe UI", 11))
        self.client_name_entry.grid(row=1, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(form, text="RNC", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        rnc_row = ttk.Frame(form, style="Card.TFrame")
        rnc_row.grid(row=3, column=0, sticky="ew", pady=(6, 12))
        rnc_row.grid_columnconfigure(0, weight=1)
        self.client_rnc_entry = ttk.Entry(rnc_row, textvariable=self.client_rnc_var, font=("Segoe UI", 11))
        self.client_rnc_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.client_rnc_copy_button = ttk.Button(
            rnc_row,
            text="Copiar",
            style="Secondary.TButton",
            command=self.copy_client_rnc,
        )
        self.client_rnc_copy_button.grid(row=0, column=1)

        ttk.Label(form, text="Ubicacion en PC", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        location_row = ttk.Frame(form, style="Card.TFrame")
        location_row.grid(row=5, column=0, sticky="ew", pady=(6, 12))
        location_row.grid_columnconfigure(0, weight=1)
        self.client_location_entry = ttk.Entry(location_row, textvariable=self.client_pc_location_var, font=("Segoe UI", 11))
        self.client_location_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            location_row,
            text="Elegir carpeta",
            style="Secondary.TButton",
            command=self.select_client_location,
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            location_row,
            text="Abrir carpeta",
            style="Secondary.TButton",
            command=self.open_client_location,
        ).grid(row=0, column=2)

        resources_row = ttk.Frame(form, style="Card.TFrame")
        resources_row.grid(row=6, column=0, sticky="ew", pady=(0, 12))
        resources_row.grid_columnconfigure(1, weight=1)
        ttk.Button(
            resources_row,
            text="Recursos",
            style="Secondary.TButton",
            command=self.open_client_resource,
        ).grid(row=0, column=0, padx=(0, 10))
        self.client_resource_label = ttk.Label(
            resources_row,
            text="Sin recurso guardado",
            style="Body.TLabel",
            wraplength=320,
            justify="left",
        )
        self.client_resource_label.grid(row=0, column=1, sticky="w")

        self.client_extra_toggle = ttk.Button(
            form,
            text="|\n▾ Datos TSS",
            style="Secondary.TButton",
            command=self.toggle_client_extra_section,
        )
        self.client_extra_toggle.grid(row=7, column=0, sticky="w", pady=(0, 10))

        self.client_extra_frame = ttk.Frame(form, style="AltCard.TFrame", padding=14)
        self.client_extra_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(self.client_extra_frame, text="Cedula", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.client_cedula_entry = ttk.Entry(
            self.client_extra_frame,
            textvariable=self.client_cedula_var,
            font=("Segoe UI", 11),
        )
        self.client_cedula_entry.grid(row=1, column=0, sticky="ew", pady=(6, 12), padx=(0, 8))
        self.client_cedula_copy_button = ttk.Button(
            self.client_extra_frame,
            text="Copiar",
            style="Secondary.TButton",
            command=self.copy_client_cedula,
        )
        self.client_cedula_copy_button.grid(row=1, column=1, sticky="e", pady=(6, 12))

        ttk.Label(self.client_extra_frame, text="Class para TSS", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        self.client_tss_class_entry = ttk.Entry(
            self.client_extra_frame,
            textvariable=self.client_tss_class_var,
            font=("Segoe UI", 11),
        )
        self.client_tss_class_entry.grid(row=3, column=0, sticky="ew", pady=(6, 0), padx=(0, 8))
        self.client_tss_class_copy_button = ttk.Button(
            self.client_extra_frame,
            text="Copiar",
            style="Secondary.TButton",
            command=self.copy_client_tss_class,
        )
        self.client_tss_class_copy_button.grid(row=3, column=1, sticky="e", pady=(6, 0))

        ttk.Label(form, text="Descripcion del trabajo", style="Body.TLabel").grid(row=9, column=0, sticky="w")
        self.client_description_text = ScrolledText(
            form,
            wrap=tk.WORD,
            height=10,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
        )
        self.client_description_text.grid(row=10, column=0, sticky="nsew", pady=(6, 14))
        form.grid_rowconfigure(10, weight=1)

        button_row = ttk.Frame(self.client_detail_content, style="Card.TFrame")
        button_row.grid(row=1, column=0, sticky="ew")
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)
        button_row.grid_columnconfigure(2, weight=1)

        ttk.Button(
            button_row,
            text="Nuevo cliente",
            style="Secondary.TButton",
            command=lambda: self.prepare_new_client(show_form=True),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            button_row,
            text="Guardar cliente",
            style="Primary.TButton",
            command=self.save_client,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(
            button_row,
            text="Eliminar cliente",
            style="Danger.TButton",
            command=self.delete_client,
        ).grid(row=0, column=2, sticky="ew")

        self.client_detail_hint = ttk.Label(
            self.client_detail_content,
            text="Completa el formulario y guarda. Si no hay cliente seleccionado, se crea uno nuevo.",
            style="Body.TLabel",
            wraplength=420,
            justify="left",
        )
        self.client_detail_hint.grid(row=2, column=0, sticky="w", pady=(14, 0))

        self.client_search_var.trace_add("write", self._on_client_search_change)
        self.client_form_visible = False
        self.prepare_new_client(select_first=False, show_form=False)
        self.refresh_clients_ui()








    def _truncate_middle(self, text, limit=46):
        if not text:
            return ""
        if len(text) <= limit:
            return text
        half = (limit - 3) // 2
        return f"{text[:half]}...{text[-half:]}"

    def update_summary(self):
        if len(self.pdf_paths) > 1:
            pdf_name = f"{len(self.pdf_paths)} PDFs seleccionados"
        elif self.pdf_paths:
            pdf_name = os.path.basename(self.pdf_paths[0])
        else:
            pdf_name = os.path.basename(self.pdf_path) if self.pdf_path else "Ningun archivo"
        active_routes = sum(1 for item in self.company_route_mappings if item.get("active", True))
        folder_name = f"{active_routes} empresa(s)" if active_routes else "Sin mapeos"
        if hasattr(self, "pdf_summary"):
            self.pdf_summary.config(text=self._truncate_middle(pdf_name, 32))
        if hasattr(self, "folder_summary"):
            self.folder_summary.config(text=self._truncate_middle(folder_name, 36))
        self.update_home_dashboard()

    def update_home_dashboard(self):
        if hasattr(self, "home_pdf_summary"):
            if len(self.pdf_paths) > 1:
                pdf_name = f"{len(self.pdf_paths)} PDFs"
            elif self.pdf_paths:
                pdf_name = os.path.basename(self.pdf_paths[0])
            else:
                pdf_name = os.path.basename(self.pdf_path) if self.pdf_path else "Ningun archivo"
            self.home_pdf_summary.config(text=self._truncate_middle(pdf_name, 28))
        if hasattr(self, "home_folder_summary"):
            active_routes = sum(1 for item in self.company_route_mappings if item.get("active", True))
            folder_name = f"{active_routes} empresa(s)" if active_routes else "Sin mapeos"
            self.home_folder_summary.config(text=self._truncate_middle(folder_name, 30))
        if hasattr(self, "home_clients_summary"):
            self.home_clients_summary.config(text=str(len(self.clients)))

    def update_progress(self, current, total):
        if not hasattr(self, "progress_canvas"):
            return

        total = max(total, 1)
        progress = max(0, min(current / total, 1))

        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(
            0,
            0,
            420,
            12,
            fill="#efe5d8",
            outline="",
        )
        self.progress_canvas.create_rectangle(
            0,
            0,
            int(420 * progress),
            12,
            fill=self.colors["accent"],
            outline="",
        )

    def update_flow_preview(self):
        if not hasattr(self, "flow_canvas"):
            return

        canvas = self.flow_canvas
        canvas.delete("all")

        width = int(canvas.winfo_width() or 480)
        height = int(canvas.winfo_height() or 290)

        left_x = width * 0.22
        right_x = width * 0.78
        center_y = height * 0.54

        source_folder = os.path.basename(os.path.dirname(self.pdf_path)) if self.pdf_path else "Carpeta origen"
        source_name = os.path.basename(self.pdf_path) if self.pdf_path else "archivo.pdf"
        target_folder = "Ruta segun empresa" if self.company_route_mappings else "Carpeta destino"
        target_name = "NCF_RazonSocial.pdf"

        canvas.create_text(
            left_x,
            30,
            text=source_folder,
            fill=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        canvas.create_text(
            right_x,
            30,
            text=target_folder,
            fill=self.colors["muted"],
            font=("Segoe UI", 10),
        )

        self._draw_pdf_icon(left_x, center_y, self.colors["accent_soft"], self.colors["accent_dark"], "PDF")
        self._draw_pdf_icon(right_x, center_y, "#ffece7", self.colors["accent"], "PDF")

        canvas.create_text(
            left_x,
            center_y + 66,
            text=self._truncate_middle(source_name, 26),
            fill=self.colors["text"],
            font=("Segoe UI Semibold", 10),
        )
        canvas.create_text(
            right_x,
            center_y + 66,
            text=self._truncate_middle(target_name, 26),
            fill=self.colors["text"],
            font=("Segoe UI Semibold", 10),
        )

        canvas.create_line(
            left_x + 70,
            center_y,
            right_x - 70,
            center_y,
            fill=self.colors["accent"],
            width=3,
            smooth=True,
        )
        canvas.create_polygon(
            right_x - 74,
            center_y - 12,
            right_x - 40,
            center_y,
            right_x - 74,
            center_y + 12,
            fill=self.colors["accent"],
            outline=self.colors["accent"],
        )

        canvas.create_text(
            width / 2,
            center_y - 30,
            text="Renombrar y mover",
            fill=self.colors["accent_dark"],
            font=("Segoe UI Semibold", 11),
        )

    def _draw_pdf_icon(self, x, y, fill_color, outline_color, text):
        w = 62
        h = 78
        fold = 16

        self.flow_canvas.create_polygon(
            x - w / 2,
            y - h / 2,
            x + w / 2 - fold,
            y - h / 2,
            x + w / 2,
            y - h / 2 + fold,
            x + w / 2,
            y + h / 2,
            x - w / 2,
            y + h / 2,
            fill=fill_color,
            outline=outline_color,
            width=2,
            smooth=False,
        )
        self.flow_canvas.create_line(
            x + w / 2 - fold,
            y - h / 2,
            x + w / 2 - fold,
            y - h / 2 + fold,
            x + w / 2,
            y - h / 2 + fold,
            fill=outline_color,
            width=2,
        )
        self.flow_canvas.create_text(
            x,
            y + 2,
            text=text,
            fill=outline_color,
            font=("Segoe UI Semibold", 12),
        )

    def log(self, message):
        if not hasattr(self, "log_text"):
            print(message)
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def copy_log(self, message):
        if not hasattr(self, "copy_log_text"):
            return
        self.copy_log_text.configure(state="normal")
        self.copy_log_text.insert(tk.END, message + "\n")
        self.copy_log_text.see(tk.END)
        self.copy_log_text.configure(state="disabled")



    def _on_message_input_change(self, *_args):
        self.update_message_preview()

    def _on_message_fiscal_buyer_change(self, *_args):
        selected_label = self.message_fiscal_buyer_var.get().strip()
        buyer_name = self.message_fiscal_buyer_map.get(selected_label, "")
        if buyer_name:
            self.message_client_name_var.set(buyer_name)
        else:
            self.update_message_preview()

    def refresh_message_fiscal_buyer_selector(self):
        if not hasattr(self, "message_fiscal_buyer_selector"):
            return

        buyer_labels = []
        self.message_fiscal_buyer_map = {}
        for buyer in self.fiscal_buyers:
            name = str(buyer.get("name", "")).strip()
            if not name:
                continue

            email = str(buyer.get("email", "")).strip()
            label = f"{name} - {email}" if email else name
            duplicate_count = 2
            original_label = label
            while label in self.message_fiscal_buyer_map:
                label = f"{original_label} ({duplicate_count})"
                duplicate_count += 1

            buyer_labels.append(label)
            self.message_fiscal_buyer_map[label] = name

        self.message_fiscal_buyer_selector.configure(values=tuple(buyer_labels))
        if self.message_fiscal_buyer_var.get() not in self.message_fiscal_buyer_map:
            self.message_fiscal_buyer_var.set("")

    def _on_copy_name_change(self, *_args):
        self.update_copy_summary()

    def update_copy_summary(self):
        source_name = os.path.basename(self.copy_source_pdf) if self.copy_source_pdf else "Sin archivo"
        folder_name = os.path.dirname(self.copy_source_pdf) if self.copy_source_pdf else ""
        variable_name = self.copy_name_var.get().strip() or "NOMBRE"
        proposal_type = self.copy_proposal_type_var.get().strip() or "mensual"
        preview_name = self.build_proposal_name(variable_name, proposal_type)

        if hasattr(self, "copy_source_summary"):
            self.copy_source_summary.config(text=self._truncate_middle(source_name, 32))
        if hasattr(self, "copy_source_label"):
            label_value = self.copy_source_pdf if self.copy_source_pdf else "(no seleccionado)"
            self.copy_source_label.config(text=f"PDF actual: {label_value}")
        if hasattr(self, "copy_preview_label"):
            self.copy_preview_label.config(text=f"Archivo nuevo: {preview_name}.pdf")
        if hasattr(self, "copy_folder_label"):
            folder_value = folder_name if folder_name else "(sin carpeta)"
            self.copy_folder_label.config(text=f"Carpeta: {folder_value}")


    def get_message_type_label(self, message_type):
        labels = {
            "plantilla_fiscal": "Plantilla fiscal",
            "Plantilla fiscal": "Plantilla fiscal",
        }
        return labels.get(message_type, "Mensaje")

    def normalize_message_type(self, message_type):
        normalized = (message_type or "").strip().lower().replace(" ", "_")
        if normalized == "plantilla_fiscal":
            return "plantilla_fiscal"
        return normalized

    def build_generated_message(self):
        client_name = self.message_client_name_var.get().strip() or "nombre"
        message_type = self.normalize_message_type(self.message_type_var.get()) or "plantilla_fiscal"

        if message_type == "plantilla_fiscal":
            return (
                f"Hola, {client_name} 👋, Gracias por tu compra.\n\n"
                "Te informamos que la plantilla tiene una duración de 365 días a partir de hoy.\n\n"
                "⚠️ Importante antes de usarla:\n"
                "Antes de abrir el archivo, debes de activar las macros, ya que esto es necesario para que la plantilla funcione correctamente.\n\n"
                "A continuación te comparto los enlaces de apoyo:\n\n"
                "📌 Primer uso (cómo activar las macros):\n"
                "https://youtu.be/i-_2RdeaRko?si=eELy0jSVx9VWXEzV\n\n"
                "📌 Tutoriales de uso:\n"
                "https://www.rddebito.com/servicios/plantillas/plantilla-fiscal/tutoriales\n\n"
                "Si tienes alguna duda o necesitas ayuda, puedes escribirme con confianza. Estoy para ayudarte 👍\n\n"
                "¡Éxitos con la plantilla! 🚀"
            )

        return f'Hola "{client_name}"'

    def update_message_preview(self):
        message_value = self.build_generated_message()
        client_name = self.message_client_name_var.get().strip() or "Sin nombre"
        message_type_label = self.get_message_type_label(self.message_type_var.get().strip())

        if hasattr(self, "message_type_summary"):
            self.message_type_summary.config(text=message_type_label)
        if hasattr(self, "message_client_summary"):
            self.message_client_summary.config(text=self._truncate_middle(client_name, 28))
        if hasattr(self, "message_preview_text"):
            self.message_preview_text.configure(state="normal")
            self.message_preview_text.delete("1.0", tk.END)
            self.message_preview_text.insert("1.0", message_value)
            self.message_preview_text.configure(state="disabled")

    def copy_generated_message(self):
        message_value = self.build_generated_message().strip()
        if not message_value:
            messagebox.showwarning("Aviso", "No hay mensaje para copiar.")
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(message_value)
            self.root.update()
            self._set_copy_button_state("copy_message_button", copied=True)
            messagebox.showinfo("Mensaje copiado", "El mensaje fue copiado al portapapeles.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar el mensaje.\n\nDetalle: {e}")


    def _update_client_list_scrollregion(self, _event=None):
        if hasattr(self, "client_list_canvas"):
            self.client_list_canvas.configure(scrollregion=self.client_list_canvas.bbox("all"))

    def _resize_client_list_inner(self, event):
        if hasattr(self, "client_list_window"):
            self.client_list_canvas.itemconfigure(self.client_list_window, width=event.width)

    def _on_client_search_change(self, *_args):
        self.refresh_clients_list()

    def refresh_clients_ui(self):
        self.refresh_clients_summary()
        self.refresh_clients_list()
        self.update_client_resource_label()
        self.update_client_extra_toggle()
        self.update_client_detail_hint()
        self.update_client_detail_panel_visibility()

    def refresh_clients_summary(self):
        if hasattr(self, "clients_total_summary"):
            self.clients_total_summary.config(text=str(len(self.clients)))
        self.update_home_dashboard()











































































































    def get_filtered_clients(self):
        query = self.client_search_var.get().strip().lower()
        if not query:
            return list(self.clients)

        filtered = []
        for client in self.clients:
            searchable = " ".join(
                [
                    client.get("name", ""),
                    client.get("rnc", ""),
                    client.get("pc_location", ""),
                    client.get("cedula", ""),
                    client.get("tss_class", ""),
                    client.get("work_description", ""),
                ]
            ).lower()
            if query in searchable:
                filtered.append(client)
        return filtered

    def refresh_clients_list(self):
        if not hasattr(self, "client_list_inner"):
            return

        for widget in self.client_list_inner.winfo_children():
            widget.destroy()

        filtered_clients = self.get_filtered_clients()
        if filtered_clients:
            for row, client in enumerate(filtered_clients):
                self._build_client_card(row, client)
        else:
            empty = tk.Frame(self.client_list_inner, bg=self.colors["clients_bg"], padx=18, pady=28)
            empty.grid(row=0, column=0, sticky="ew")
            tk.Label(
                empty,
                text="No hay clientes que coincidan con la busqueda.",
                bg=self.colors["clients_bg"],
                fg=self.colors["clients_muted"],
                font=("Segoe UI", 11),
                anchor="w",
                justify="left",
            ).pack(anchor="w")

        self._update_client_list_scrollregion()

    def _build_client_card(self, row, client):
        is_active = client.get("id") == self.selected_client_id
        bg = self.colors["clients_active"] if is_active else self.colors["clients_card"]
        hover_bg = self.colors["clients_hover"] if not is_active else self.colors["clients_active"]

        card = tk.Frame(
            self.client_list_inner,
            bg=bg,
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=12,
            cursor="hand2",
        )
        card.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)

        avatar = tk.Canvas(card, width=52, height=52, bg=bg, highlightthickness=0, bd=0)
        avatar.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))
        avatar.create_oval(4, 4, 48, 48, fill=self.colors["clients_accent"], outline="")
        initials = self.get_client_initials(client.get("name", ""))
        avatar.create_text(26, 26, text=initials, fill="#083d20", font=("Segoe UI Semibold", 13))

        tk.Label(
            card,
            text=client.get("name", "Sin nombre"),
            bg=bg,
            fg=self.colors["clients_text"],
            font=("Segoe UI Semibold", 12),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        location_value = client.get("pc_location", "").strip() or "Sin ubicacion en PC"
        tk.Label(
            card,
            text=self._truncate_middle(location_value, 42),
            bg=bg,
            fg=self.colors["clients_muted"],
            font=("Segoe UI", 9),
            anchor="e",
        ).grid(row=0, column=2, sticky="e")

        description = client.get("work_description", "").strip() or "Sin descripcion del trabajo"
        snippet = self._truncate_middle(description.replace("\n", " "), 58)
        tk.Label(
            card,
            text=f"RNC: {client.get('rnc', '').strip() or 'Sin RNC'}",
            bg=bg,
            fg=self.colors["clients_text"],
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=1, sticky="w")
        tk.Label(
            card,
            text=snippet,
            bg=bg,
            fg=self.colors["clients_muted"],
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        ).grid(row=2, column=1, columnspan=2, sticky="ew", pady=(6, 0))

        def bind_click(widget):
            widget.bind("<Button-1>", lambda _event, client_id=client.get("id"): self.select_client(client_id))
            widget.bind("<Enter>", lambda _event: self._set_client_card_background(card, avatar, hover_bg))
            widget.bind("<Leave>", lambda _event, normal_bg=bg: self._set_client_card_background(card, avatar, normal_bg))

        bind_click(card)
        for child in card.winfo_children():
            bind_click(child)

    def _set_client_card_background(self, card, avatar, color):
        card.configure(bg=color)
        avatar.configure(bg=color)
        for child in card.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=color)

    def get_client_initials(self, name):
        parts = [part for part in name.strip().split() if part]
        if not parts:
            return "CL"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()

    def prepare_new_client(self, select_first=False, show_form=True):
        if not self.confirm_discard_or_save_client_changes():
            return

        self.selected_client_id = None
        self.client_form_visible = show_form
        self.client_name_var.set("")
        self.client_rnc_var.set("")
        self.client_pc_location_var.set("")
        self.client_cedula_var.set("")
        self.client_tss_class_var.set("")
        self.client_resource_path_var.set("")
        if hasattr(self, "client_description_text"):
            self.client_description_text.delete("1.0", tk.END)
        self.reset_client_copy_buttons()
        self.client_extra_visible = False
        self.set_client_extra_section_visibility()
        self.update_client_detail_hint()
        self.update_client_resource_label()
        self.refresh_clients_list()
        if select_first and self.clients:
            self.select_client(self.clients[0].get("id"))
            return
        self.update_client_detail_panel_visibility()

    def update_client_detail_hint(self):
        if not hasattr(self, "client_detail_hint"):
            return
        if self.selected_client_id:
            self.client_detail_hint.config(text="Edita los datos del cliente seleccionado y presiona Guardar cliente.")
        else:
            self.client_detail_hint.config(text="Completa el formulario y guarda. Si no hay cliente seleccionado, se crea uno nuevo.")

    def update_client_detail_panel_visibility(self):
        if not hasattr(self, "client_empty_state") or not hasattr(self, "client_detail_content"):
            return
        if self.client_form_visible:
            self.client_empty_state.grid_remove()
            self.client_detail_content.grid()
            if hasattr(self, "client_close_button"):
                self.client_close_button.grid()
        else:
            self.client_detail_content.grid_remove()
            self.client_empty_state.grid()
            if hasattr(self, "client_close_button"):
                self.client_close_button.grid_remove()

    def select_client(self, client_id):
        if client_id == self.selected_client_id:
            return

        if not self.confirm_discard_or_save_client_changes():
            return

        client = self.find_client_by_id(client_id)
        if not client:
            return

        self.selected_client_id = client_id
        self.client_form_visible = True
        self.client_name_var.set(client.get("name", ""))
        self.client_rnc_var.set(client.get("rnc", ""))
        self.client_pc_location_var.set(client.get("pc_location", ""))
        self.client_cedula_var.set(client.get("cedula", ""))
        self.client_tss_class_var.set(client.get("tss_class", ""))
        self.client_resource_path_var.set(client.get("resource_path", ""))
        if hasattr(self, "client_description_text"):
            self.client_description_text.delete("1.0", tk.END)
            self.client_description_text.insert("1.0", client.get("work_description", ""))
        self.reset_client_copy_buttons()
        self.client_extra_visible = False
        self.set_client_extra_section_visibility()
        self.update_client_detail_hint()
        self.update_client_resource_label()
        self.update_client_detail_panel_visibility()
        self.refresh_clients_list()

    def get_client_form_record(self):
        work_description = ""
        if hasattr(self, "client_description_text"):
            work_description = self.client_description_text.get("1.0", tk.END).strip()

        return {
            "id": self.selected_client_id or "",
            "name": self.client_name_var.get().strip(),
            "rnc": self.client_rnc_var.get().strip(),
            "pc_location": self.client_pc_location_var.get().strip(),
            "cedula": self.client_cedula_var.get().strip(),
            "tss_class": self.client_tss_class_var.get().strip(),
            "resource_path": self.client_resource_path_var.get().strip(),
            "work_description": work_description,
        }

    def has_unsaved_client_changes(self):
        if not self.selected_client_id:
            return False

        client = self.find_client_by_id(self.selected_client_id)
        if not client:
            return False

        current = self.get_client_form_record()
        saved = self.normalize_client_record(client) or {}
        fields = ("name", "rnc", "pc_location", "cedula", "tss_class", "resource_path", "work_description")
        return any(current.get(field, "") != saved.get(field, "") for field in fields)

    def confirm_discard_or_save_client_changes(self):
        if not self.has_unsaved_client_changes():
            return True

        client_name = self.client_name_var.get().strip() or "este cliente"
        choice = messagebox.askyesnocancel(
            "Guardar cambios",
            f"Hay cambios sin guardar en {client_name}.\n\n¿Deseas guardarlos antes de cambiar de cliente?",
        )
        if choice is None:
            return False
        if choice is False:
            return True

        payload = self.build_client_payload()
        if not payload:
            return False
        if not self.save_client_to_db(payload):
            messagebox.showerror("Error", "No se pudieron guardar los cambios del cliente.")
            return False

        self.load_clients_from_db()
        self.refresh_clients_ui()
        self.log(f"[INFO] Cliente actualizado: {payload['name']}")
        return True

    def find_client_by_id(self, client_id):
        for client in self.clients:
            if client.get("id") == client_id:
                return client
        return None

    def normalize_client_record(self, client):
        if not isinstance(client, dict):
            return None

        name = str(client.get("name", "")).strip()
        if not name:
            return None

        return {
            "id": str(client.get("id") or uuid.uuid4()),
            "name": name,
            "rnc": str(client.get("rnc", "")).strip(),
            "pc_location": str(client.get("pc_location", "")).strip(),
            "cedula": str(client.get("cedula", "")).strip(),
            "tss_class": str(client.get("tss_class", "")).strip(),
            "resource_path": str(client.get("resource_path", "")).strip(),
            "work_description": str(client.get("work_description", "")).strip(),
        }

    def normalize_fiscal_version_record(self, version_data):
        if not isinstance(version_data, dict):
            return None

        version = str(version_data.get("version", "")).strip()
        change_date = str(version_data.get("change_date", "")).strip()
        change_type = str(version_data.get("change_type", "")).strip()
        description = str(version_data.get("description", "")).strip()
        affects_macros = str(version_data.get("affects_macros", "")).strip() or "No"
        requires_manual_update = str(version_data.get("requires_manual_update", "")).strip() or "No"

        if not version or not change_date or not change_type or not description:
            return None

        try:
            datetime.strptime(change_date, "%Y-%m-%d")
        except ValueError:
            return None

        return {
            "id": str(version_data.get("id") or uuid.uuid4()),
            "version": version,
            "change_date": change_date,
            "change_type": change_type,
            "description": description,
            "affects_macros": "Si" if affects_macros.lower() == "si" else "No",
            "requires_manual_update": "Si" if requires_manual_update.lower() == "si" else "No",
        }

    def normalize_fiscal_buyer_record(self, buyer_data):
        if not isinstance(buyer_data, dict):
            return None

        name = str(buyer_data.get("name", "")).strip()
        purchase_date = str(buyer_data.get("purchase_date", "")).strip()
        expiration_date = str(buyer_data.get("expiration_date", "")).strip()
        email = str(buyer_data.get("email", "")).strip()
        price = self.parse_money_value(buyer_data.get("price", ""))
        channel = str(buyer_data.get("channel", "")).strip().lower()
        valid_channels = {"instagram", "youtube", "pagina web", "desconocido"}

        if not name or not purchase_date or not expiration_date or not email or price is None:
            return None
        if channel not in valid_channels:
            channel = "desconocido"

        try:
            datetime.strptime(purchase_date, "%Y-%m-%d")
            datetime.strptime(expiration_date, "%Y-%m-%d")
        except ValueError:
            return None

        return {
            "id": str(buyer_data.get("id") or uuid.uuid4()),
            "name": name,
            "purchase_date": purchase_date,
            "expiration_date": expiration_date,
            "email": email,
            "price": price,
            "channel": channel,
        }

    def parse_money_value(self, value):
        if isinstance(value, (int, float)):
            return float(value)

        clean_value = str(value or "").strip()
        if not clean_value:
            return None

        clean_value = clean_value.replace("RD$", "").replace("$", "").replace(" ", "")
        if "," in clean_value and "." in clean_value:
            clean_value = clean_value.replace(",", "")
        else:
            clean_value = clean_value.replace(",", "")

        try:
            parsed = float(clean_value)
        except ValueError:
            return None

        if parsed < 0:
            return None
        return parsed

    def format_money_value(self, value):
        amount = self.parse_money_value(value)
        if amount is None:
            amount = 0
        return f"RD${amount:,.2f}"

    def load_fiscal_versions_from_db(self):
        try:
            self.fiscal_versions = self.services.fiscal.versions()
        except Exception:
            self.fiscal_versions = []

    def save_fiscal_version_to_db(self, payload):
        normalized = self.normalize_fiscal_version_record(payload)
        if not normalized:
            return False
        try:
            self.services.fiscal.save_version(normalized)
            return True
        except ValueError:
            return False

    def load_fiscal_buyers_from_db(self):
        try:
            self.fiscal_buyers = self.services.fiscal.buyers()
        except Exception:
            self.fiscal_buyers = []

    def save_fiscal_buyer_to_db(self, payload):
        normalized = self.normalize_fiscal_buyer_record(payload)
        if not normalized:
            return False
        try:
            self.services.fiscal.save_buyer(normalized)
            return True
        except ValueError:
            return False

    def refresh_fiscal_template_summary(self):
        if hasattr(self, "fiscal_versions_summary"):
            self.fiscal_versions_summary.config(text=str(len(self.fiscal_versions)))
        if hasattr(self, "fiscal_buyers_summary"):
            self.fiscal_buyers_summary.config(text=str(len(self.fiscal_buyers)))
        total_price = sum(self.parse_money_value(item.get("price", 0)) or 0 for item in self.fiscal_buyers)
        gross_profit = total_price - (total_price * 0.18)
        if hasattr(self, "fiscal_net_profit_summary"):
            self.fiscal_net_profit_summary.config(text=self.format_money_value(total_price))
        if hasattr(self, "fiscal_gross_profit_summary"):
            self.fiscal_gross_profit_summary.config(text=self.format_money_value(gross_profit))

    def refresh_fiscal_versions_tree(self):
        if not hasattr(self, "fiscal_versions_tree"):
            return

        for item_id in self.fiscal_versions_tree.get_children():
            self.fiscal_versions_tree.delete(item_id)

        for item in self.fiscal_versions:
            self.fiscal_versions_tree.insert(
                "",
                tk.END,
                values=(
                    item.get("version", ""),
                    item.get("change_date", ""),
                    item.get("change_type", ""),
                    item.get("description", ""),
                    item.get("affects_macros", ""),
                    item.get("requires_manual_update", ""),
                ),
            )

    def refresh_fiscal_buyers_tree(self):
        if not hasattr(self, "fiscal_buyers_tree"):
            self.refresh_message_fiscal_buyer_selector()
            return

        for item_id in self.fiscal_buyers_tree.get_children():
            self.fiscal_buyers_tree.delete(item_id)

        for item in self.fiscal_buyers:
            self.fiscal_buyers_tree.insert(
                "",
                tk.END,
                values=(
                    item.get("name", ""),
                    item.get("purchase_date", ""),
                    item.get("expiration_date", ""),
                    item.get("email", ""),
                    self.format_money_value(item.get("price", 0)),
                    item.get("channel", "desconocido"),
                ),
                iid=item.get("id", ""),
            )

        self.refresh_message_fiscal_buyer_selector()

    def reset_fiscal_version_form(self):
        self.fiscal_version_var.set("")
        self.fiscal_version_date_var.set(date.today().isoformat())
        self.fiscal_version_change_type_var.set("Lanzamiento")
        self.fiscal_version_description_var.set("")
        self.fiscal_version_affects_macros_var.set("Si")
        self.fiscal_version_requires_manual_var.set("No")

    def reset_fiscal_buyer_form(self):
        self.selected_fiscal_buyer_id = None
        self.fiscal_buyer_name_var.set("")
        self.fiscal_buyer_purchase_date_var.set(date.today().isoformat())
        self.fiscal_buyer_expiration_date_var.set("")
        self.fiscal_buyer_email_var.set("")
        self.fiscal_buyer_price_var.set("3,000")
        self.fiscal_buyer_channel_var.set("desconocido")
        if hasattr(self, "fiscal_buyer_save_button"):
            self.fiscal_buyer_save_button.config(text="Guardar comprador")
        if hasattr(self, "fiscal_buyers_tree"):
            for item_id in self.fiscal_buyers_tree.selection():
                self.fiscal_buyers_tree.selection_remove(item_id)

    def load_selected_fiscal_buyer_into_form(self, _event=None):
        if not hasattr(self, "fiscal_buyers_tree"):
            return

        selection = self.fiscal_buyers_tree.selection()
        if not selection:
            return

        buyer_id = selection[0]
        buyer = next((item for item in self.fiscal_buyers if item.get("id") == buyer_id), None)
        if not buyer:
            return

        self.selected_fiscal_buyer_id = buyer_id
        self.fiscal_buyer_name_var.set(buyer.get("name", ""))
        self.fiscal_buyer_purchase_date_var.set(buyer.get("purchase_date", ""))
        self.fiscal_buyer_expiration_date_var.set(buyer.get("expiration_date", ""))
        self.fiscal_buyer_email_var.set(buyer.get("email", ""))
        price = self.parse_money_value(buyer.get("price", 3000))
        self.fiscal_buyer_price_var.set(f"{price:,.0f}" if price is not None else "3,000")
        self.fiscal_buyer_channel_var.set(buyer.get("channel", "desconocido") or "desconocido")
        if hasattr(self, "fiscal_buyer_save_button"):
            self.fiscal_buyer_save_button.config(text="Actualizar comprador")

    def save_fiscal_version(self):
        payload = {
            "version": self.fiscal_version_var.get(),
            "change_date": self.fiscal_version_date_var.get(),
            "change_type": self.fiscal_version_change_type_var.get(),
            "description": self.fiscal_version_description_var.get(),
            "affects_macros": self.fiscal_version_affects_macros_var.get(),
            "requires_manual_update": self.fiscal_version_requires_manual_var.get(),
        }

        if not self.save_fiscal_version_to_db(payload):
            messagebox.showwarning(
                "Aviso",
                "Completa todos los campos de la version y usa fecha en formato AAAA-MM-DD.",
            )
            return

        self.load_fiscal_versions_from_db()
        self.refresh_fiscal_versions_tree()
        self.reset_fiscal_version_form()
        self.log(f"[INFO] Version fiscal guardada: {payload['version']}")

    def save_fiscal_buyer(self):
        payload = {
            "id": self.selected_fiscal_buyer_id,
            "name": self.fiscal_buyer_name_var.get(),
            "purchase_date": self.fiscal_buyer_purchase_date_var.get(),
            "expiration_date": self.fiscal_buyer_expiration_date_var.get(),
            "email": self.fiscal_buyer_email_var.get(),
            "price": self.fiscal_buyer_price_var.get(),
            "channel": self.fiscal_buyer_channel_var.get(),
        }

        if not self.save_fiscal_buyer_to_db(payload):
            messagebox.showwarning(
                "Aviso",
                "Completa todos los campos del comprador, usa fechas en formato AAAA-MM-DD y un precio valido.",
            )
            return

        action_text = "actualizado" if self.selected_fiscal_buyer_id else "guardado"
        self.load_fiscal_buyers_from_db()
        self.refresh_fiscal_buyers_tree()
        self.reset_fiscal_buyer_form()
        self.log(f"[INFO] Comprador de plantilla fiscal {action_text}: {payload['name']}")

    def get_selected_fiscal_version_description(self):
        if not hasattr(self, "fiscal_versions_tree"):
            return ""

        selection = self.fiscal_versions_tree.selection()
        if not selection:
            return ""

        values = self.fiscal_versions_tree.item(selection[0], "values")
        if len(values) < 4:
            return ""

        return str(values[3]).strip()

    def copy_fiscal_version_description(self, _event=None):
        description = self.get_selected_fiscal_version_description()
        self._copy_client_field(
            description,
            "Selecciona una version con descripcion para copiar.",
            "[INFO] Descripcion de version fiscal copiada al portapapeles: {value}",
            "fiscal_version_copy_button",
        )

    def get_selected_fiscal_buyer_values(self):
        if not hasattr(self, "fiscal_buyers_tree"):
            return ("", "")

        selection = self.fiscal_buyers_tree.selection()
        if not selection:
            return ("", "")

        values = self.fiscal_buyers_tree.item(selection[0], "values")
        if len(values) < 4:
            return ("", "")

        return str(values[0]).strip(), str(values[3]).strip()

    def copy_fiscal_buyer_name(self):
        buyer_name, _buyer_email = self.get_selected_fiscal_buyer_values()
        self._copy_client_field(
            buyer_name,
            "Selecciona un comprador con nombre para copiar.",
            "[INFO] Nombre de comprador fiscal copiado al portapapeles: {value}",
            "fiscal_buyer_copy_name_button",
        )

    def copy_fiscal_buyer_email(self):
        _buyer_name, buyer_email = self.get_selected_fiscal_buyer_values()
        self._copy_client_field(
            buyer_email,
            "Selecciona un comprador con correo para copiar.",
            "[INFO] Correo de comprador fiscal copiado al portapapeles: {value}",
            "fiscal_buyer_copy_email_button",
        )

    def get_db_connection(self):
        return self.services.database.connect()


    def init_database(self):
        self.services.database.initialize()






    def load_clients_from_db(self):
        try:
            self.clients = self.services.clients.list()
        except Exception:
            self.clients = []
        self.update_home_dashboard()

    def save_client_to_db(self, payload):
        normalized = self.normalize_client_record(payload)
        if not normalized:
            return False
        try:
            self.services.clients.save(normalized)
            return True
        except ValueError:
            return False

    def delete_client_from_db(self, client_id):
        return self.services.clients.delete(client_id)

    def ensure_client_default_folder(self, payload):
        if payload.get("pc_location", "").strip():
            return True

        folder_name = self.sanitize_filename(payload.get("name", ""))
        if not folder_name:
            messagebox.showwarning("Aviso", "El cliente debe tener un nombre valido para crear la carpeta.")
            return False

        folder_path = os.path.join(self.client_default_base_folder, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            self.log(f"[ERROR] No se pudo crear la carpeta del cliente. Detalle: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudo crear la carpeta del cliente.\n\nRuta:\n{folder_path}\n\nDetalle: {e}",
            )
            return False

        payload["pc_location"] = folder_path
        if hasattr(self, "client_pc_location_var") and (
            not self.selected_client_id or payload.get("id") == self.selected_client_id
        ):
            self.client_pc_location_var.set(folder_path)
        self.log(f"[INFO] Carpeta creada/asignada para cliente: {folder_path}")
        return True

    def select_client_location(self):
        initial_dir = self.client_pc_location_var.get().strip()
        selected = self.choose_folder("Selecciona la carpeta del cliente", initial_dir)
        if selected:
            self.client_pc_location_var.set(selected)
            self.log(f"[INFO] Carpeta del cliente seleccionada: {selected}")
            self.open_client_location()

    def open_client_location(self):
        location = self.client_pc_location_var.get().strip()
        if not location:
            messagebox.showwarning("Aviso", "El cliente no tiene una ubicacion en PC definida.")
            return

        if not os.path.isdir(location):
            messagebox.showwarning("Aviso", "La carpeta guardada no existe o no es valida.")
            return

        try:
            os.startfile(location)
            self.log(f"[INFO] Carpeta del cliente abierta: {location}")
        except Exception as e:
            self.log(f"[ERROR] No se pudo abrir la carpeta del cliente. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta del cliente.\n\nDetalle: {e}")

    def toggle_client_extra_section(self):
        self.client_extra_visible = not self.client_extra_visible
        self.set_client_extra_section_visibility()

    def set_client_extra_section_visibility(self):
        if not hasattr(self, "client_extra_frame"):
            return
        if self.client_extra_visible:
            self.client_extra_frame.grid(row=8, column=0, sticky="ew", pady=(0, 12))
        else:
            self.client_extra_frame.grid_forget()
        self.update_client_extra_toggle()

    def update_client_extra_toggle(self):
        if not hasattr(self, "client_extra_toggle"):
            return
        if self.client_extra_visible:
            self.client_extra_toggle.config(text="|\n▴ Datos TSS")
        else:
            self.client_extra_toggle.config(text="|\n▾ Datos TSS")

    def copy_client_rnc(self):
        rnc = self.client_rnc_var.get().strip()
        self._copy_client_field(
            rnc,
            "El cliente no tiene un RNC para copiar.",
            "[INFO] RNC copiado al portapapeles: {value}",
            "client_rnc_copy_button",
        )

    def _copy_client_field(self, value, empty_message, success_log, button_attr):
        if not value:
            messagebox.showwarning("Aviso", empty_message)
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self.root.update()
            self.log(success_log.format(value=value))
            self._set_copy_button_state(button_attr, copied=True)
        except Exception as e:
            self.log(f"[ERROR] No se pudo copiar el valor. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo copiar el valor.\n\nDetalle: {e}")

    def _set_copy_button_state(self, button_attr, copied):
        button = getattr(self, button_attr, None)
        if not button:
            return

        default_text = getattr(self, f"{button_attr}_default_text", "Copiar")
        reset_job_attr = f"{button_attr}_reset_job"
        pending_job = getattr(self, reset_job_attr, None)
        if pending_job:
            self.root.after_cancel(pending_job)
            setattr(self, reset_job_attr, None)

        if copied:
            button.config(text="Copiado")
            job_id = self.root.after(5000, lambda: self._set_copy_button_state(button_attr, copied=False))
            setattr(self, reset_job_attr, job_id)
        else:
            button.config(text=default_text)

    def reset_client_copy_buttons(self):
        self._set_copy_button_state("client_rnc_copy_button", copied=False)
        self._set_copy_button_state("client_cedula_copy_button", copied=False)
        self._set_copy_button_state("client_tss_class_copy_button", copied=False)

    def copy_client_cedula(self):
        cedula = self.client_cedula_var.get().strip()
        self._copy_client_field(
            cedula,
            "El cliente no tiene una cedula para copiar.",
            "[INFO] Cedula copiada al portapapeles: {value}",
            "client_cedula_copy_button",
        )

    def copy_client_tss_class(self):
        tss_class = self.client_tss_class_var.get().strip()
        self._copy_client_field(
            tss_class,
            "El cliente no tiene un class de TSS para copiar.",
            "[INFO] Class TSS copiada al portapapeles: {value}",
            "client_tss_class_copy_button",
        )

    def update_client_resource_label(self):
        if not hasattr(self, "client_resource_label"):
            return
        resource_path = self.client_resource_path_var.get().strip()
        if resource_path:
            self.client_resource_label.config(text=self._truncate_middle(resource_path, 54))
        else:
            self.client_resource_label.config(text="Sin recurso guardado")

    def open_client_resource(self):
        resource_path = self.client_resource_path_var.get().strip()

        if resource_path and os.path.exists(resource_path):
            try:
                os.startfile(resource_path)
                self.log(f"[INFO] Recurso del cliente abierto: {resource_path}")
            except Exception as e:
                self.log(f"[ERROR] No se pudo abrir el recurso del cliente. Detalle: {e}")
                messagebox.showerror("Error", f"No se pudo abrir el recurso del cliente.\n\nDetalle: {e}")
            return

        initial_dir = ""
        client_folder = self.client_pc_location_var.get().strip()
        if client_folder and os.path.isdir(client_folder):
            initial_dir = client_folder

        selected = filedialog.askopenfilename(
            title="Selecciona el recurso del cliente",
            initialdir=initial_dir,
            filetypes=[
                ("Archivos compatibles", "*.pdf;*.png;*.jpg;*.jpeg;*.webp;*.doc;*.docx;*.xls;*.xlsx;*.txt"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not selected:
            return

        self.client_resource_path_var.set(selected)
        self.update_client_resource_label()
        self.log(f"[INFO] Recurso del cliente guardado: {selected}")

        client = self.find_client_by_id(self.selected_client_id) if self.selected_client_id else None
        if client:
            client["resource_path"] = selected
            self.save_client_to_db(client)
            self.load_clients_from_db()

        try:
            os.startfile(selected)
            self.log(f"[INFO] Recurso del cliente abierto: {selected}")
        except Exception as e:
            self.log(f"[ERROR] No se pudo abrir el recurso del cliente. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el recurso del cliente.\n\nDetalle: {e}")

    def build_client_payload(self):
        name = self.client_name_var.get().strip()
        rnc = self.client_rnc_var.get().strip()
        pc_location = self.client_pc_location_var.get().strip()
        cedula = self.client_cedula_var.get().strip()
        tss_class = self.client_tss_class_var.get().strip()
        resource_path = self.client_resource_path_var.get().strip()
        work_description = self.client_description_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("Aviso", "El cliente debe tener al menos un nombre.")
            return None

        payload = {
            "id": self.selected_client_id or str(uuid.uuid4()),
            "name": name,
            "rnc": rnc,
            "pc_location": pc_location,
            "cedula": cedula,
            "tss_class": tss_class,
            "resource_path": resource_path,
            "work_description": work_description,
        }
        if not self.ensure_client_default_folder(payload):
            return None
        return payload

    def save_client(self):
        payload = self.build_client_payload()
        if not payload:
            return

        existing = self.find_client_by_id(payload["id"])
        if not self.save_client_to_db(payload):
            messagebox.showerror("Error", "No se pudo guardar el cliente en la base de datos.")
            return

        self.load_clients_from_db()
        if existing:
            self.log(f"[INFO] Cliente actualizado: {payload['name']}")
        else:
            self.log(f"[INFO] Cliente agregado: {payload['name']}")

        self.selected_client_id = payload["id"]
        self.refresh_clients_ui()
        self.select_client(payload["id"])

    def delete_client(self):
        if not self.selected_client_id:
            messagebox.showwarning("Aviso", "Selecciona un cliente de la lista para eliminarlo.")
            return

        client = self.find_client_by_id(self.selected_client_id)
        if not client:
            return

        confirmed = messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas eliminar el cliente '{client.get('name', 'Sin nombre')}'?",
        )
        if not confirmed:
            return

        self.delete_client_from_db(self.selected_client_id)
        self.load_clients_from_db()
        self.log(f"[INFO] Cliente eliminado: {client.get('name', 'Sin nombre')}")
        self.prepare_new_client(show_form=False)
        self.refresh_clients_ui()

    def normalize_text_for_match(self, value):
        normalized = unicodedata.normalize("NFKD", value or "")
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = re.sub(r"[^A-Z0-9]+", " ", normalized.upper())
        return re.sub(r"\s+", " ", normalized).strip()

    def normalize_company_route_mappings(self, mappings):
        normalized = []
        seen = set()
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            company = str(mapping.get("company", "")).strip()
            folder = str(mapping.get("folder", "")).strip()
            if not company:
                continue
            key = self.normalize_text_for_match(company)
            if not key or key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "company": company,
                    "folder": folder,
                    "active": bool(mapping.get("active", True)),
                }
            )
        return normalized

    def ensure_default_company_routes(self):
        existing = {self.normalize_text_for_match(item.get("company", "")) for item in self.company_route_mappings}
        default_pairs = [
            ("DEBITO SRL", self.find_saved_folder_hint("DEBITO")),
            ("KALIL RENE ENCARNACION MARIÑEZ", self.find_saved_folder_hint("KALIL")),
        ]
        changed = False
        for company, folder in default_pairs:
            key = self.normalize_text_for_match(company)
            if key not in existing:
                self.company_route_mappings.append(
                    {
                        "company": company,
                        "folder": folder,
                        "active": True,
                    }
                )
                existing.add(key)
                changed = True
        return changed

    def find_saved_folder_hint(self, keyword):
        key = self.normalize_text_for_match(keyword)
        for folder in self.saved_folders:
            if key and key in self.normalize_text_for_match(folder):
                return folder
        return ""

    def refresh_company_routes_ui(self):
        if not hasattr(self, "company_routes_tree"):
            return
        self.company_routes_tree.delete(*self.company_routes_tree.get_children())
        for index, mapping in enumerate(self.company_route_mappings):
            folder = mapping.get("folder", "") or "(sin ruta)"
            self.company_routes_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(mapping.get("company", ""), self._truncate_middle(folder, 68)),
            )
        if hasattr(self, "output_label"):
            self.output_label.config(
                text=f"Mapeos activos: {sum(1 for item in self.company_route_mappings if item.get('active', True))}"
            )
        self.update_summary()
        self.update_flow_preview()

    def get_selected_company_route_index(self):
        if not hasattr(self, "company_routes_tree"):
            return None
        selected = self.company_routes_tree.selection()
        if not selected:
            return None
        try:
            index = int(selected[0])
        except ValueError:
            return None
        if 0 <= index < len(self.company_route_mappings):
            return index
        return None

    def load_selected_company_route_into_form(self, _event=None):
        index = self.get_selected_company_route_index()
        if index is None:
            return
        mapping = self.company_route_mappings[index]
        self.company_name_var.set(mapping.get("company", ""))
        self.company_route_var.set(mapping.get("folder", ""))

    def clear_company_route_form(self):
        if hasattr(self, "company_routes_tree"):
            self.company_routes_tree.selection_remove(self.company_routes_tree.selection())
        self.company_name_var.set("")
        self.company_route_var.set("")

    def choose_company_route_for_form(self):
        selected = self.choose_folder("Selecciona la carpeta destino de la empresa", self.company_route_var.get())
        if selected:
            self.company_route_var.set(selected)

    def choose_company_route_for_selected(self):
        index = self.get_selected_company_route_index()
        if index is None:
            messagebox.showwarning("Aviso", "Selecciona una empresa para cambiar su ruta.")
            return
        current_folder = self.company_route_mappings[index].get("folder", "")
        selected = self.choose_folder("Selecciona la nueva carpeta destino", current_folder)
        if not selected:
            return
        self.company_route_mappings[index]["folder"] = selected
        self.company_route_var.set(selected)
        self.save_config()
        self.refresh_company_routes_ui()
        self.log(f"[INFO] Ruta de empresa actualizada: {self.company_route_mappings[index]['company']} -> {selected}")

    def save_company_route_from_form(self):
        company = self.company_name_var.get().strip()
        folder = self.company_route_var.get().strip()
        if not company:
            messagebox.showwarning("Aviso", "Escribe el nombre de la empresa.")
            return
        if not folder:
            messagebox.showwarning("Aviso", "Selecciona o escribe la ruta de destino.")
            return

        key = self.normalize_text_for_match(company)
        index = self.get_selected_company_route_index()
        if index is None:
            for candidate_index, mapping in enumerate(self.company_route_mappings):
                if self.normalize_text_for_match(mapping.get("company", "")) == key:
                    index = candidate_index
                    break

        mapping = {"company": company, "folder": folder, "active": True}
        if index is None:
            self.company_route_mappings.append(mapping)
            self.log(f"[INFO] Empresa agregada al mapeo: {company}")
        else:
            self.company_route_mappings[index] = mapping
            self.log(f"[INFO] Empresa actualizada en el mapeo: {company}")

        if folder not in self.saved_folders:
            self.saved_folders.append(folder)
        self.save_config()
        self.refresh_folder_selector()
        self.refresh_company_routes_ui()

    def delete_company_route(self):
        index = self.get_selected_company_route_index()
        if index is None:
            messagebox.showwarning("Aviso", "Selecciona una empresa para borrarla.")
            return
        mapping = self.company_route_mappings[index]
        confirmed = messagebox.askyesno(
            "Confirmar borrado",
            f"Deseas borrar el mapeo de esta empresa?\n\n{mapping.get('company', '')}",
        )
        if not confirmed:
            return
        removed = self.company_route_mappings.pop(index)
        self.save_config()
        self.clear_company_route_form()
        self.refresh_company_routes_ui()
        self.log(f"[INFO] Empresa eliminada del mapeo: {removed.get('company', '')}")

    def find_company_route_for_text(self, text):
        normalized_text = self.normalize_text_for_match(text)
        matches = []
        for mapping in self.company_route_mappings:
            if not mapping.get("active", True):
                continue
            company = mapping.get("company", "")
            key = self.normalize_text_for_match(company)
            folder = mapping.get("folder", "")
            if key and folder and key in normalized_text:
                matches.append((len(key), mapping))
        if not matches:
            return None
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.ensure_default_company_routes()
            self.load_clients_from_db()
            return

        try:
            data = self.services.config.load()
            folders = data.get("saved_folders", [])
            selected_folder = data.get("selected_output_folder", "")
            legacy_folder = data.get("output_folder", "")
            copy_source_pdf = data.get("copy_source_pdf", "")
            company_routes = data.get("company_route_mappings", [])
            pomodoro_state = data.get("pomodoro_state", {})
            pomodoro_settings = data.get("pomodoro_settings", {})

            if isinstance(folders, list):
                self.saved_folders = [folder for folder in folders if isinstance(folder, str) and folder.strip()]

            if isinstance(legacy_folder, str) and legacy_folder.strip() and legacy_folder not in self.saved_folders:
                self.saved_folders.append(legacy_folder)

            if isinstance(selected_folder, str) and selected_folder in self.saved_folders:
                self.output_folder = selected_folder
            elif self.saved_folders:
                self.output_folder = self.saved_folders[0]

            if isinstance(copy_source_pdf, str) and copy_source_pdf.strip():
                self.copy_source_pdf = copy_source_pdf
            if isinstance(company_routes, list):
                self.company_route_mappings = self.normalize_company_route_mappings(company_routes)
            self.load_pomodoro_settings(pomodoro_settings)
            self.pomodoro_state = self.normalize_pomodoro_state(pomodoro_state)
            self.ensure_default_company_routes()
        except Exception:
            self.output_folder = ""
            self.saved_folders = []
            self.company_route_mappings = []
            self.copy_source_pdf = ""
            self.pomodoro_state = self.get_default_pomodoro_state()
            self.ensure_default_company_routes()
        self.load_clients_from_db()

    def save_config(self):
        data = {
            "selected_output_folder": self.output_folder,
            "saved_folders": self.saved_folders,
            "company_route_mappings": self.company_route_mappings,
            "copy_source_pdf": self.copy_source_pdf,
            "pomodoro_settings": self.get_pomodoro_settings(),
            "pomodoro_state": self.get_serializable_pomodoro_state(),
        }
        self.services.config.save(data)

    def refresh_folder_selector(self):
        if hasattr(self, "folder_selector"):
            self.folder_selector["values"] = self.saved_folders

        if self.output_folder in self.saved_folders:
            if hasattr(self, "folder_var"):
                self.folder_var.set(self.output_folder)
            output_text = self.output_folder
        else:
            if hasattr(self, "folder_var"):
                self.folder_var.set("")
            output_text = "(no seleccionado)"

        if hasattr(self, "output_label"):
            self.output_label.config(text=f"Destino actual: {output_text}")

        self.update_summary()
        self.update_flow_preview()

    def set_output_folder(self, folder, *, save=True):
        self.output_folder = folder if folder in self.saved_folders else ""
        self.refresh_folder_selector()
        if save:
            self.save_config()

    def choose_folder(self, title, initialdir=""):
        return filedialog.askdirectory(title=title, initialdir=initialdir or "")




    def add_output_folder(self):
        selected = self.choose_folder("Selecciona una nueva carpeta destino", self.output_folder)
        if not selected:
            return

        if selected in self.saved_folders:
            self.set_output_folder(selected)
            self.log(f"[INFO] La carpeta ya estaba guardada y fue seleccionada: {selected}")
            return

        self.saved_folders.append(selected)
        self.set_output_folder(selected)
        self.log(f"[INFO] Carpeta destino agregada: {selected}")

    def edit_output_folder(self):
        if not self.output_folder:
            messagebox.showwarning("Aviso", "Primero selecciona una carpeta guardada para cambiarla.")
            return

        previous_folder = self.output_folder
        selected = self.choose_folder("Selecciona la nueva carpeta destino", previous_folder)
        if not selected or selected == previous_folder:
            return

        index = self.saved_folders.index(previous_folder)
        if selected in self.saved_folders:
            self.saved_folders.pop(index)
            self.set_output_folder(selected)
            self.log(
                "[INFO] La carpeta fue cambiada a una ya existente; se elimino el duplicado anterior."
            )
            return

        self.saved_folders[index] = selected
        self.set_output_folder(selected)
        self.log(f"[INFO] Carpeta destino actualizada: {previous_folder} -> {selected}")

    def delete_output_folder(self):
        if not self.output_folder:
            messagebox.showwarning("Aviso", "No hay una carpeta seleccionada para borrar.")
            return

        folder_to_delete = self.output_folder
        confirmed = messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas borrar esta carpeta guardada?\n\n{folder_to_delete}",
        )
        if not confirmed:
            return

        self.saved_folders = [folder for folder in self.saved_folders if folder != folder_to_delete]
        next_folder = self.saved_folders[0] if self.saved_folders else ""
        self.set_output_folder(next_folder)
        self.log(f"[INFO] Carpeta destino eliminada: {folder_to_delete}")

    def on_folder_selected(self, _event=None):
        selected = self.folder_var.get().strip()
        if selected in self.saved_folders:
            self.set_output_folder(selected)
            self.log(f"[INFO] Carpeta destino seleccionada: {selected}")

    def ensure_output_folder(self):
        if self.output_folder and os.path.isdir(self.output_folder):
            return True

        selected = self.choose_folder("Selecciona la carpeta destino", self.output_folder)
        if not selected:
            self.log("[ABORTADO] No se selecciono carpeta destino.")
            return False

        if selected not in self.saved_folders:
            self.saved_folders.append(selected)
            self.log(f"[INFO] Carpeta destino agregada: {selected}")
        else:
            self.log(f"[INFO] Carpeta destino seleccionada: {selected}")

        self.set_output_folder(selected)
        return True

    def select_pdf(self):
        selected = filedialog.askopenfilenames(
            title="Selecciona uno o varios archivos PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if selected:
            self.pdf_paths = list(selected)
            self.pdf_path = self.pdf_paths[0]
            self.update_summary()
            self.update_flow_preview()
            if len(self.pdf_paths) == 1:
                self.log(f"[INFO] PDF seleccionado: {self.pdf_path}")
            else:
                self.log(f"[INFO] PDFs seleccionados: {len(self.pdf_paths)} archivos")

    def extract_text_from_pdf(self, pdf_path):
        return self.services.pdf.extract_text(pdf_path)

    def extract_ncf_and_razon_social(self, text):
        ncf, razon_social = self.services.pdf.extract_fields(text)
        return ncf or None, razon_social or None

    def sanitize_filename(self, value):
        clean = re.sub(r'[<>:"/\\|?*]', "_", value)
        clean = re.sub(r"\s+", " ", clean).strip(" .")
        return clean






    def build_proposal_name(self, variable_name, proposal_type="mensual"):
        if proposal_type == "renta":
            clean_variable = self.sanitize_filename(variable_name.upper())
            return f"PROPUESTA DE ASESORIA DE RENTA PARA {clean_variable}"
        return os.path.splitext(self.services.proposals.preview(variable_name, proposal_type))[0]

    def get_unique_target_path(self, folder, base_name):
        target_path = os.path.join(folder, base_name + ".pdf")
        if not os.path.exists(target_path):
            return target_path

        i = 1
        while True:
            candidate = os.path.join(folder, f"{base_name}_{i}.pdf")
            if not os.path.exists(candidate):
                return candidate
            i += 1


    def process_pdf(self):
        pdf_paths = [path for path in self.pdf_paths if path and os.path.isfile(path)]
        if not pdf_paths and self.pdf_path and os.path.isfile(self.pdf_path):
            pdf_paths = [self.pdf_path]

        if not pdf_paths:
            messagebox.showwarning("Aviso", "Primero selecciona uno o varios PDFs.")
            return

        total = len(pdf_paths)
        processed = 0
        skipped = 0
        target_folders = []

        self.processed_count = 0
        if hasattr(self, "counter_label"):
            self.counter_label.config(text=f"Procesados: 0 / {total}")
        self.update_progress(0, total)
        self.log(f"[INFO] Iniciando procesamiento de {total} archivo(s)...")

        for index, pdf_path in enumerate(pdf_paths, start=1):
            file_name = os.path.basename(pdf_path)
            if hasattr(self, "current_file_label"):
                self.current_file_label.config(text=f"Archivo actual: {file_name}")
            self.root.update_idletasks()

            try:
                text = self.extract_text_from_pdf(pdf_path)
                ncf, razon_social = self.extract_ncf_and_razon_social(text)
                company_route = self.find_company_route_for_text(text)

                if not ncf or not razon_social:
                    skipped += 1
                    self.log(f"[OMITIDO] {file_name}: faltan NCF y/o Razon Social Cliente.")
                    continue

                if not company_route:
                    skipped += 1
                    self.log(f"[OMITIDO] {file_name}: no coincide con ninguna empresa configurada.")
                    continue

                target_folder = company_route.get("folder", "").strip()
                if not target_folder:
                    skipped += 1
                    self.log(f"[OMITIDO] {file_name}: {company_route.get('company', '')} no tiene ruta configurada.")
                    continue

                os.makedirs(target_folder, exist_ok=True)
                base_name = self.sanitize_filename(f"{ncf}_{razon_social}")
                new_path = self.get_unique_target_path(target_folder, base_name)
                os.replace(pdf_path, new_path)

                processed += 1
                self.processed_count = processed
                self.output_folder = target_folder
                if target_folder not in target_folders:
                    target_folders.append(target_folder)
                self.log(f"[OK] {file_name} -> {company_route.get('company', '')} / {os.path.basename(new_path)}")

            except Exception as e:
                skipped += 1
                self.log(f"[ERROR] {file_name}: no se pudo leer/procesar. Detalle: {e}")

            if hasattr(self, "counter_label"):
                self.counter_label.config(text=f"Procesados: {processed} / {total}")
            self.update_progress(index, total)

        if hasattr(self, "current_file_label"):
            self.current_file_label.config(text="Archivo actual: -")

        self.pdf_paths = []
        self.pdf_path = ""
        self.save_config()
        self.update_summary()
        self.update_flow_preview()
        self.root.update_idletasks()

        self.log(f"[INFO] Proceso finalizado. Procesados: {processed}. Omitidos: {skipped}.")
        if processed == 0:
            messagebox.showwarning(
                "Sin archivos procesados",
                "No se pudo procesar ninguna factura. Revisa el log para ver los motivos.",
            )
            return

        open_folder = messagebox.askyesno(
            "Completado",
            f"Procesados: {processed}\nOmitidos: {skipped}\n\nDeseas abrir una carpeta destino?",
        )
        if open_folder:
            folder_to_open = target_folders[0] if target_folders else self.output_folder
            try:
                os.startfile(folder_to_open)
                self.log(f"[INFO] Carpeta abierta: {folder_to_open}")
            except Exception as e:
                self.log(f"[ERROR] No se pudo abrir la carpeta destino. Detalle: {e}")
                messagebox.showerror(
                    "Error",
                    f"No se pudo abrir la carpeta destino.\n\nDetalle: {e}",
                )

    def set_copy_source_pdf(self, pdf_path, *, save=True):
        self.copy_source_pdf = pdf_path if pdf_path and os.path.isfile(pdf_path) else ""
        self.update_copy_summary()
        if save:
            self.save_config()












    def choose_pdf_file(self, title, initialdir=""):
        return filedialog.askopenfilename(
            title=title,
            initialdir=initialdir or "",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

    def select_copy_source_pdf(self):
        initial_dir = os.path.dirname(self.copy_source_pdf) if self.copy_source_pdf else ""
        selected = self.choose_pdf_file("Selecciona el PDF base", initial_dir)
        if not selected:
            return

        self.set_copy_source_pdf(selected)
        self.copy_log(f"[INFO] PDF base guardado: {selected}")

    def change_copy_source_pdf(self):
        if not self.copy_source_pdf:
            messagebox.showwarning("Aviso", "Primero selecciona un PDF base.")
            return

        initial_dir = os.path.dirname(self.copy_source_pdf)
        selected = self.choose_pdf_file("Selecciona el nuevo PDF base", initial_dir)
        if not selected or selected == self.copy_source_pdf:
            return

        previous = self.copy_source_pdf
        self.set_copy_source_pdf(selected)
        self.copy_log(f"[INFO] PDF base actualizado: {previous} -> {selected}")

    def clear_copy_source_pdf(self):
        if not self.copy_source_pdf:
            messagebox.showwarning("Aviso", "No hay un PDF base guardado para borrar.")
            return

        confirmed = messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas borrar la ruta guardada?\n\n{self.copy_source_pdf}",
        )
        if not confirmed:
            return

        previous = self.copy_source_pdf
        self.set_copy_source_pdf("")
        self.copy_log(f"[INFO] Ruta de PDF base eliminada: {previous}")

    def ensure_copy_source_pdf(self):
        if self.copy_source_pdf and os.path.isfile(self.copy_source_pdf):
            return True

        selected = self.choose_pdf_file("Selecciona el PDF base")
        if not selected:
            self.copy_log("[ABORTADO] No se seleccionó un PDF base.")
            return False

        self.set_copy_source_pdf(selected)
        self.copy_log(f"[INFO] PDF base guardado: {selected}")
        return True

    def create_proposal_copy(self):
        variable_name = self.copy_name_var.get().strip()
        proposal_type = self.copy_proposal_type_var.get().strip() or "mensual"
        if not variable_name:
            messagebox.showwarning("Aviso", "Escribe el nombre variable para crear la copia.")
            return

        if not self.ensure_copy_source_pdf():
            messagebox.showwarning("Aviso", "Debes seleccionar un PDF base para continuar.")
            return

        try:
            result = self.services.proposals.create(self.copy_source_pdf, variable_name, proposal_type)
            source_folder = os.path.dirname(result["target"])
            target_path = result["target"]
            self.copy_log(
                f"[OK] {os.path.basename(self.copy_source_pdf)} -> {os.path.basename(target_path)}"
            )
        except Exception as e:
            self.copy_log(f"[ERROR] No se pudo crear la copia. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo crear la copia del PDF.\n\nDetalle: {e}")
            return

        messagebox.showinfo(
            "Copia creada",
            f"Se creó la copia:\n\n{os.path.basename(target_path)}\n\nCarpeta:\n{source_folder}",
        )

        try:
            os.startfile(source_folder)
            self.copy_log(f"[INFO] Carpeta abierta: {source_folder}")
        except Exception as e:
            self.copy_log(f"[ERROR] No se pudo abrir la carpeta. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta.\n\nDetalle: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PdfRenamerApp(root)
    root.mainloop()


