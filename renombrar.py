# pip install PyPDF2

import calendar
import json
import os
import random
import re
import shutil
import sqlite3
import tempfile
import time
import textwrap
import tkinter as tk
import unicodedata
import uuid
from copy import copy
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from PyPDF2 import PdfReader

try:
    import winsound
except ImportError:
    winsound = None

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None


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
        self.organizer_folder = ""
        self.organizer_scan_results = []
        self.template_workbook_path = ""
        self.template_sheet_password_var = tk.StringVar()
        self.template_date_var = tk.StringVar(value=date.today().isoformat())
        self.template_date_picker_window = None
        self.template_date_picker_month = date.today().month
        self.template_date_picker_year = date.today().year
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
        self.statement_year_var = tk.StringVar(value=str(date.today().year))
        self.statement_date_var = tk.StringVar(value=date.today().isoformat())
        self.statement_client_var = tk.StringVar()
        self.statement_entity_type_var = tk.StringVar(value="juridica")
        self.statement_target_var = tk.StringVar(value="balance_general")
        self.statement_account_var = tk.StringVar()
        self.task_title_var = tk.StringVar()
        self.task_client_var = tk.StringVar()
        self.task_due_date_var = tk.StringVar(value=date.today().isoformat())
        self.task_due_time_var = tk.StringVar()
        self.task_urgency_var = tk.StringVar(value="amarillo")
        self.task_recurrence_var = tk.StringVar(value="none")
        self.task_client_search_var = tk.StringVar()
        self.task_show_completed_var = tk.BooleanVar(value=True)
        self.quick_client_name_var = tk.StringVar()
        self.quick_client_rnc_var = tk.StringVar()
        self.quick_client_location_var = tk.StringVar()
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
        self.excel_test_path_var = tk.StringVar()
        self.excel_test_start_row_var = tk.StringVar(value="2")
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
        self.client_default_base_folder = r"C:\Users\kalil\OneDrive\Documentos\igualas"
        self.processed_count = 0
        self.clients = []
        self.tasks = []
        self.pomodoro_tasks = []
        self.pomodoro_flows = []
        self.fiscal_versions = []
        self.fiscal_buyers = []
        self.message_fiscal_buyer_map = {}
        self.excel_test_clients = []
        self.selected_fiscal_buyer_id = None
        self.selected_client_id = None
        self.selected_task_id = None
        self.client_extra_visible = False
        self.statement_id = None
        self.statement_client_map = {}
        self.statement_account_map = {}
        self.task_client_map = {}
        self.task_client_selector_values = []
        self.task_list_ids = []
        self.statement_value_vars = {}
        self.statement_total_labels = {}
        self.statement_direct_amounts = {}
        self.statement_selected_account_ids = set()
        self.statement_layout_loaded = None
        self.statement_screen_mode = "editor"
        self.statement_defaults_entity_var = tk.StringVar(value="juridica")
        self.statement_defaults_root_var = tk.StringVar()
        self.statement_defaults_root_map = {}
        self.statement_defaults_subaccount_var = tk.StringVar()
        self.statement_defaults_subaccount_map = {}
        self.statement_defaults_available_search_var = tk.StringVar()
        self.statement_defaults_selected_search_var = tk.StringVar()
        self.statement_defaults_available_map = {}
        self.statement_defaults_selected_map = {}
        self.statement_history_map = {}
        self.statement_preview_window = None
        self.task_date_picker_window = None
        self.task_date_picker_month = date.today().month
        self.task_date_picker_year = date.today().year
        self.notebook = None
        self.tab_frames = {}
        self.home_icon_images = {}
        self.template_target_sheets = [
            "607",
            "IT-1",
            "MENU",
            "IR-2",
            "ANEXO B",
            "ANEXO A (IR-1)",
            "D",
            "IR-1",
            "ANTICIPOS IR-1",
            "ANTICIPOS IR-2",
            "B-1",
            "A-1",
            "ACTIVO",
            "RESIDUOS",
            "D-1",
            "E",
            "D-2",
            "606",
            "CLIENTES",
            "ANEXO A",
            "RESUMEN",
            "",
            "IMPUESTOS",
        ]

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
            "task_green": "#2e8b57",
            "task_yellow": "#e0a21a",
            "task_red": "#d65245",
            "task_overdue": "#7d2c27",
        }

        # Ejemplo valido: E310000000001
        self.ncf_pattern = re.compile(r"\b[A-Z]\d{12}\b")

        # Ejemplo esperado en PDF: Razon Social Cliente: 40225661210 kalil
        self.razon_social_pattern = re.compile(
            r"R[aá]z[oó]n\s+Social\s+Cliente\s*[:\-]?\s*(.+)",
            re.IGNORECASE,
        )

        self.organizer_name_pattern = re.compile(
            r"^(?P<company>.+?)\s+(?P<month>ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+(?P<day>\d{1,2})$",
            re.IGNORECASE,
        )
        self.organizer_supported_extensions = {".pdf", ".jpg", ".jpeg"}
        self.organizer_month_map = {
            "ene": 1,
            "feb": 2,
            "mar": 3,
            "abr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "ago": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dic": 12,
        }

        self.init_database()
        self.load_config()
        self.load_tasks_from_db()
        self.load_pomodoro_tasks_from_db()
        self.load_pomodoro_flows_from_db()
        self.load_fiscal_versions_from_db()
        self.load_fiscal_buyers_from_db()
        self.template_date_var.trace_add("write", self._on_template_date_change)
        self.template_sheet_password_var.trace_add("write", self._on_template_password_change)
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

        excel_test_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=0)
        excel_test_tab.grid_rowconfigure(1, weight=1)
        excel_test_tab.grid_columnconfigure(0, weight=1)
        self.notebook.add(excel_test_tab, text="Prueba Excel")
        self.tab_frames["excel_test"] = excel_test_tab

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
        self._build_excel_test_tab(excel_test_tab)
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
            ("Prueba Excel", "Carga temporalmente RNC y clientes desde un libro para revisar los datos.", "excel_test"),
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
            with self.get_db_connection() as conn:
                flow_rows = conn.execute(
                    "SELECT id, name FROM pomodoro_flows ORDER BY created_at"
                ).fetchall()
                task_rows = conn.execute(
                    """
                    SELECT ft.flow_id, t.id, t.title, t.completed_pomodoros, ft.completed
                    FROM pomodoro_flow_tasks ft
                    JOIN pomodoro_tasks t ON t.id = ft.task_id
                    ORDER BY ft.created_at, t.created_at
                    """
                ).fetchall()
            tasks_by_flow = {}
            for row in task_rows:
                tasks_by_flow.setdefault(row["flow_id"], []).append(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "completed_pomodoros": int(row["completed_pomodoros"] or 0),
                        "completed": bool(row["completed"]),
                    }
                )
            self.pomodoro_flows = [
                {"id": row["id"], "name": row["name"], "tasks": tasks_by_flow.get(row["id"], [])}
                for row in flow_rows
            ]
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
        flow_id = str(uuid.uuid4())
        try:
            with self.get_db_connection() as conn:
                conn.execute("INSERT INTO pomodoro_flows (id, name) VALUES (?, ?)", (flow_id, name))
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"No se pudo crear el flujo.\n{exc}")
            return "break"
        self.pomodoro_flow_name_var.set("")
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.log(f"[INFO] Flujo de Pomodoro creado: {name}")
        return "break"

    def set_task_in_pomodoro_flow(self, flow_id, task_id, assigned):
        with self.get_db_connection() as conn:
            if assigned:
                conn.execute(
                    "INSERT OR IGNORE INTO pomodoro_flow_tasks (flow_id, task_id) VALUES (?, ?)",
                    (flow_id, task_id),
                )
            else:
                conn.execute(
                    "DELETE FROM pomodoro_flow_tasks WHERE flow_id = ? AND task_id = ?",
                    (flow_id, task_id),
                )
        self.load_pomodoro_flows_from_db()
        self.refresh_pomodoro_tasks_list()
        self.refresh_pomodoro_ui()

    def set_pomodoro_flow_task_completed(self, flow_id, task_id, completed):
        with self.get_db_connection() as conn:
            conn.execute(
                "UPDATE pomodoro_flow_tasks SET completed = ? WHERE flow_id = ? AND task_id = ?",
                (1 if completed else 0, flow_id, task_id),
            )
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
        with self.get_db_connection() as conn:
            conn.execute("DELETE FROM pomodoro_flows WHERE id = ?", (flow_id,))
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
            with self.get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, title, completed_pomodoros
                    FROM pomodoro_tasks
                    ORDER BY created_at
                    """
                ).fetchall()
            self.pomodoro_tasks = []
            for row in rows:
                normalized = self.normalize_pomodoro_task_record(dict(row))
                if normalized:
                    self.pomodoro_tasks.append(normalized)
        except Exception as exc:
            self.pomodoro_tasks = []
            self.log(f"[ERROR] No se pudieron cargar las tareas de Pomodoro. Detalle: {exc}")

    def save_pomodoro_task_to_db(self, payload):
        normalized = self.normalize_pomodoro_task_record(payload)
        if not normalized:
            return False

        try:
            with self.get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO pomodoro_tasks (id, title, completed_pomodoros)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        completed_pomodoros = excluded.completed_pomodoros,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (normalized["id"], normalized["title"], normalized["completed_pomodoros"]),
                )
            return True
        except sqlite3.Error as exc:
            self.log(f"[ERROR] No se pudo guardar la tarea de Pomodoro. Detalle: {exc}")
            return False

    def delete_pomodoro_task_from_db(self, task_id):
        with self.get_db_connection() as conn:
            conn.execute("DELETE FROM pomodoro_tasks WHERE id = ?", (task_id,))

    def increment_pomodoro_task_count_in_db(self, task_id):
        if not task_id:
            return
        with self.get_db_connection() as conn:
            conn.execute(
                """
                UPDATE pomodoro_tasks
                SET completed_pomodoros = completed_pomodoros + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (task_id,),
            )

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

    def _build_template_tab(self, parent):
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
            text="Plantilla Excel",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Selecciona un libro, indica la fecha y actualiza las hojas protegidas colocando la fecha en una celda aleatoria entre AM1, AN1, AM5 y AN5.",
            style="Body.TLabel",
            wraplength=540,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.template_book_summary = self._create_info_card(header, 0, 1, "Libro guardado", "Sin libro")
        self.template_date_summary = self._create_info_card(header, 0, 2, "Fecha activa", self.template_date_var.get())

        controls_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        controls_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        controls_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(controls_panel, text="Libro de Excel", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            controls_panel,
            text="La ruta del libro y la clave quedan guardadas para las siguientes veces. Puedes cambiarlas cuando quieras.",
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.template_book_label = ttk.Label(
            controls_panel,
            text="Libro actual: (no seleccionado)",
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        )
        self.template_book_label.grid(row=2, column=0, sticky="w", pady=(0, 12))

        book_actions = ttk.Frame(controls_panel, style="Card.TFrame")
        book_actions.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        book_actions.grid_columnconfigure(0, weight=1)
        book_actions.grid_columnconfigure(1, weight=1)
        book_actions.grid_columnconfigure(2, weight=1)

        ttk.Button(
            book_actions,
            text="Escoger libro",
            style="Secondary.TButton",
            command=self.select_template_workbook,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            book_actions,
            text="Cambiar libro",
            style="Secondary.TButton",
            command=self.change_template_workbook,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(
            book_actions,
            text="Abrir libro",
            style="Primary.TButton",
            command=self.open_template_workbook,
        ).grid(row=0, column=2, sticky="ew")

        ttk.Label(controls_panel, text="Fecha", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        date_row = ttk.Frame(controls_panel, style="Card.TFrame")
        date_row.grid(row=5, column=0, sticky="ew", pady=(6, 12))
        date_row.grid_columnconfigure(0, weight=1)
        self.template_date_entry = ttk.Entry(date_row, textvariable=self.template_date_var, font=("Segoe UI", 11))
        self.template_date_entry.grid(row=0, column=0, sticky="ew")
        self.template_date_entry.bind("<Button-1>", lambda _event: self.open_template_date_picker())
        ttk.Button(
            date_row,
            text="Elegir",
            style="Secondary.TButton",
            command=self.open_template_date_picker,
            width=10,
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        ttk.Label(
            controls_panel,
            text="Se usa la fecha de hoy automáticamente al abrir la app. Puedes elegir otra desde el calendario.",
            style="Body.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=6, column=0, sticky="w", pady=(0, 14))

        ttk.Label(controls_panel, text="Clave para desbloquear/proteger hojas", style="Body.TLabel").grid(row=7, column=0, sticky="w")
        self.template_password_entry = ttk.Entry(
            controls_panel,
            textvariable=self.template_sheet_password_var,
            show="*",
            font=("Segoe UI", 11),
        )
        self.template_password_entry.grid(row=8, column=0, sticky="ew", pady=(6, 18))

        ttk.Button(
            controls_panel,
            text="Colocar fecha en plantilla",
            style="Primary.TButton",
            command=self.apply_date_to_template_workbook,
        ).grid(row=9, column=0, sticky="ew")

        preview_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        preview_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(3, weight=1)

        ttk.Label(preview_panel, text="Hojas objetivo", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            preview_panel,
            text=f"Se procesan {len(self.template_target_sheets)} hojas. En cada una se limpia la zona objetivo y se coloca la fecha en una celda aleatoria entre AM1, AN1, AM5 y AN5.",
            style="Body.TLabel",
            wraplength=430,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        ttk.Label(
            preview_panel,
            text=", ".join(self.template_target_sheets),
            style="CardValue.TLabel",
            wraplength=430,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 16))

        template_log_box = ttk.Frame(preview_panel, style="AltCard.TFrame", padding=16)
        template_log_box.grid(row=3, column=0, sticky="nsew")
        template_log_box.grid_rowconfigure(0, weight=1)
        template_log_box.grid_columnconfigure(0, weight=1)

        self.template_log_text = ScrolledText(
            template_log_box,
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
        self.template_log_text.grid(row=0, column=0, sticky="nsew")
        self.template_log_text.configure(state="disabled")

        self.update_template_summary()

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

    def _build_organizer_tab(self, parent):
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
            text="Organizador por día",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Analiza una carpeta con PDFs o JPGs y los renombra como DD empresa para mantenerlos ordenados.",
            style="Body.TLabel",
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.organizer_folder_summary = self._create_info_card(header, 0, 1, "Carpeta activa", "Sin carpeta")
        self.organizer_count_summary = self._create_info_card(header, 0, 2, "Archivos válidos", "0")

        controls_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        controls_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        controls_panel.grid_columnconfigure(0, weight=1)
        controls_panel.grid_rowconfigure(4, weight=1)

        ttk.Label(controls_panel, text="Carpeta origen", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            controls_panel,
            text="Se revisan solo archivos de la carpeta elegida, sin tocar subcarpetas.",
            style="Body.TLabel",
            wraplength=440,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.organizer_folder_label = ttk.Label(
            controls_panel,
            text="Carpeta actual: (sin carpeta)",
            style="CardValue.TLabel",
            wraplength=440,
            justify="left",
        )
        self.organizer_folder_label.grid(row=2, column=0, sticky="w", pady=(0, 14))

        organizer_actions = ttk.Frame(controls_panel, style="Card.TFrame")
        organizer_actions.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        organizer_actions.grid_columnconfigure(0, weight=1)
        organizer_actions.grid_columnconfigure(1, weight=1)
        organizer_actions.grid_columnconfigure(2, weight=1)

        ttk.Button(
            organizer_actions,
            text="Elegir carpeta",
            style="Secondary.TButton",
            command=self.select_organizer_folder,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            organizer_actions,
            text="Analizar carpeta",
            style="Secondary.TButton",
            command=self.scan_organizer_folder,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(
            organizer_actions,
            text="Renombrar archivos",
            style="Primary.TButton",
            command=self.apply_organizer_renames,
        ).grid(row=0, column=2, sticky="ew")

        organizer_log_box = ttk.Frame(controls_panel, style="AltCard.TFrame", padding=16)
        organizer_log_box.grid(row=4, column=0, sticky="nsew")
        organizer_log_box.grid_rowconfigure(0, weight=1)
        organizer_log_box.grid_columnconfigure(0, weight=1)

        self.organizer_log_text = ScrolledText(
            organizer_log_box,
            wrap=tk.WORD,
            height=16,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.organizer_log_text.grid(row=0, column=0, sticky="nsew")
        self.organizer_log_text.configure(state="disabled")

        preview_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        preview_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(1, weight=1)

        ttk.Label(preview_panel, text="Vista previa", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        columns = ("actual", "dia", "nuevo", "estado")
        self.organizer_tree = ttk.Treeview(
            preview_panel,
            columns=columns,
            show="headings",
            height=18,
        )
        self.organizer_tree.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.organizer_tree.heading("actual", text="Nombre actual")
        self.organizer_tree.heading("dia", text="Día")
        self.organizer_tree.heading("nuevo", text="Nombre nuevo")
        self.organizer_tree.heading("estado", text="Estado")
        self.organizer_tree.column("actual", width=230, anchor="w")
        self.organizer_tree.column("dia", width=60, anchor="center")
        self.organizer_tree.column("nuevo", width=230, anchor="w")
        self.organizer_tree.column("estado", width=120, anchor="center")

        organizer_scrollbar = ttk.Scrollbar(preview_panel, orient="vertical", command=self.organizer_tree.yview)
        organizer_scrollbar.grid(row=1, column=1, sticky="ns", pady=(12, 0))
        self.organizer_tree.configure(yscrollcommand=organizer_scrollbar.set)

        self.update_organizer_summary()

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

    def _build_excel_test_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")
        ttk.Label(title_block, text="Prueba Excel", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Lee RNC desde la columna B y clientes desde la columna C sin guardar en base de datos.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.excel_test_total_summary = self._create_info_card(header, 0, 1, "Clientes leidos", "0")

        content = ttk.Frame(parent, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        controls = ttk.Frame(content, style="Card.TFrame", padding=18)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(1, weight=1)

        ttk.Label(controls, text="Archivo Excel", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            controls,
            textvariable=self.excel_test_path_var,
            font=("Segoe UI", 10),
            state="readonly",
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 12), padx=(0, 10))

        ttk.Button(
            controls,
            text="Seleccionar Excel",
            style="Primary.TButton",
            command=self.select_excel_test_workbook,
        ).grid(row=1, column=3, sticky="ew", pady=(6, 12))

        ttk.Label(controls, text="Fila inicial", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Spinbox(
            controls,
            from_=1,
            to=99999,
            textvariable=self.excel_test_start_row_var,
            width=8,
        ).grid(row=3, column=0, sticky="w", pady=(6, 0), padx=(0, 12))

        ttk.Button(
            controls,
            text="Leer datos",
            style="Secondary.TButton",
            command=self.load_excel_test_clients,
        ).grid(row=3, column=1, sticky="w", pady=(6, 0))
        ttk.Button(
            controls,
            text="Limpiar prueba",
            style="Danger.TButton",
            command=self.clear_excel_test_clients,
        ).grid(row=3, column=2, sticky="w", pady=(6, 0), padx=(10, 0))

        self.excel_test_status_label = ttk.Label(
            controls,
            text="Sin archivo seleccionado.",
            style="Body.TLabel",
            wraplength=760,
            justify="left",
        )
        self.excel_test_status_label.grid(row=4, column=0, columnspan=4, sticky="w", pady=(12, 0))

        table_panel = ttk.Frame(content, style="Card.TFrame", padding=18)
        table_panel.grid(row=1, column=0, sticky="nsew")
        table_panel.grid_rowconfigure(1, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(table_panel, text="Clientes cargados para prueba", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.excel_test_tree = ttk.Treeview(
            table_panel,
            columns=("fila", "rnc", "cliente"),
            show="headings",
            height=14,
        )
        self.excel_test_tree.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.excel_test_tree.heading("fila", text="Fila")
        self.excel_test_tree.heading("rnc", text="RNC")
        self.excel_test_tree.heading("cliente", text="Cliente")
        self.excel_test_tree.column("fila", width=80, anchor="center", stretch=False)
        self.excel_test_tree.column("rnc", width=180, anchor="w")
        self.excel_test_tree.column("cliente", width=420, anchor="w")

        scrollbar = ttk.Scrollbar(table_panel, orient="vertical", command=self.excel_test_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(12, 0))
        self.excel_test_tree.configure(yscrollcommand=scrollbar.set)

    def select_excel_test_workbook(self):
        initial_dir = os.path.dirname(self.excel_test_path_var.get().strip())
        selected = self.choose_excel_file("Selecciona el Excel de clientes", initial_dir)
        if not selected:
            return

        self.excel_test_path_var.set(selected)
        self.load_excel_test_clients()

    def get_excel_test_start_row(self):
        try:
            start_row = int(self.excel_test_start_row_var.get().strip())
        except ValueError:
            start_row = 2
        return max(1, start_row)

    def load_excel_test_clients(self):
        workbook_path = self.excel_test_path_var.get().strip()
        if not workbook_path:
            messagebox.showwarning("Aviso", "Primero selecciona un archivo de Excel.")
            return
        if not os.path.isfile(workbook_path):
            messagebox.showwarning("Aviso", "El archivo seleccionado no existe.")
            return
        if load_workbook is None:
            messagebox.showerror("Error", "openpyxl no esta instalado en este equipo.")
            return

        extension = os.path.splitext(workbook_path)[1].lower()
        if extension not in {".xlsx", ".xlsm"}:
            messagebox.showwarning("Aviso", "Esta prueba admite archivos .xlsx o .xlsm.")
            return

        start_row = self.get_excel_test_start_row()
        keep_vba = extension == ".xlsm"

        try:
            workbook = load_workbook(workbook_path, read_only=True, data_only=True, keep_vba=keep_vba)
            try:
                sheet = workbook.active
                loaded_clients = []
                for row_number in range(start_row, sheet.max_row + 1):
                    rnc = self.normalize_excel_cell_value(sheet.cell(row=row_number, column=2).value)
                    client_name = self.normalize_excel_cell_value(sheet.cell(row=row_number, column=3).value)
                    if not rnc and not client_name:
                        continue
                    loaded_clients.append(
                        {
                            "id": f"excel-test-{row_number}",
                            "row": row_number,
                            "rnc": rnc,
                            "name": client_name or "Sin nombre",
                            "pc_location": "",
                            "cedula": "",
                            "tss_class": "",
                            "resource_path": "",
                            "work_description": "Carga temporal desde Excel",
                        }
                    )
            finally:
                workbook.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo de Excel.\n\nDetalle: {e}")
            return

        self.excel_test_clients = loaded_clients
        self.refresh_excel_test_clients()
        file_name = os.path.basename(workbook_path)
        self.excel_test_status_label.config(
            text=f"{file_name}: {len(loaded_clients)} cliente(s) leidos desde la fila {start_row}."
        )

    def normalize_excel_cell_value(self, value):
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value)).strip()
        return str(value).strip()

    def refresh_excel_test_clients(self):
        if hasattr(self, "excel_test_total_summary"):
            self.excel_test_total_summary.config(text=str(len(self.excel_test_clients)))
        if not hasattr(self, "excel_test_tree"):
            return

        for item_id in self.excel_test_tree.get_children():
            self.excel_test_tree.delete(item_id)

        for client in self.excel_test_clients:
            self.excel_test_tree.insert(
                "",
                tk.END,
                values=(client.get("row", ""), client.get("rnc", ""), client.get("name", "")),
            )

    def clear_excel_test_clients(self):
        self.excel_test_clients = []
        self.refresh_excel_test_clients()
        if hasattr(self, "excel_test_status_label"):
            self.excel_test_status_label.config(text="Prueba limpiada. No se guardo nada en base de datos.")

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
        active_tasks = [task for task in self.tasks if task.get("status") == "pending"]
        today_iso = date.today().isoformat()
        due_today = sum(1 for task in active_tasks if task.get("due_date") == today_iso)
        red_count = sum(1 for task in active_tasks if task.get("urgency") == "rojo")

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
        if hasattr(self, "home_tasks_summary"):
            self.home_tasks_summary.config(text=str(len(active_tasks)))
        if hasattr(self, "home_clients_summary"):
            self.home_clients_summary.config(text=str(len(self.clients)))
        if hasattr(self, "home_due_today_summary"):
            self.home_due_today_summary.config(text=str(due_today))
        if hasattr(self, "home_red_tasks_summary"):
            self.home_red_tasks_summary.config(text=str(red_count))

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

    def organizer_log(self, message):
        if not hasattr(self, "organizer_log_text"):
            return
        self.organizer_log_text.configure(state="normal")
        self.organizer_log_text.insert(tk.END, message + "\n")
        self.organizer_log_text.see(tk.END)
        self.organizer_log_text.configure(state="disabled")

    def template_log(self, message):
        if not hasattr(self, "template_log_text"):
            return
        self.template_log_text.configure(state="normal")
        self.template_log_text.insert(tk.END, message + "\n")
        self.template_log_text.see(tk.END)
        self.template_log_text.configure(state="disabled")

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

    def update_organizer_summary(self):
        folder_value = self.organizer_folder if self.organizer_folder else "(sin carpeta)"
        valid_count = sum(1 for item in self.organizer_scan_results if item.get("is_valid"))
        if hasattr(self, "organizer_folder_summary"):
            self.organizer_folder_summary.config(text=self._truncate_middle(folder_value, 36))
        if hasattr(self, "organizer_count_summary"):
            self.organizer_count_summary.config(text=str(valid_count))
        if hasattr(self, "organizer_folder_label"):
            self.organizer_folder_label.config(text=f"Carpeta actual: {folder_value}")

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

    def refresh_organizer_tree(self):
        if not hasattr(self, "organizer_tree"):
            return

        for item_id in self.organizer_tree.get_children():
            self.organizer_tree.delete(item_id)

        for item in self.organizer_scan_results:
            day_value = f"{item['day']:02d}" if item.get("day") is not None else "-"
            new_name = item.get("target_name") or "-"
            self.organizer_tree.insert(
                "",
                tk.END,
                values=(item["current_name"], day_value, new_name, item["status"]),
            )

        self.update_organizer_summary()

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
        self.refresh_states_client_selector()
        self.refresh_statement_history()

    def refresh_clients_summary(self):
        if hasattr(self, "clients_total_summary"):
            self.clients_total_summary.config(text=str(len(self.clients)))
        self.update_home_dashboard()

    def _build_tasks_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=2)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")
        ttk.Label(title_block, text="Tareas", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Administra pendientes por cliente con horario, urgencia y recurrencia.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.tasks_total_summary = self._create_info_card(header, 0, 1, "Activas", "0")
        self.tasks_due_today_summary = self._create_info_card(header, 0, 2, "Vencen hoy", "0")
        self.tasks_red_summary = self._create_info_card(header, 0, 3, "Urgentes rojas", "0")

        list_panel = ttk.Frame(parent, style="Card.TFrame", padding=18)
        list_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        list_panel.grid_rowconfigure(3, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)

        filter_row = ttk.Frame(list_panel, style="Card.TFrame")
        filter_row.grid(row=0, column=0, sticky="ew")
        filter_row.grid_columnconfigure(0, weight=1)
        filter_row.grid_columnconfigure(1, weight=0)
        ttk.Label(filter_row, text="Tareas", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(
            filter_row,
            text="Nueva tarea",
            style="Secondary.TButton",
            command=self.prepare_new_task,
        ).grid(row=0, column=1, sticky="e")
        ttk.Checkbutton(
            list_panel,
            text="Mostrar completadas",
            variable=self.task_show_completed_var,
            command=self.refresh_tasks_tree,
        ).grid(row=1, column=0, sticky="e", pady=(8, 0))

        ttk.Label(
            list_panel,
            text="Las tareas vencidas se muestran primero. Haz clic en una fila para editarla o completarla.",
            style="Body.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(6, 14))

        tree_container = ttk.Frame(list_panel, style="Card.TFrame")
        tree_container.grid(row=3, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.tasks_tree = ttk.Treeview(
            tree_container,
            columns=("tarea", "cliente", "fecha", "hora", "urgencia", "repite", "estado"),
            show="headings",
            selectmode="browse",
            height=16,
        )
        self.tasks_tree.grid(row=0, column=0, sticky="nsew")
        self.tasks_tree.heading("tarea", text="Tarea")
        self.tasks_tree.heading("cliente", text="Cliente")
        self.tasks_tree.heading("fecha", text="Fecha")
        self.tasks_tree.heading("hora", text="Hora")
        self.tasks_tree.heading("urgencia", text="Urgencia")
        self.tasks_tree.heading("repite", text="Repeticion")
        self.tasks_tree.heading("estado", text="Estado")
        self.tasks_tree.column("tarea", width=220, anchor="w")
        self.tasks_tree.column("cliente", width=220, anchor="w")
        self.tasks_tree.column("fecha", width=120, anchor="center")
        self.tasks_tree.column("hora", width=90, anchor="center")
        self.tasks_tree.column("urgencia", width=100, anchor="center")
        self.tasks_tree.column("repite", width=110, anchor="center")
        self.tasks_tree.column("estado", width=105, anchor="center")
        self.tasks_tree.bind("<<TreeviewSelect>>", self.on_task_tree_select)

        tasks_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tasks_tree.yview)
        tasks_scroll.grid(row=0, column=1, sticky="ns")
        self.tasks_tree.configure(yscrollcommand=tasks_scroll.set)

        detail_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        detail_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        detail_panel.grid_rowconfigure(1, weight=3)
        detail_panel.grid_rowconfigure(2, weight=2)
        detail_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(detail_panel, text="Detalle de tarea", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        form = ttk.Frame(detail_panel, style="Card.TFrame")
        form.grid(row=1, column=0, sticky="nsew", pady=(12, 18))
        form.grid_columnconfigure(0, weight=1)
        form.grid_rowconfigure(7, weight=1)

        ttk.Label(form, text="Cliente", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.task_client_selector = ttk.Combobox(form, textvariable=self.task_client_var, state="normal", style="Modern.TCombobox")
        self.task_client_selector.grid(row=1, column=0, sticky="ew", pady=(6, 12))
        self.task_client_selector.bind("<KeyRelease>", self.on_task_client_selector_search)
        self.task_client_selector.bind("<<ComboboxSelected>>", self.on_task_client_selector_selected)
        self.task_client_selector.bind("<FocusOut>", self.on_task_client_selector_focus_out)

        ttk.Label(form, text="Tarea", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        self.task_title_entry = ttk.Entry(form, textvariable=self.task_title_var, font=("Segoe UI", 11))
        self.task_title_entry.grid(row=3, column=0, sticky="ew", pady=(6, 12))

        schedule_row = ttk.Frame(form, style="Card.TFrame")
        schedule_row.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        schedule_row.grid_columnconfigure(0, weight=1)
        schedule_row.grid_columnconfigure(1, weight=0)
        schedule_row.grid_columnconfigure(2, weight=1)
        ttk.Label(schedule_row, text="Fecha", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(schedule_row, text="Hora", style="Body.TLabel").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.task_due_date_entry = ttk.Entry(schedule_row, textvariable=self.task_due_date_var, font=("Segoe UI", 11))
        self.task_due_date_entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(
            schedule_row,
            text="Elegir",
            style="Secondary.TButton",
            command=self.open_task_date_picker,
            width=10,
        ).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(6, 0))
        self.task_due_time_entry = ttk.Entry(schedule_row, textvariable=self.task_due_time_var, font=("Segoe UI", 11))
        self.task_due_time_entry.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(6, 0))

        options_row = ttk.Frame(form, style="Card.TFrame")
        options_row.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        options_row.grid_columnconfigure(0, weight=1)
        options_row.grid_columnconfigure(1, weight=1)
        ttk.Label(options_row, text="Urgencia", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(options_row, text="Repeticion", style="Body.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.task_urgency_selector = ttk.Combobox(
            options_row,
            textvariable=self.task_urgency_var,
            values=("verde", "amarillo", "rojo"),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.task_urgency_selector.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.task_recurrence_selector = ttk.Combobox(
            options_row,
            textvariable=self.task_recurrence_var,
            values=("none", "daily", "weekly", "monthly"),
            state="readonly",
            style="Modern.TCombobox",
        )
        self.task_recurrence_selector.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(6, 0))

        ttk.Label(form, text="Notas", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        self.task_notes_text = ScrolledText(
            form,
            wrap=tk.WORD,
            height=7,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
        )
        self.task_notes_text.grid(row=7, column=0, sticky="nsew", pady=(6, 12))

        urgency_guide = ttk.Frame(form, style="AltCard.TFrame", padding=12)
        urgency_guide.grid(row=8, column=0, sticky="ew")
        ttk.Label(
            urgency_guide,
            text="Verde: baja prioridad | Amarillo: media | Rojo: alta",
            style="Body.TLabel",
        ).grid(row=0, column=0, sticky="w")

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=9, column=0, sticky="ew", pady=(14, 0))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)
        buttons.grid_columnconfigure(2, weight=1)
        buttons.grid_columnconfigure(3, weight=1)
        ttk.Button(buttons, text="Nueva tarea", style="Secondary.TButton", command=self.prepare_new_task).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(buttons, text="Guardar", style="Primary.TButton", command=self.save_task).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.task_complete_button = ttk.Button(buttons, text="Completar", style="Secondary.TButton", command=self.complete_task)
        self.task_complete_button.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        self.task_delete_button = ttk.Button(buttons, text="Eliminar", style="Danger.TButton", command=self.delete_task)
        self.task_delete_button.grid(row=0, column=3, sticky="ew")

        self.task_detail_hint = ttk.Label(
            form,
            text="Crea una tarea nueva o selecciona una existente para editarla.",
            style="Body.TLabel",
            wraplength=360,
            justify="left",
        )
        self.task_detail_hint.grid(row=10, column=0, sticky="w", pady=(14, 0))

        clients_panel = ttk.Frame(detail_panel, style="AltCard.TFrame", padding=18)
        clients_panel.grid(row=2, column=0, sticky="nsew")
        clients_panel.grid_rowconfigure(3, weight=1)
        clients_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(clients_panel, text="Clientes en tareas", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            clients_panel,
            text="Puedes vincular tareas a clientes existentes o crear uno rapido desde aqui.",
            style="Body.TLabel",
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        search_row = ttk.Frame(clients_panel, style="AltCard.TFrame")
        search_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        search_row.grid_columnconfigure(0, weight=1)
        self.task_client_search_entry = ttk.Entry(search_row, textvariable=self.task_client_search_var, font=("Segoe UI", 10))
        self.task_client_search_entry.grid(row=0, column=0, sticky="ew")

        self.task_client_listbox = tk.Listbox(
            clients_panel,
            exportselection=False,
            height=6,
            font=("Segoe UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.task_client_listbox.grid(row=3, column=0, sticky="nsew")
        self.task_client_listbox.bind("<<ListboxSelect>>", self.on_task_client_pick)

        quick_client = ttk.Frame(clients_panel, style="AltCard.TFrame")
        quick_client.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        quick_client.grid_columnconfigure(0, weight=1)
        ttk.Label(quick_client, text="Alta rapida de cliente", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(quick_client, text="Nombre", style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(quick_client, textvariable=self.quick_client_name_var, font=("Segoe UI", 10)).grid(row=2, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(quick_client, text="RNC", style="Body.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(quick_client, textvariable=self.quick_client_rnc_var, font=("Segoe UI", 10)).grid(row=4, column=0, sticky="ew", pady=(4, 8))

        quick_location = ttk.Frame(quick_client, style="AltCard.TFrame")
        quick_location.grid(row=6, column=0, sticky="ew", pady=(4, 8))
        quick_location.grid_columnconfigure(0, weight=1)
        ttk.Label(quick_client, text="Ubicacion en PC", style="Body.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(quick_location, textvariable=self.quick_client_location_var, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(quick_location, text="Carpeta", style="Secondary.TButton", command=self.select_quick_client_location).grid(row=0, column=1)
        ttk.Button(
            quick_client,
            text="Guardar cliente rapido",
            style="Secondary.TButton",
            command=self.save_quick_client,
        ).grid(row=7, column=0, sticky="ew")

        self.task_client_search_var.trace_add("write", self._on_task_client_search_change)
        self.prepare_new_task()
        self.refresh_tasks_ui()

    def _on_task_client_search_change(self, *_args):
        self.refresh_task_client_list()

    def refresh_tasks_ui(self):
        self.refresh_tasks_summary()
        self.refresh_task_client_selector()
        self.refresh_tasks_tree()
        self.refresh_task_client_list()
        self.update_task_action_buttons()

    def refresh_tasks_summary(self):
        active_tasks = [task for task in self.tasks if task.get("status") == "pending"]
        today_iso = date.today().isoformat()
        due_today = sum(1 for task in active_tasks if task.get("due_date") == today_iso)
        red_count = sum(1 for task in active_tasks if task.get("urgency") == "rojo")
        if hasattr(self, "tasks_total_summary"):
            self.tasks_total_summary.config(text=str(len(active_tasks)))
        if hasattr(self, "tasks_due_today_summary"):
            self.tasks_due_today_summary.config(text=str(due_today))
        if hasattr(self, "tasks_red_summary"):
            self.tasks_red_summary.config(text=str(red_count))
        self.update_home_dashboard()

    def refresh_task_client_selector(self):
        if not hasattr(self, "task_client_selector"):
            return

        self.task_client_map = {"Sin cliente": None}
        values = ["Sin cliente"]
        seen = set(values)
        for client in self.clients:
            label = client.get("name", "Sin nombre").strip() or "Sin nombre"
            rnc = client.get("rnc", "").strip()
            if rnc:
                label = f"{label} ({rnc})"
            if label in seen:
                label = f"{label} [{client.get('id', '')[:6]}]"
            seen.add(label)
            values.append(label)
            self.task_client_map[label] = client.get("id")

        self.task_client_selector_values = values
        self.task_client_selector["values"] = values
        if self.task_client_var.get() not in values:
            self.task_client_var.set("Sin cliente")

    def filter_task_client_selector_values(self, raw_query):
        query = raw_query.strip().lower()
        if not query:
            return list(self.task_client_selector_values)

        matches = ["Sin cliente"] if "sin cliente".startswith(query) else []
        for label in self.task_client_selector_values:
            if label == "Sin cliente":
                continue
            if query in label.lower():
                matches.append(label)
        return matches or list(self.task_client_selector_values)

    def on_task_client_selector_search(self, _event=None):
        if not hasattr(self, "task_client_selector"):
            return
        self.task_client_selector["values"] = self.filter_task_client_selector_values(self.task_client_var.get())

    def on_task_client_selector_selected(self, _event=None):
        if hasattr(self, "task_client_selector"):
            self.task_client_selector["values"] = list(self.task_client_selector_values)

    def on_task_client_selector_focus_out(self, _event=None):
        self.resolve_task_client_selection(silent=True)
        if hasattr(self, "task_client_selector"):
            self.task_client_selector["values"] = list(self.task_client_selector_values)

    def resolve_task_client_selection(self, silent=False):
        raw_value = self.task_client_var.get().strip()
        if not raw_value or raw_value == "Sin cliente":
            self.task_client_var.set("Sin cliente")
            return True, None

        exact_client_id = self.task_client_map.get(raw_value)
        if exact_client_id is not None or raw_value in self.task_client_map:
            return True, exact_client_id

        query = raw_value.lower()
        matches = []
        for label in self.task_client_selector_values:
            if label == "Sin cliente":
                continue
            if query in label.lower():
                matches.append(label)

        if len(matches) == 1:
            selected_label = matches[0]
            self.task_client_var.set(selected_label)
            return True, self.task_client_map.get(selected_label)

        if not silent:
            if matches:
                messagebox.showwarning("Aviso", "Hay varios clientes que coinciden. Escribe un poco mas o selecciona uno exacto.")
            else:
                messagebox.showwarning("Aviso", "No se encontro un cliente con ese nombre. Puedes dejarlo como 'Sin cliente'.")
        return False, None

    def refresh_task_client_list(self):
        if not hasattr(self, "task_client_listbox"):
            return

        selected_search = self.task_client_search_var.get().strip().lower()
        self.task_client_listbox.delete(0, tk.END)
        self.task_client_list_ids = []

        for client in self.clients:
            name = client.get("name", "").strip()
            rnc = client.get("rnc", "").strip()
            label = name or "Sin nombre"
            if rnc:
                label = f"{label} - {rnc}"
            haystack = f"{name} {rnc} {client.get('pc_location', '')}".lower()
            if selected_search and selected_search not in haystack:
                continue
            self.task_client_listbox.insert(tk.END, label)
            self.task_client_list_ids.append(client.get("id"))

        if not self.task_client_list_ids:
            self.task_client_listbox.insert(tk.END, "No hay clientes para mostrar.")

    def on_task_client_pick(self, _event=None):
        if not hasattr(self, "task_client_listbox"):
            return
        selection = self.task_client_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.task_client_list_ids):
            return
        client = self.find_client_by_id(self.task_client_list_ids[index])
        if client:
            self.task_client_var.set(self.get_task_client_label(client))

    def get_task_client_label(self, client):
        for label, client_id in self.task_client_map.items():
            if client_id == client.get("id"):
                return label
        return "Sin cliente"

    def get_visible_tasks_sorted(self):
        visible_tasks = []
        include_completed = self.task_show_completed_var.get() if hasattr(self, "task_show_completed_var") else True
        for task in self.tasks:
            if task.get("status") == "completed" and not include_completed:
                continue
            visible_tasks.append(task)
        visible_tasks.sort(key=self.get_task_sort_key)
        return visible_tasks

    def get_task_sort_key(self, task):
        status_bucket = 0 if task.get("status") == "pending" else 1
        today_iso = date.today().isoformat()
        due_date = task.get("due_date", "")
        if due_date < today_iso:
            bucket = 0
        elif due_date == today_iso:
            bucket = 1
        else:
            bucket = 2
        urgency_rank = {"rojo": 0, "amarillo": 1, "verde": 2}.get(task.get("urgency"), 1)
        due_time = task.get("due_time", "") or "99:99"
        completed_at = task.get("completed_at") or ""
        return (status_bucket, bucket, due_date, due_time, urgency_rank, completed_at, task.get("title", "").lower())

    def refresh_tasks_tree(self):
        if not hasattr(self, "tasks_tree"):
            return

        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        for task in self.get_visible_tasks_sorted():
            task_id = task.get("id")
            tags = [task.get("urgency", "amarillo")]
            if task.get("status") == "completed":
                tags.append("completed")
            elif task.get("due_date", "") < date.today().isoformat():
                tags.append("overdue")
            self.tasks_tree.insert(
                "",
                "end",
                iid=task_id,
                values=(
                    self._truncate_middle(task.get("title", ""), 32),
                    self._truncate_middle(self.get_client_name_for_task(task), 28),
                    self.format_task_date(task.get("due_date", "")),
                    task.get("due_time", "").strip() or "--:--",
                    task.get("urgency", "").capitalize(),
                    self.format_task_recurrence(task.get("recurrence", "none")),
                    self.format_task_status(task.get("status", "pending")),
                ),
                tags=tuple(tags),
            )

        self.tasks_tree.tag_configure("verde", foreground=self.colors["task_green"])
        self.tasks_tree.tag_configure("amarillo", foreground=self.colors["task_yellow"])
        self.tasks_tree.tag_configure("rojo", foreground=self.colors["task_red"])
        self.tasks_tree.tag_configure("overdue", background="#fff1ef")
        self.tasks_tree.tag_configure("completed", foreground=self.colors["muted"])

        if self.selected_task_id and self.tasks_tree.exists(self.selected_task_id):
            self.tasks_tree.selection_set(self.selected_task_id)
            self.tasks_tree.focus(self.selected_task_id)

    def format_task_date(self, due_date):
        try:
            parsed = datetime.strptime(due_date, "%Y-%m-%d").date()
            return parsed.strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return due_date or "-"

    def format_task_recurrence(self, recurrence):
        labels = {"none": "No", "daily": "Diaria", "weekly": "Semanal", "monthly": "Mensual"}
        return labels.get(recurrence, "No")

    def format_task_status(self, status):
        return "Completada" if status == "completed" else "Pendiente"

    def get_client_name_for_task(self, task):
        client_id = task.get("client_id")
        client = self.find_client_by_id(client_id) if client_id else None
        return client.get("name", "Sin cliente") if client else "Sin cliente"

    def open_task_date_picker(self):
        if self.task_date_picker_window and self.task_date_picker_window.winfo_exists():
            self.task_date_picker_window.lift()
            self.task_date_picker_window.focus_force()
            return

        try:
            current_date = datetime.strptime(self.task_due_date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            current_date = date.today()

        self.task_date_picker_year = current_date.year
        self.task_date_picker_month = current_date.month

        picker = tk.Toplevel(self.root)
        picker.title("Seleccionar fecha")
        picker.transient(self.root)
        picker.resizable(False, False)
        picker.configure(bg=self.colors["card"])
        picker.grab_set()
        self.task_date_picker_window = picker
        picker.protocol("WM_DELETE_WINDOW", self.close_task_date_picker)

        container = ttk.Frame(picker, style="Card.TFrame", padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        ttk.Button(container, text="<", style="Secondary.TButton", width=4, command=lambda: self.shift_task_date_picker_month(-1)).grid(row=0, column=0, sticky="w")
        self.task_date_picker_header = ttk.Label(container, text="", style="Section.TLabel")
        self.task_date_picker_header.grid(row=0, column=1, sticky="n", padx=12)
        ttk.Button(container, text=">", style="Secondary.TButton", width=4, command=lambda: self.shift_task_date_picker_month(1)).grid(row=0, column=2, sticky="e")

        weekdays = ttk.Frame(container, style="Card.TFrame")
        weekdays.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        for index, label in enumerate(("Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do")):
            ttk.Label(weekdays, text=label, style="Muted.TLabel", width=4, anchor="center").grid(row=0, column=index, padx=1, pady=1)

        self.task_date_picker_days = ttk.Frame(container, style="Card.TFrame")
        self.task_date_picker_days.grid(row=2, column=0, columnspan=3, sticky="nsew")

        footer = ttk.Frame(container, style="Card.TFrame")
        footer.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        ttk.Button(footer, text="Hoy", style="Secondary.TButton", command=lambda: self.set_task_due_date(date.today())).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(footer, text="Cerrar", style="Secondary.TButton", command=self.close_task_date_picker).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.render_task_date_picker()

    def close_task_date_picker(self):
        if self.task_date_picker_window and self.task_date_picker_window.winfo_exists():
            self.task_date_picker_window.destroy()
        self.task_date_picker_window = None

    def shift_task_date_picker_month(self, delta):
        month = self.task_date_picker_month + delta
        year = self.task_date_picker_year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.task_date_picker_month = month
        self.task_date_picker_year = year
        self.render_task_date_picker()

    def render_task_date_picker(self):
        if not self.task_date_picker_window or not self.task_date_picker_window.winfo_exists():
            return

        month_name = calendar.month_name[self.task_date_picker_month]
        self.task_date_picker_header.config(text=f"{month_name} {self.task_date_picker_year}")

        for widget in self.task_date_picker_days.winfo_children():
            widget.destroy()

        month_matrix = calendar.Calendar(firstweekday=0).monthdayscalendar(self.task_date_picker_year, self.task_date_picker_month)
        for row_index, week in enumerate(month_matrix):
            for column_index, day_number in enumerate(week):
                if day_number == 0:
                    ttk.Label(self.task_date_picker_days, text="", width=4).grid(row=row_index, column=column_index, padx=1, pady=1)
                    continue
                selected_date = date(self.task_date_picker_year, self.task_date_picker_month, day_number)
                ttk.Button(
                    self.task_date_picker_days,
                    text=str(day_number),
                    style="Secondary.TButton",
                    width=4,
                    command=lambda value=selected_date: self.set_task_due_date(value),
                ).grid(row=row_index, column=column_index, padx=1, pady=1)

    def set_task_due_date(self, selected_date):
        self.task_due_date_var.set(selected_date.isoformat())
        self.close_task_date_picker()

    def open_template_date_picker(self):
        if self.template_date_picker_window and self.template_date_picker_window.winfo_exists():
            self.template_date_picker_window.lift()
            self.template_date_picker_window.focus_force()
            return

        try:
            current_date = datetime.strptime(self.template_date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            current_date = date.today()

        self.template_date_picker_year = current_date.year
        self.template_date_picker_month = current_date.month

        picker = tk.Toplevel(self.root)
        picker.title("Seleccionar fecha")
        picker.transient(self.root)
        picker.resizable(False, False)
        picker.configure(bg=self.colors["card"])
        picker.grab_set()
        self.template_date_picker_window = picker
        picker.protocol("WM_DELETE_WINDOW", self.close_template_date_picker)

        container = ttk.Frame(picker, style="Card.TFrame", padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        ttk.Button(container, text="<", style="Secondary.TButton", width=4, command=lambda: self.shift_template_date_picker_month(-1)).grid(row=0, column=0, sticky="w")
        self.template_date_picker_header = ttk.Label(container, text="", style="Section.TLabel")
        self.template_date_picker_header.grid(row=0, column=1, sticky="n", padx=12)
        ttk.Button(container, text=">", style="Secondary.TButton", width=4, command=lambda: self.shift_template_date_picker_month(1)).grid(row=0, column=2, sticky="e")

        weekdays = ttk.Frame(container, style="Card.TFrame")
        weekdays.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        for index, label in enumerate(("Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do")):
            ttk.Label(weekdays, text=label, style="Muted.TLabel", width=4, anchor="center").grid(row=0, column=index, padx=1, pady=1)

        self.template_date_picker_days = ttk.Frame(container, style="Card.TFrame")
        self.template_date_picker_days.grid(row=2, column=0, columnspan=3, sticky="nsew")

        footer = ttk.Frame(container, style="Card.TFrame")
        footer.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        ttk.Button(footer, text="Hoy", style="Secondary.TButton", command=lambda: self.set_template_date(date.today())).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(footer, text="Cerrar", style="Secondary.TButton", command=self.close_template_date_picker).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.render_template_date_picker()

    def close_template_date_picker(self):
        if self.template_date_picker_window and self.template_date_picker_window.winfo_exists():
            self.template_date_picker_window.destroy()
        self.template_date_picker_window = None

    def shift_template_date_picker_month(self, delta):
        month = self.template_date_picker_month + delta
        year = self.template_date_picker_year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.template_date_picker_month = month
        self.template_date_picker_year = year
        self.render_template_date_picker()

    def render_template_date_picker(self):
        if not self.template_date_picker_window or not self.template_date_picker_window.winfo_exists():
            return

        month_name = calendar.month_name[self.template_date_picker_month]
        self.template_date_picker_header.config(text=f"{month_name} {self.template_date_picker_year}")

        for widget in self.template_date_picker_days.winfo_children():
            widget.destroy()

        month_matrix = calendar.Calendar(firstweekday=0).monthdayscalendar(self.template_date_picker_year, self.template_date_picker_month)
        for row_index, week in enumerate(month_matrix):
            for column_index, day_number in enumerate(week):
                if day_number == 0:
                    ttk.Label(self.template_date_picker_days, text="", width=4).grid(row=row_index, column=column_index, padx=1, pady=1)
                    continue
                selected_date = date(self.template_date_picker_year, self.template_date_picker_month, day_number)
                ttk.Button(
                    self.template_date_picker_days,
                    text=str(day_number),
                    style="Secondary.TButton",
                    width=4,
                    command=lambda value=selected_date: self.set_template_date(value),
                ).grid(row=row_index, column=column_index, padx=1, pady=1)

    def set_template_date(self, selected_date):
        self.template_date_var.set(selected_date.isoformat())
        self.update_template_summary()
        self.close_template_date_picker()

    def prepare_new_task(self):
        self.selected_task_id = None
        self.task_title_var.set("")
        self.task_client_var.set("Sin cliente")
        self.task_due_date_var.set(date.today().isoformat())
        self.task_due_time_var.set("")
        self.task_urgency_var.set("amarillo")
        self.task_recurrence_var.set("none")
        if hasattr(self, "task_notes_text"):
            self.task_notes_text.delete("1.0", tk.END)
        if hasattr(self, "task_detail_hint"):
            self.task_detail_hint.config(text="Crea una tarea nueva o selecciona una existente para editarla.")
        if hasattr(self, "tasks_tree"):
            self.tasks_tree.selection_remove(self.tasks_tree.selection())
        self.update_task_action_buttons()

    def on_task_tree_select(self, _event=None):
        if not hasattr(self, "tasks_tree"):
            return
        selection = self.tasks_tree.selection()
        if selection:
            self.select_task(selection[0])

    def select_task(self, task_id):
        task = self.find_task_by_id(task_id)
        if not task:
            return

        self.selected_task_id = task_id
        self.task_title_var.set(task.get("title", ""))
        self.task_due_date_var.set(task.get("due_date", date.today().isoformat()))
        self.task_due_time_var.set(task.get("due_time", ""))
        self.task_urgency_var.set(task.get("urgency", "amarillo"))
        self.task_recurrence_var.set(task.get("recurrence", "none"))
        client = self.find_client_by_id(task.get("client_id")) if task.get("client_id") else None
        self.task_client_var.set(self.get_task_client_label(client) if client else "Sin cliente")
        if hasattr(self, "task_notes_text"):
            self.task_notes_text.delete("1.0", tk.END)
            self.task_notes_text.insert("1.0", task.get("notes", ""))
        if hasattr(self, "task_detail_hint"):
            if task.get("status") == "completed":
                self.task_detail_hint.config(text="Esta tarea esta completada. Puedes revisarla, eliminarla o editarla para reactivarla.")
            else:
                self.task_detail_hint.config(text="Edita la tarea seleccionada o marquela como completada.")
        self.update_task_action_buttons()

    def update_task_action_buttons(self):
        task = self.find_task_by_id(self.selected_task_id) if self.selected_task_id else None
        complete_state = "normal" if task and task.get("status") != "completed" else "disabled"
        delete_state = "normal" if task else "disabled"
        if hasattr(self, "task_complete_button"):
            self.task_complete_button.config(state=complete_state)
        if hasattr(self, "task_delete_button"):
            self.task_delete_button.config(state=delete_state)

    def find_task_by_id(self, task_id):
        for task in self.tasks:
            if task.get("id") == task_id:
                return task
        return None

    def build_task_payload(self):
        title = self.task_title_var.get().strip()
        due_date = self.task_due_date_var.get().strip()
        due_time = self.task_due_time_var.get().strip()
        urgency = self.task_urgency_var.get().strip() or "amarillo"
        recurrence = self.task_recurrence_var.get().strip() or "none"
        notes = self.task_notes_text.get("1.0", tk.END).strip() if hasattr(self, "task_notes_text") else ""
        resolved_ok, client_id = self.resolve_task_client_selection()
        if not resolved_ok:
            return None

        if not title:
            messagebox.showwarning("Aviso", "La tarea debe tener un titulo.")
            return None

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Aviso", "La fecha debe estar en formato YYYY-MM-DD.")
            return None

        if due_time:
            try:
                datetime.strptime(due_time, "%H:%M")
            except ValueError:
                messagebox.showwarning("Aviso", "La hora debe estar en formato HH:MM.")
                return None

        if urgency not in {"verde", "amarillo", "rojo"}:
            urgency = "amarillo"
        if recurrence not in {"none", "daily", "weekly", "monthly"}:
            recurrence = "none"

        return {
            "id": self.selected_task_id or str(uuid.uuid4()),
            "client_id": client_id,
            "title": title,
            "notes": notes,
            "due_date": due_date,
            "due_time": due_time,
            "urgency": urgency,
            "recurrence": recurrence,
            "status": "pending",
            "completed_at": None,
        }

    def normalize_task_record(self, task):
        if not isinstance(task, dict):
            return None

        title = str(task.get("title", "")).strip()
        due_date = str(task.get("due_date", "")).strip()
        if not title or not due_date:
            return None

        urgency = str(task.get("urgency", "amarillo")).strip().lower()
        recurrence = str(task.get("recurrence", "none")).strip().lower()
        status = str(task.get("status", "pending")).strip().lower()
        if urgency not in {"verde", "amarillo", "rojo"}:
            urgency = "amarillo"
        if recurrence not in {"none", "daily", "weekly", "monthly"}:
            recurrence = "none"
        if status not in {"pending", "completed"}:
            status = "pending"

        return {
            "id": str(task.get("id") or uuid.uuid4()),
            "client_id": str(task.get("client_id")).strip() if task.get("client_id") else None,
            "title": title,
            "notes": str(task.get("notes", "")).strip(),
            "due_date": due_date,
            "due_time": str(task.get("due_time", "")).strip(),
            "urgency": urgency,
            "recurrence": recurrence,
            "status": status,
            "completed_at": task.get("completed_at"),
        }

    def load_tasks_from_db(self):
        try:
            with self.get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, client_id, title, notes, due_date, due_time, urgency, recurrence, status, completed_at
                    FROM tasks
                    ORDER BY due_date, due_time, created_at
                    """
                ).fetchall()
            self.tasks = []
            for row in rows:
                normalized = self.normalize_task_record(dict(row))
                if normalized:
                    self.tasks.append(normalized)
        except Exception as exc:
            self.tasks = []
            self.log(f"[ERROR] No se pudieron cargar las tareas. Detalle: {exc}")

    def save_task_to_db(self, payload):
        normalized = self.normalize_task_record(payload)
        if not normalized:
            return False

        try:
            with self.get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO tasks (
                        id,
                        client_id,
                        title,
                        notes,
                        due_date,
                        due_time,
                        urgency,
                        recurrence,
                        status,
                        completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        client_id = excluded.client_id,
                        title = excluded.title,
                        notes = excluded.notes,
                        due_date = excluded.due_date,
                        due_time = excluded.due_time,
                        urgency = excluded.urgency,
                        recurrence = excluded.recurrence,
                        status = excluded.status,
                        completed_at = excluded.completed_at,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        normalized["id"],
                        normalized["client_id"],
                        normalized["title"],
                        normalized["notes"],
                        normalized["due_date"],
                        normalized["due_time"],
                        normalized["urgency"],
                        normalized["recurrence"],
                        normalized["status"],
                        normalized["completed_at"],
                    ),
                )
            return True
        except sqlite3.Error as exc:
            self.log(f"[ERROR] No se pudo guardar la tarea '{normalized['title']}'. Detalle: {exc}")
            return False

    def delete_task_from_db(self, task_id):
        with self.get_db_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def complete_task_in_db(self, task_id):
        completed_at = datetime.now().isoformat(timespec="seconds")
        with self.get_db_connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'completed',
                    completed_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (completed_at, task_id),
            )
        return completed_at

    def generate_next_recurring_task(self, task):
        recurrence = task.get("recurrence", "none")
        if recurrence == "none":
            return

        next_due_date = self.calculate_next_due_date(task.get("due_date", ""), recurrence)
        if not next_due_date:
            return

        self.save_task_to_db(
            {
                "id": str(uuid.uuid4()),
                "client_id": task.get("client_id"),
                "title": task.get("title", ""),
                "notes": task.get("notes", ""),
                "due_date": next_due_date,
                "due_time": task.get("due_time", ""),
                "urgency": task.get("urgency", "amarillo"),
                "recurrence": recurrence,
                "status": "pending",
                "completed_at": None,
            }
        )

    def calculate_next_due_date(self, due_date, recurrence):
        try:
            current = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            return None

        if recurrence == "daily":
            return (current + timedelta(days=1)).isoformat()
        if recurrence == "weekly":
            return (current + timedelta(days=7)).isoformat()
        if recurrence == "monthly":
            year = current.year
            month = current.month + 1
            if month > 12:
                month = 1
                year += 1
            day = min(current.day, calendar.monthrange(year, month)[1])
            return date(year, month, day).isoformat()
        return current.isoformat()

    def save_task(self):
        payload = self.build_task_payload()
        if not payload:
            return

        existing = self.find_task_by_id(payload["id"])
        if not self.save_task_to_db(payload):
            messagebox.showerror("Error", "No se pudo guardar la tarea en la base de datos.")
            return

        self.load_tasks_from_db()
        self.refresh_tasks_ui()
        self.select_task(payload["id"])
        if existing:
            self.log(f"[INFO] Tarea actualizada: {payload['title']}")
        else:
            self.log(f"[INFO] Tarea agregada: {payload['title']}")

    def complete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Aviso", "Selecciona una tarea para completarla.")
            return

        task = self.find_task_by_id(self.selected_task_id)
        if not task:
            return

        self.complete_task_in_db(self.selected_task_id)
        self.generate_next_recurring_task(task)
        self.load_tasks_from_db()
        self.log(f"[INFO] Tarea completada: {task.get('title', 'Sin titulo')}")
        self.prepare_new_task()
        self.refresh_tasks_ui()

    def delete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Aviso", "Selecciona una tarea para eliminarla.")
            return

        task = self.find_task_by_id(self.selected_task_id)
        if not task:
            return

        confirmed = messagebox.askyesno(
            "Confirmar borrado",
            f"¿Deseas eliminar la tarea '{task.get('title', 'Sin titulo')}'?",
        )
        if not confirmed:
            return

        self.delete_task_from_db(self.selected_task_id)
        self.load_tasks_from_db()
        self.log(f"[INFO] Tarea eliminada: {task.get('title', 'Sin titulo')}")
        self.prepare_new_task()
        self.refresh_tasks_ui()

    def select_quick_client_location(self):
        initial_dir = self.quick_client_location_var.get().strip()
        selected = self.choose_folder("Selecciona la carpeta del cliente", initial_dir)
        if selected:
            self.quick_client_location_var.set(selected)

    def save_quick_client(self):
        name = self.quick_client_name_var.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "El cliente rapido debe tener un nombre.")
            return

        payload = {
            "id": str(uuid.uuid4()),
            "name": name,
            "rnc": self.quick_client_rnc_var.get().strip(),
            "pc_location": self.quick_client_location_var.get().strip(),
            "cedula": "",
            "tss_class": "",
            "resource_path": "",
            "work_description": "",
        }
        if not self.ensure_client_default_folder(payload):
            return

        if not self.save_client_to_db(payload):
            messagebox.showerror("Error", "No se pudo guardar el cliente rapido.")
            return

        self.load_clients_from_db()
        self.refresh_clients_ui()
        self.refresh_tasks_ui()
        client = self.find_client_by_id(payload["id"])
        if client:
            self.task_client_var.set(self.get_task_client_label(client))
        self.quick_client_name_var.set("")
        self.quick_client_rnc_var.set("")
        self.quick_client_location_var.set("")
        self.log(f"[INFO] Cliente agregado desde tareas: {payload['name']}")

    def _build_states_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame", padding=22)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        title_block = ttk.Frame(header, style="Card.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(title_block, text="Estados", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Prepara el encabezado, selecciona cuentas y captura valores para balance general y estado de resultados.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.statement_status_summary = self._create_info_card(header, 0, 1, "Estado activo", "Sin cargar")

        self.states_stage = ttk.Frame(parent, style="App.TFrame", padding=0)
        self.states_stage.grid(row=1, column=0, sticky="nsew")
        self.states_stage.grid_rowconfigure(0, weight=1)
        self.states_stage.grid_columnconfigure(0, weight=1)

        self.statement_intro_panel = ttk.Frame(self.states_stage, style="Card.TFrame", padding=28)
        self.statement_intro_panel.grid_columnconfigure(0, weight=1)

        ttk.Label(self.statement_intro_panel, text="Encabezado", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.statement_intro_panel,
            text="Selecciona cliente, año y fecha para cargar el juego de estados.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(self.statement_intro_panel, text="Año", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        self.statement_year_entry = ttk.Entry(self.statement_intro_panel, textvariable=self.statement_year_var, font=("Segoe UI", 11))
        self.statement_year_entry.grid(row=3, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(self.statement_intro_panel, text="Fecha", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        self.statement_date_entry = ttk.Entry(self.statement_intro_panel, textvariable=self.statement_date_var, font=("Segoe UI", 11))
        self.statement_date_entry.grid(row=5, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(self.statement_intro_panel, text="Cliente", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        self.statement_client_selector = ttk.Combobox(
            self.statement_intro_panel,
            textvariable=self.statement_client_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.statement_client_selector.grid(row=7, column=0, sticky="ew", pady=(6, 12))
        self.statement_client_selector.bind("<<ComboboxSelected>>", self.on_statement_client_selected)

        self.statement_entity_label = ttk.Label(
            self.statement_intro_panel,
            text="Tipo detectado: Persona juridica",
            style="Body.TLabel",
        )
        self.statement_entity_label.grid(row=8, column=0, sticky="w", pady=(0, 18))

        header_actions = ttk.Frame(self.statement_intro_panel, style="Card.TFrame")
        header_actions.grid(row=9, column=0, sticky="ew")
        header_actions.grid_columnconfigure(0, weight=1)
        header_actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            header_actions,
            text="Cargar estado",
            style="Primary.TButton",
            command=self.load_or_create_statement,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            header_actions,
            text="Guardar valores",
            style="Secondary.TButton",
            command=self.save_statement_values,
        ).grid(row=0, column=1, sticky="ew")

        ttk.Button(
            self.statement_intro_panel,
            text="Administrar cuentas predeterminadas",
            style="Secondary.TButton",
            command=self.open_statement_default_manager,
        ).grid(row=10, column=0, sticky="ew", pady=(12, 0))

        intro_pdf_actions = ttk.Frame(self.statement_intro_panel, style="Card.TFrame")
        intro_pdf_actions.grid(row=11, column=0, sticky="ew", pady=(12, 0))
        intro_pdf_actions.grid_columnconfigure(0, weight=1)
        intro_pdf_actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            intro_pdf_actions,
            text="Vista previa",
            style="Secondary.TButton",
            command=self.open_statement_preview,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            intro_pdf_actions,
            text="Generar PDF",
            style="Primary.TButton",
            command=self.generate_statement_pdf,
        ).grid(row=0, column=1, sticky="ew")

        ttk.Separator(self.statement_intro_panel, orient="horizontal").grid(row=12, column=0, sticky="ew", pady=(18, 16))

        ttk.Label(self.statement_intro_panel, text="Estados realizados", style="Section.TLabel").grid(row=13, column=0, sticky="w")
        ttk.Label(
            self.statement_intro_panel,
            text="Haz doble clic en un estado para cargarlo y continuar editando o generar su PDF.",
            style="Body.TLabel",
            wraplength=340,
            justify="left",
        ).grid(row=14, column=0, sticky="w", pady=(4, 10))

        self.statement_history_listbox = tk.Listbox(
            self.statement_intro_panel,
            exportselection=False,
            height=8,
            font=("Segoe UI", 10),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.statement_history_listbox.grid(row=15, column=0, sticky="nsew")
        self.statement_history_listbox.bind("<Double-Button-1>", self.load_statement_from_history)

        ttk.Button(
            self.statement_intro_panel,
            text="Cargar estado seleccionado",
            style="Secondary.TButton",
            command=self.load_statement_from_history,
        ).grid(row=16, column=0, sticky="ew", pady=(10, 0))

        self.statement_intro_panel.grid_rowconfigure(15, weight=1)

        self.statement_workspace = ttk.Frame(self.states_stage, style="App.TFrame", padding=0)
        self.statement_workspace.grid_rowconfigure(0, weight=1)
        self.statement_workspace.grid_columnconfigure(0, weight=0)
        self.statement_workspace.grid_columnconfigure(1, weight=1)

        self.statement_left_panel = ttk.Frame(self.statement_workspace, style="Card.TFrame", padding=22)
        self.statement_left_panel.grid_columnconfigure(0, weight=1)
        self.statement_left_panel.grid_rowconfigure(24, weight=1)

        ttk.Label(self.statement_left_panel, text="Encabezado", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.statement_left_panel,
            text="Edita los datos del encabezado o guarda los valores del estado cargado.",
            style="Body.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(self.statement_left_panel, text="Año", style="Body.TLabel").grid(row=2, column=0, sticky="w")
        self.statement_year_loaded_entry = ttk.Entry(
            self.statement_left_panel,
            textvariable=self.statement_year_var,
            font=("Segoe UI", 11),
        )
        self.statement_year_loaded_entry.grid(row=3, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(self.statement_left_panel, text="Fecha", style="Body.TLabel").grid(row=4, column=0, sticky="w")
        self.statement_date_loaded_entry = ttk.Entry(
            self.statement_left_panel,
            textvariable=self.statement_date_var,
            font=("Segoe UI", 11),
        )
        self.statement_date_loaded_entry.grid(row=5, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(self.statement_left_panel, text="Cliente", style="Body.TLabel").grid(row=6, column=0, sticky="w")
        self.statement_client_loaded_selector = ttk.Combobox(
            self.statement_left_panel,
            textvariable=self.statement_client_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.statement_client_loaded_selector.grid(row=7, column=0, sticky="ew", pady=(6, 12))
        self.statement_client_loaded_selector.bind("<<ComboboxSelected>>", self.on_statement_client_selected)

        self.statement_entity_loaded_label = ttk.Label(
            self.statement_left_panel,
            text="Tipo detectado: Persona juridica",
            style="Body.TLabel",
        )
        self.statement_entity_loaded_label.grid(row=8, column=0, sticky="w", pady=(0, 18))

        loaded_header_actions = ttk.Frame(self.statement_left_panel, style="Card.TFrame")
        loaded_header_actions.grid(row=9, column=0, sticky="ew", pady=(0, 22))
        loaded_header_actions.grid_columnconfigure(0, weight=1)
        loaded_header_actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            loaded_header_actions,
            text="Cargar estado",
            style="Primary.TButton",
            command=self.load_or_create_statement,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            loaded_header_actions,
            text="Guardar valores",
            style="Secondary.TButton",
            command=self.save_statement_values,
        ).grid(row=0, column=1, sticky="ew")

        loaded_pdf_actions = ttk.Frame(self.statement_left_panel, style="Card.TFrame")
        loaded_pdf_actions.grid(row=10, column=0, sticky="ew", pady=(0, 18))
        loaded_pdf_actions.grid_columnconfigure(0, weight=1)
        loaded_pdf_actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            loaded_pdf_actions,
            text="Vista previa",
            style="Secondary.TButton",
            command=self.open_statement_preview,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            loaded_pdf_actions,
            text="Generar PDF",
            style="Primary.TButton",
            command=self.generate_statement_pdf,
        ).grid(row=0, column=1, sticky="ew")

        ttk.Separator(self.statement_left_panel, orient="horizontal").grid(row=11, column=0, sticky="ew", pady=(0, 18))

        ttk.Label(self.statement_left_panel, text="Agregar cuentas", style="Section.TLabel").grid(row=12, column=0, sticky="w")
        ttk.Label(
            self.statement_left_panel,
            text="Selecciona el estado y luego una cuenta disponible para incluirla en la captura.",
            style="Body.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=13, column=0, sticky="w", pady=(4, 16))

        ttk.Label(self.statement_left_panel, text="Estado", style="Body.TLabel").grid(row=14, column=0, sticky="w")
        self.statement_target_selector = ttk.Combobox(
            self.statement_left_panel,
            textvariable=self.statement_target_var,
            state="readonly",
            style="Modern.TCombobox",
            values=("balance_general", "estado_resultados"),
        )
        self.statement_target_selector.grid(row=15, column=0, sticky="ew", pady=(6, 12))
        self.statement_target_selector.bind("<<ComboboxSelected>>", lambda _event: self.refresh_statement_account_selector())

        ttk.Label(self.statement_left_panel, text="Cuenta disponible", style="Body.TLabel").grid(row=16, column=0, sticky="w")
        self.statement_account_selector = ttk.Combobox(
            self.statement_left_panel,
            textvariable=self.statement_account_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.statement_account_selector.grid(row=17, column=0, sticky="ew", pady=(6, 12))

        ttk.Button(
            self.statement_left_panel,
            text="Agregar cuenta al estado",
            style="Primary.TButton",
            command=self.add_selected_account_to_statement,
        ).grid(row=18, column=0, sticky="ew")

        ttk.Button(
            self.statement_left_panel,
            text="Administrar cuentas predeterminadas",
            style="Secondary.TButton",
            command=self.open_statement_default_manager,
        ).grid(row=19, column=0, sticky="ew", pady=(10, 0))

        self.statement_helper_label = ttk.Label(
            self.statement_left_panel,
            text="Carga un estado para comenzar a editar valores.",
            style="Body.TLabel",
            wraplength=300,
            justify="left",
        )
        self.statement_helper_label.grid(row=20, column=0, sticky="w", pady=(16, 0))

        ttk.Separator(self.statement_left_panel, orient="horizontal").grid(row=21, column=0, sticky="ew", pady=(18, 16))

        ttk.Label(self.statement_left_panel, text="Estados realizados", style="Section.TLabel").grid(row=22, column=0, sticky="w")
        ttk.Label(
            self.statement_left_panel,
            text="La lista se actualiza automaticamente con los estados guardados.",
            style="Body.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=23, column=0, sticky="w", pady=(4, 10))

        self.statement_history_loaded_listbox = tk.Listbox(
            self.statement_left_panel,
            exportselection=False,
            height=8,
            font=("Segoe UI", 10),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.statement_history_loaded_listbox.grid(row=24, column=0, sticky="nsew")
        self.statement_history_loaded_listbox.bind("<Double-Button-1>", self.load_statement_from_history)

        ttk.Button(
            self.statement_left_panel,
            text="Cargar estado seleccionado",
            style="Secondary.TButton",
            command=self.load_statement_from_history,
        ).grid(row=25, column=0, sticky="ew", pady=(10, 0))

        self.statement_right_panel = ttk.Frame(self.statement_workspace, style="Card.TFrame", padding=0)
        self.statement_right_panel.grid_rowconfigure(0, weight=1)
        self.statement_right_panel.grid_columnconfigure(0, weight=1)

        self.states_canvas = tk.Canvas(
            self.statement_right_panel,
            bg=self.colors["bg"],
            highlightthickness=0,
            bd=0,
        )
        self.states_canvas.grid(row=0, column=0, sticky="nsew")

        states_scrollbar = ttk.Scrollbar(self.statement_right_panel, orient="vertical", command=self.states_canvas.yview)
        states_scrollbar.grid(row=0, column=1, sticky="ns")
        self.states_canvas.configure(yscrollcommand=states_scrollbar.set)

        self.states_content = ttk.Frame(self.states_canvas, style="App.TFrame", padding=0)
        self.states_content.grid_columnconfigure(0, weight=1)
        self.states_window = self.states_canvas.create_window((0, 0), window=self.states_content, anchor="nw")
        self.states_content.bind("<Configure>", self._update_states_scrollregion)
        self.states_canvas.bind("<Configure>", self._resize_states_inner)

        self.balance_general_panel = ttk.Frame(self.states_content, style="Card.TFrame", padding=22)
        self.balance_general_panel.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.balance_general_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(self.balance_general_panel, text="Balance general", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.balance_general_body = ttk.Frame(self.balance_general_panel, style="Card.TFrame")
        self.balance_general_body.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self.balance_general_body.grid_columnconfigure(0, weight=1)

        self.estado_resultados_panel = ttk.Frame(self.states_content, style="Card.TFrame", padding=22)
        self.estado_resultados_panel.grid(row=1, column=0, sticky="ew")
        self.estado_resultados_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(self.estado_resultados_panel, text="Estado de resultados", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.estado_resultados_body = ttk.Frame(self.estado_resultados_panel, style="Card.TFrame")
        self.estado_resultados_body.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self.estado_resultados_body.grid_columnconfigure(0, weight=1)

        self.statement_defaults_panel = ttk.Frame(self.states_stage, style="Card.TFrame", padding=24)
        self.statement_defaults_panel.grid_columnconfigure(0, weight=1)
        self.statement_defaults_panel.grid_rowconfigure(2, weight=1)

        defaults_header = ttk.Frame(self.statement_defaults_panel, style="Card.TFrame")
        defaults_header.grid(row=0, column=0, sticky="ew")
        defaults_header.grid_columnconfigure(0, weight=1)

        ttk.Label(defaults_header, text="Cuentas predeterminadas", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            defaults_header,
            text="Configura las cuentas que se cargan por defecto para todos los clientes, segun el grupo madre.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Button(
            defaults_header,
            text="X",
            style="Secondary.TButton",
            command=self.close_statement_default_manager,
        ).grid(row=0, column=1, rowspan=2, sticky="ne")

        defaults_filters = ttk.Frame(self.statement_defaults_panel, style="Card.TFrame")
        defaults_filters.grid(row=1, column=0, sticky="ew", pady=(18, 18))
        defaults_filters.grid_columnconfigure(1, weight=1)
        defaults_filters.grid_columnconfigure(3, weight=1)
        defaults_filters.grid_columnconfigure(5, weight=1)

        ttk.Label(defaults_filters, text="Tipo", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.statement_defaults_entity_selector = ttk.Combobox(
            defaults_filters,
            textvariable=self.statement_defaults_entity_var,
            state="readonly",
            style="Modern.TCombobox",
            values=("juridica", "fisica"),
        )
        self.statement_defaults_entity_selector.grid(row=0, column=1, sticky="ew", padx=(8, 18))
        self.statement_defaults_entity_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_statement_defaults_root_selector(),
        )

        ttk.Label(defaults_filters, text="Cuenta madre", style="Body.TLabel").grid(row=0, column=2, sticky="w")
        self.statement_defaults_root_selector = ttk.Combobox(
            defaults_filters,
            textvariable=self.statement_defaults_root_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.statement_defaults_root_selector.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        self.statement_defaults_root_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_statement_defaults_subaccount_selector(),
        )

        ttk.Label(defaults_filters, text="Subcuenta", style="Body.TLabel").grid(row=0, column=4, sticky="w", padx=(18, 0))
        self.statement_defaults_subaccount_selector = ttk.Combobox(
            defaults_filters,
            textvariable=self.statement_defaults_subaccount_var,
            state="readonly",
            style="Modern.TCombobox",
        )
        self.statement_defaults_subaccount_selector.grid(row=0, column=5, sticky="ew", padx=(8, 0))
        self.statement_defaults_subaccount_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_statement_defaults_lists(),
        )

        defaults_lists = ttk.Frame(self.statement_defaults_panel, style="Card.TFrame")
        defaults_lists.grid(row=2, column=0, sticky="nsew")
        defaults_lists.grid_columnconfigure(0, weight=1)
        defaults_lists.grid_columnconfigure(1, weight=0)
        defaults_lists.grid_columnconfigure(2, weight=1)
        defaults_lists.grid_rowconfigure(2, weight=1)

        ttk.Label(defaults_lists, text="Disponibles", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Label(defaults_lists, text="Predeterminadas", style="Section.TLabel").grid(row=0, column=2, sticky="w", pady=(0, 10))

        self.statement_defaults_available_search_entry = ttk.Entry(
            defaults_lists,
            textvariable=self.statement_defaults_available_search_var,
            font=("Segoe UI", 10),
        )
        self.statement_defaults_available_search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.statement_defaults_available_search_var.trace_add("write", lambda *_args: self.refresh_statement_defaults_lists())

        self.statement_defaults_selected_search_entry = ttk.Entry(
            defaults_lists,
            textvariable=self.statement_defaults_selected_search_var,
            font=("Segoe UI", 10),
        )
        self.statement_defaults_selected_search_entry.grid(row=1, column=2, sticky="ew", pady=(0, 12))
        self.statement_defaults_selected_search_var.trace_add("write", lambda *_args: self.refresh_statement_defaults_lists())

        self.statement_defaults_available_listbox = tk.Listbox(
            defaults_lists,
            exportselection=False,
            font=("Segoe UI", 10),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.statement_defaults_available_listbox.grid(row=2, column=0, sticky="nsew")

        defaults_actions = ttk.Frame(defaults_lists, style="Card.TFrame")
        defaults_actions.grid(row=2, column=1, sticky="ns", padx=18)
        defaults_actions.grid_columnconfigure(0, weight=1)

        ttk.Button(
            defaults_actions,
            text="Agregar >>",
            style="Primary.TButton",
            command=self.add_statement_default_account,
        ).grid(row=0, column=0, sticky="ew", pady=(50, 10))
        ttk.Button(
            defaults_actions,
            text="<< Quitar",
            style="Secondary.TButton",
            command=self.remove_statement_default_account,
        ).grid(row=1, column=0, sticky="ew")

        self.statement_defaults_selected_listbox = tk.Listbox(
            defaults_lists,
            exportselection=False,
            font=("Segoe UI", 10),
            bg=self.colors["card_alt"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.statement_defaults_selected_listbox.grid(row=2, column=2, sticky="nsew")

        self.statement_defaults_helper_label = ttk.Label(
            self.statement_defaults_panel,
            text="Selecciona una cuenta madre para agregar o quitar cuentas predeterminadas globales.",
            style="Body.TLabel",
            wraplength=900,
            justify="left",
        )
        self.statement_defaults_helper_label.grid(row=3, column=0, sticky="w", pady=(16, 0))

        self.refresh_states_client_selector()
        self.refresh_statement_history()
        self.refresh_statement_defaults_root_selector()
        self.render_statement_views()
        self.update_statement_layout()

    def update_statement_layout(self):
        if not hasattr(self, "states_stage"):
            return

        layout_state = (self.statement_screen_mode, bool(self.statement_id))
        if layout_state == self.statement_layout_loaded and hasattr(self, "statement_workspace"):
            return

        self.statement_layout_loaded = layout_state
        self.statement_intro_panel.grid_forget()
        self.statement_workspace.grid_forget()
        self.statement_defaults_panel.grid_forget()
        self.statement_left_panel.grid_forget()
        self.statement_right_panel.grid_forget()

        if self.statement_screen_mode == "defaults":
            self.statement_defaults_panel.grid(row=0, column=0, sticky="nsew", padx=32, pady=24)
            return

        if self.statement_id:
            self.statement_workspace.grid(row=0, column=0, sticky="nsew")
            self.statement_left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))
            self.statement_right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        else:
            self.statement_intro_panel.grid(row=0, column=0, padx=32, pady=24)

    def open_statement_default_manager(self):
        self.statement_screen_mode = "defaults"
        self.refresh_statement_defaults_root_selector()
        self.update_statement_layout()

    def close_statement_default_manager(self):
        self.statement_screen_mode = "editor"
        self.update_statement_layout()

    def get_statement_root_accounts(self, entity_type):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, statement_type, entity_type, root_group, name, sort_order
                FROM account_catalog
                WHERE entity_type = ? AND level = 0
                ORDER BY statement_type, sort_order, name
                """,
                (entity_type,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_accounts_for_root_group(self, statement_type, entity_type, root_group):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, parent_id, code, name, level, sort_order
                FROM account_catalog
                WHERE statement_type = ?
                  AND entity_type = ?
                  AND root_group = ?
                  AND level > 0
                ORDER BY level, sort_order, name
                """,
                (statement_type, entity_type, root_group),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_descendant_account_ids(self, accounts, parent_id):
        descendants = {parent_id}
        added = True
        while added:
            added = False
            for account in accounts:
                current_id = account.get("id")
                if current_id in descendants:
                    continue
                if account.get("parent_id") in descendants:
                    descendants.add(current_id)
                    added = True
        return descendants

    def get_default_account_ids_for_root_group(self, statement_type, entity_type, root_group):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT defaults.account_id
                FROM statement_default_accounts AS defaults
                JOIN account_catalog AS catalog ON catalog.id = defaults.account_id
                WHERE defaults.statement_type = ?
                  AND defaults.entity_type = ?
                  AND catalog.root_group = ?
                ORDER BY catalog.level, catalog.sort_order, catalog.name
                """,
                (statement_type, entity_type, root_group),
            ).fetchall()
        return {row["account_id"] for row in rows}

    def refresh_statement_defaults_root_selector(self):
        if not hasattr(self, "statement_defaults_root_selector"):
            return

        entity_type = self.statement_defaults_entity_var.get() or "juridica"
        roots = self.get_statement_root_accounts(entity_type)
        current_value = self.statement_defaults_root_var.get().strip()

        self.statement_defaults_root_map = {}
        options = []
        for root in roots:
            statement_label = "Balance general" if root["statement_type"] == "balance_general" else "Estado de resultados"
            label = f"{statement_label} / {root['name']}"
            self.statement_defaults_root_map[label] = (root["id"], root["statement_type"], root["root_group"])
            options.append(label)

        self.statement_defaults_root_selector["values"] = options
        if current_value in self.statement_defaults_root_map:
            self.statement_defaults_root_var.set(current_value)
        elif options:
            self.statement_defaults_root_var.set(options[0])
        else:
            self.statement_defaults_root_var.set("")

        self.refresh_statement_defaults_subaccount_selector()

    def refresh_statement_defaults_subaccount_selector(self):
        if not hasattr(self, "statement_defaults_subaccount_selector"):
            return

        root_label = self.statement_defaults_root_var.get().strip()
        root_selection = self.statement_defaults_root_map.get(root_label)
        current_value = self.statement_defaults_subaccount_var.get().strip()
        self.statement_defaults_subaccount_map = {"Todas": None}
        options = ["Todas"]

        if root_selection:
            root_id, statement_type, root_group = root_selection
            entity_type = self.statement_defaults_entity_var.get() or "juridica"
            accounts = self.get_accounts_for_root_group(statement_type, entity_type, root_group)
            children = [account for account in accounts if account.get("parent_id") == root_id]
            for account in children:
                code = account.get("code", "").strip()
                name = account.get("name", "")
                label = f"{code} - {name}" if code else name
                self.statement_defaults_subaccount_map[label] = account["id"]
                options.append(label)

        self.statement_defaults_subaccount_selector["values"] = options
        if current_value in self.statement_defaults_subaccount_map:
            self.statement_defaults_subaccount_var.set(current_value)
        else:
            self.statement_defaults_subaccount_var.set("Todas")

        self.refresh_statement_defaults_lists()

    def refresh_statement_defaults_lists(self):
        if not hasattr(self, "statement_defaults_available_listbox"):
            return

        self.statement_defaults_available_listbox.delete(0, tk.END)
        self.statement_defaults_selected_listbox.delete(0, tk.END)
        self.statement_defaults_available_map = {}
        self.statement_defaults_selected_map = {}

        root_label = self.statement_defaults_root_var.get().strip()
        root_selection = self.statement_defaults_root_map.get(root_label)
        if not root_selection:
            if hasattr(self, "statement_defaults_helper_label"):
                self.statement_defaults_helper_label.config(
                    text="No hay cuentas madre disponibles para el tipo seleccionado."
                )
            return

        _root_id, statement_type, root_group = root_selection
        entity_type = self.statement_defaults_entity_var.get() or "juridica"
        accounts = self.get_accounts_for_root_group(statement_type, entity_type, root_group)
        subaccount_id = self.statement_defaults_subaccount_map.get(self.statement_defaults_subaccount_var.get().strip())
        if subaccount_id:
            descendant_ids = self.get_descendant_account_ids(accounts, subaccount_id)
            accounts = [account for account in accounts if account.get("id") in descendant_ids]
        selected_ids = self.get_default_account_ids_for_root_group(statement_type, entity_type, root_group)
        available_search = self.statement_defaults_available_search_var.get().strip().lower()
        selected_search = self.statement_defaults_selected_search_var.get().strip().lower()

        for account in accounts:
            indent = "   " * max(account.get("level", 1) - 1, 0)
            name = account.get("name", "")
            code = account.get("code", "").strip()
            label = f"{indent}{code} - {name}" if code else f"{indent}{name}"
            if account["id"] in selected_ids:
                if selected_search and selected_search not in label.lower():
                    continue
                self.statement_defaults_selected_map[label] = account["id"]
                self.statement_defaults_selected_listbox.insert(tk.END, label)
            else:
                if available_search and available_search not in label.lower():
                    continue
                self.statement_defaults_available_map[label] = account["id"]
                self.statement_defaults_available_listbox.insert(tk.END, label)

        if hasattr(self, "statement_defaults_helper_label"):
            self.statement_defaults_helper_label.config(
                text=f"Grupo activo: {root_group}. Los cambios aplican a todos los clientes."
            )

    def add_statement_default_account(self):
        selection = self.statement_defaults_available_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una cuenta disponible para agregar.")
            return

        label = self.statement_defaults_available_listbox.get(selection[0])
        account_id = self.statement_defaults_available_map.get(label)
        root_label = self.statement_defaults_root_var.get().strip()
        root_selection = self.statement_defaults_root_map.get(root_label)
        if not account_id or not root_selection:
            return

        _root_id, statement_type, _root_group = root_selection
        entity_type = self.statement_defaults_entity_var.get() or "juridica"
        with self.get_db_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO statement_default_accounts (id, statement_type, entity_type, account_id)
                VALUES (?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), statement_type, entity_type, account_id),
            )

        self.refresh_statement_defaults_lists()
        self.refresh_statement_account_selector()

    def remove_statement_default_account(self):
        selection = self.statement_defaults_selected_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una cuenta predeterminada para quitar.")
            return

        label = self.statement_defaults_selected_listbox.get(selection[0])
        account_id = self.statement_defaults_selected_map.get(label)
        root_label = self.statement_defaults_root_var.get().strip()
        root_selection = self.statement_defaults_root_map.get(root_label)
        if not account_id or not root_selection:
            return

        _root_id, statement_type, _root_group = root_selection
        entity_type = self.statement_defaults_entity_var.get() or "juridica"
        with self.get_db_connection() as conn:
            conn.execute(
                """
                DELETE FROM statement_default_accounts
                WHERE statement_type = ? AND entity_type = ? AND account_id = ?
                """,
                (statement_type, entity_type, account_id),
            )

        self.refresh_statement_defaults_lists()
        self.refresh_statement_account_selector()

    def _update_states_scrollregion(self, _event=None):
        if hasattr(self, "states_canvas"):
            self.states_canvas.configure(scrollregion=self.states_canvas.bbox("all"))

    def _resize_states_inner(self, event):
        if hasattr(self, "states_window"):
            self.states_canvas.itemconfigure(self.states_window, width=event.width)

    def refresh_states_client_selector(self):
        if not hasattr(self, "statement_client_selector"):
            return

        current_value = self.statement_client_var.get().strip()
        self.statement_client_map = {}
        options = []
        for client in self.clients:
            label = client.get("name", "Sin nombre")
            rnc = client.get("rnc", "").strip()
            if rnc:
                label = f"{label} ({rnc})"
            self.statement_client_map[label] = client.get("id")
            options.append(label)

        self.statement_client_selector["values"] = options
        if hasattr(self, "statement_client_loaded_selector"):
            self.statement_client_loaded_selector["values"] = options
        if current_value in self.statement_client_map:
            self.statement_client_var.set(current_value)
        elif options:
            self.statement_client_var.set(options[0])
        else:
            self.statement_client_var.set("")

        self.on_statement_client_selected()

    def get_statement_history_rows(self):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    headers.id,
                    headers.client_id,
                    headers.entity_type,
                    headers.fiscal_year,
                    headers.statement_date,
                    headers.updated_at,
                    clients.name AS client_name
                FROM statement_headers AS headers
                JOIN clients ON clients.id = headers.client_id
                ORDER BY headers.updated_at DESC, clients.name COLLATE NOCASE, headers.fiscal_year DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def refresh_statement_history(self):
        rows = self.get_statement_history_rows()
        self.statement_history_map = {}

        listboxes = []
        if hasattr(self, "statement_history_listbox"):
            listboxes.append(self.statement_history_listbox)
        if hasattr(self, "statement_history_loaded_listbox"):
            listboxes.append(self.statement_history_loaded_listbox)

        for listbox in listboxes:
            listbox.delete(0, tk.END)

        if not rows:
            empty_label = "No hay estados guardados todavia."
            self.statement_history_map[empty_label] = None
            for listbox in listboxes:
                listbox.insert(tk.END, empty_label)
            return

        for row in rows:
            entity_label = "PJ" if row.get("entity_type") == "juridica" else "PF"
            label = (
                f"{row.get('client_name', 'Sin nombre')} | "
                f"{row.get('fiscal_year', '')} | "
                f"{row.get('statement_date', '')} | "
                f"{entity_label}"
            )
            self.statement_history_map[label] = row
            for listbox in listboxes:
                listbox.insert(tk.END, label)

    def load_statement_from_history(self, _event=None):
        listbox = None
        if _event is not None and isinstance(getattr(_event, "widget", None), tk.Listbox):
            listbox = _event.widget
        elif (
            hasattr(self, "statement_history_loaded_listbox")
            and self.statement_history_loaded_listbox.winfo_ismapped()
            and self.statement_history_loaded_listbox.curselection()
        ):
            listbox = self.statement_history_loaded_listbox
        elif hasattr(self, "statement_history_listbox") and self.statement_history_listbox.curselection():
            listbox = self.statement_history_listbox

        if not listbox:
            messagebox.showwarning("Aviso", "Selecciona un estado realizado para cargarlo.")
            return

        label = listbox.get(listbox.curselection()[0])
        row = self.statement_history_map.get(label)
        if not row or not row.get("id"):
            messagebox.showwarning("Aviso", "Ese elemento no corresponde a un estado valido.")
            return

        client = self.find_client_by_id(row.get("client_id"))
        if not client:
            messagebox.showwarning("Aviso", "El cliente asociado a este estado ya no existe.")
            return

        client_label = client.get("name", "Sin nombre")
        rnc = client.get("rnc", "").strip()
        if rnc:
            client_label = f"{client_label} ({rnc})"

        self.statement_id = row["id"]
        self.statement_year_var.set(str(row.get("fiscal_year", "")))
        self.statement_date_var.set(row.get("statement_date", "") or "")
        self.statement_client_var.set(client_label)
        self.statement_entity_type_var.set(row.get("entity_type") or self.infer_entity_type_for_client(client))
        self.statement_screen_mode = "editor"
        self.on_statement_client_selected()

        if hasattr(self, "statement_status_summary"):
            self.statement_status_summary.config(
                text=f"{client.get('name', 'Sin nombre')} / {row.get('fiscal_year', '')}"
            )
        if hasattr(self, "statement_helper_label"):
            self.statement_helper_label.config(
                text="Estado cargado desde el historial. Puedes editarlo, previsualizarlo o generar el PDF."
            )

        self.render_statement_views()
        self.update_statement_layout()
        self.log(
            f"[INFO] Estado cargado desde historial: {client.get('name', 'Sin nombre')} / {row.get('fiscal_year', '')}"
        )

    def on_statement_client_selected(self, _event=None):
        client = self.get_statement_client()
        entity_type = self.infer_entity_type_for_client(client)
        self.statement_entity_type_var.set(entity_type)
        entity_label = "Persona juridica" if entity_type == "juridica" else "Persona fisica"
        if hasattr(self, "statement_entity_label"):
            self.statement_entity_label.config(text=f"Tipo detectado: {entity_label}")
        if hasattr(self, "statement_entity_loaded_label"):
            self.statement_entity_loaded_label.config(text=f"Tipo detectado: {entity_label}")
        self.refresh_statement_account_selector()

    def get_statement_client(self):
        client_id = self.statement_client_map.get(self.statement_client_var.get().strip())
        return self.find_client_by_id(client_id) if client_id else None

    def infer_entity_type_for_client(self, client):
        if not client:
            return "juridica"

        rnc_digits = re.sub(r"\D", "", client.get("rnc", ""))
        cedula_digits = re.sub(r"\D", "", client.get("cedula", ""))
        if len(rnc_digits) == 9:
            return "juridica"
        if len(rnc_digits) == 11 or len(cedula_digits) == 11:
            return "fisica"
        return "juridica"

    def validate_statement_header(self):
        client = self.get_statement_client()
        if not client:
            messagebox.showwarning("Aviso", "Selecciona un cliente para trabajar los estados.")
            return None

        year_text = self.statement_year_var.get().strip()
        if not year_text.isdigit():
            messagebox.showwarning("Aviso", "El año debe ser numérico.")
            return None

        statement_date = self.statement_date_var.get().strip()
        if not statement_date:
            messagebox.showwarning("Aviso", "La fecha no puede estar vacía.")
            return None

        return {
            "client": client,
            "client_id": client.get("id"),
            "entity_type": self.statement_entity_type_var.get() or "juridica",
            "fiscal_year": int(year_text),
            "statement_date": statement_date,
        }

    def get_or_create_statement_header(self, *, client_id, entity_type, fiscal_year, statement_date):
        with self.get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM statement_headers
                WHERE client_id = ? AND fiscal_year = ?
                """,
                (client_id, fiscal_year),
            ).fetchone()

            if row:
                statement_id = row["id"]
                conn.execute(
                    """
                    UPDATE statement_headers
                    SET entity_type = ?, statement_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (entity_type, statement_date, statement_id),
                )
                return statement_id

            statement_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO statement_headers (id, client_id, entity_type, fiscal_year, statement_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (statement_id, client_id, entity_type, fiscal_year, statement_date),
            )
            return statement_id

    def ensure_statement_line_item(self, conn, statement_id, account_id):
        conn.execute(
            """
            INSERT OR IGNORE INTO statement_line_items (id, statement_id, account_id, amount)
            VALUES (?, ?, ?, NULL)
            """,
            (str(uuid.uuid4()), statement_id, account_id),
        )

    def get_first_child_of_account(self, conn, account_id):
        row = conn.execute(
            """
            SELECT id
            FROM account_catalog
            WHERE parent_id = ?
            ORDER BY sort_order, name
            LIMIT 1
            """,
            (account_id,),
        ).fetchone()
        return row["id"] if row else None

    def ensure_account_with_required_descendants(self, conn, statement_id, account_id):
        current_id = account_id
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            self.ensure_statement_line_item(conn, statement_id, current_id)
            current_id = self.get_first_child_of_account(conn, current_id)

    def get_first_child_account_id(self, conn, statement_type, entity_type, root_name):
        row = conn.execute(
            """
            SELECT child.id
            FROM account_catalog AS root
            JOIN account_catalog AS child ON child.parent_id = root.id
            WHERE root.statement_type = ?
              AND root.entity_type = ?
              AND root.level = 0
              AND root.name = ?
            ORDER BY child.sort_order, child.name
            LIMIT 1
            """,
            (statement_type, entity_type, root_name),
        ).fetchone()
        return row["id"] if row else None

    def get_account_ids_by_names(self, conn, statement_type, entity_type, root_group, names):
        placeholders = ",".join("?" for _ in names)
        rows = conn.execute(
            f"""
            SELECT id
            FROM account_catalog
            WHERE statement_type = ?
              AND entity_type = ?
              AND root_group = ?
              AND name IN ({placeholders})
            ORDER BY sort_order, name
            """,
            [statement_type, entity_type, root_group, *names],
        ).fetchall()
        return [row["id"] for row in rows]

    def get_custom_default_account_ids(self, conn, statement_type, entity_type):
        rows = conn.execute(
            """
            SELECT account_id
            FROM statement_default_accounts
            WHERE statement_type = ? AND entity_type = ?
            ORDER BY created_at, account_id
            """,
            (statement_type, entity_type),
        ).fetchall()
        return [row["account_id"] for row in rows]

    def ensure_default_statement_accounts(self, statement_id, entity_type):
        with self.get_db_connection() as conn:
            defaults = []
            defaults.extend(
                filter(
                    None,
                    [
                        self.get_first_child_account_id(conn, "balance_general", entity_type, "ACTIVOS"),
                        self.get_first_child_account_id(conn, "balance_general", entity_type, "PASIVOS"),
                        self.get_first_child_account_id(conn, "estado_resultados", entity_type, "INGRESOS"),
                        self.get_first_child_account_id(conn, "estado_resultados", entity_type, "COSTOS"),
                        self.get_first_child_account_id(conn, "estado_resultados", entity_type, "GASTOS"),
                    ],
                )
            )

            if entity_type == "juridica":
                patrimonio_defaults = self.get_account_ids_by_names(
                    conn,
                    "balance_general",
                    entity_type,
                    "PATRIMONIO",
                    [
                        "CAPITAL SOCIAL AUTORIZADO",
                        "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL",
                        "BENEFICIO O PERDIDA DE EJERCICIOS ANTERIORES",
                    ],
                )
                if not patrimonio_defaults:
                    patrimonio_defaults = self.get_account_ids_by_names(
                        conn,
                        "balance_general",
                        entity_type,
                        "PATRIMONIO",
                        [
                            "CAPITAL SUSCRITO Y PAGADO",
                            "BENEFICIO (PERDIDA) DEL EJERCICIO ACTUAL",
                            "BENEFICIOS (PERDIDAS) DE EJERCICIOS ANTERIORES",
                        ],
                    )
                defaults.extend(patrimonio_defaults)
            else:
                patrimonio_default = self.get_first_child_account_id(conn, "balance_general", entity_type, "PATRIMONIO")
                if patrimonio_default:
                    defaults.append(patrimonio_default)

            defaults.extend(self.get_custom_default_account_ids(conn, "balance_general", entity_type))
            defaults.extend(self.get_custom_default_account_ids(conn, "estado_resultados", entity_type))

            for account_id in dict.fromkeys(defaults):
                self.ensure_account_with_required_descendants(conn, statement_id, account_id)

    def get_statement_line_items(self, statement_id):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT account_id, amount
                FROM statement_line_items
                WHERE statement_id = ?
                """,
                (statement_id,),
            ).fetchall()
        return {row["account_id"]: row["amount"] for row in rows}

    def get_accounts_for_statement(self, statement_type, entity_type):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, statement_type, entity_type, root_group, parent_id, code, name, level, sort_order
                FROM account_catalog
                WHERE statement_type = ? AND entity_type = ?
                ORDER BY level, sort_order, name
                """,
                (statement_type, entity_type),
            ).fetchall()
        return [dict(row) for row in rows]

    def refresh_statement_account_selector(self):
        if not hasattr(self, "statement_account_selector"):
            return

        entity_type = self.statement_entity_type_var.get() or "juridica"
        statement_type = self.statement_target_var.get() or "balance_general"
        accounts = self.get_accounts_for_statement(statement_type, entity_type)

        self.statement_account_map = {}
        options = []
        for account in accounts:
            if account.get("level", 0) == 0:
                continue
            if account.get("id") in self.statement_selected_account_ids:
                continue
            label = account.get("name", "")
            code = account.get("code", "").strip()
            if code:
                label = f"{code} - {label}"
            self.statement_account_map[label] = account["id"]
            options.append(label)

        self.statement_account_selector["values"] = options
        self.statement_account_var.set(options[0] if options else "")

    def load_or_create_statement(self):
        payload = self.validate_statement_header()
        if not payload:
            return

        try:
            self.init_database()
            self.statement_id = self.get_or_create_statement_header(
                client_id=payload["client_id"],
                entity_type=payload["entity_type"],
                fiscal_year=payload["fiscal_year"],
                statement_date=payload["statement_date"],
            )
            self.ensure_default_statement_accounts(self.statement_id, payload["entity_type"])
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo cargar el estado.\n\nDetalle: {e}")
            return

        client_name = payload["client"].get("name", "Sin nombre")
        if hasattr(self, "statement_status_summary"):
            self.statement_status_summary.config(text=f"{client_name} / {payload['fiscal_year']}")
        if hasattr(self, "statement_helper_label"):
            self.statement_helper_label.config(
                text="Agrega cuentas si necesitas más detalle y luego escribe los valores directamente en los estados."
            )
        self.refresh_statement_history()
        self.render_statement_views()
        self.update_statement_layout()

    def add_selected_account_to_statement(self):
        if not self.statement_id:
            messagebox.showwarning("Aviso", "Primero carga o crea un estado.")
            return

        label = self.statement_account_var.get().strip()
        account_id = self.statement_account_map.get(label)
        if not account_id:
            messagebox.showwarning("Aviso", "Selecciona una cuenta para agregar.")
            return

        with self.get_db_connection() as conn:
            self.ensure_account_with_required_descendants(conn, self.statement_id, account_id)

        self.render_statement_views()
        self.update_statement_layout()

    def add_selected_account_as_default(self):
        label = self.statement_account_var.get().strip()
        account_id = self.statement_account_map.get(label)
        if not account_id:
            messagebox.showwarning("Aviso", "Selecciona una cuenta para guardar como predeterminada.")
            return

        statement_type = self.statement_target_var.get() or "balance_general"
        entity_type = self.statement_entity_type_var.get() or "juridica"

        with self.get_db_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO statement_default_accounts (id, statement_type, entity_type, account_id)
                VALUES (?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), statement_type, entity_type, account_id),
            )

        if self.statement_id:
            with self.get_db_connection() as conn:
                self.ensure_account_with_required_descendants(conn, self.statement_id, account_id)
            self.render_statement_views()
        else:
            self.refresh_statement_account_selector()
        self.update_statement_layout()

        messagebox.showinfo("Predeterminada", "La cuenta fue agregada a las cuentas por defecto.")

    def render_statement_views(self):
        if not hasattr(self, "balance_general_body") or not hasattr(self, "estado_resultados_body"):
            return

        self.statement_value_vars = {"balance_general": {}, "estado_resultados": {}}
        self.statement_total_labels = {"balance_general": {}, "estado_resultados": {}}
        self.statement_direct_amounts = {"balance_general": {}, "estado_resultados": {}}
        self.statement_summary_labels = {}

        if not self.statement_id:
            self.statement_selected_account_ids = set()
            self._render_empty_statement_section(self.balance_general_body, "Carga un estado para ver el balance general.")
            self._render_empty_statement_section(
                self.estado_resultados_body,
                "Carga un estado para ver el estado de resultados.",
            )
            self.refresh_statement_account_selector()
            self.update_statement_layout()
            return

        line_items = self.get_statement_line_items(self.statement_id)
        self.statement_selected_account_ids = set(line_items.keys())
        entity_type = self.statement_entity_type_var.get() or "juridica"

        self._render_statement_section(
            self.balance_general_body,
            statement_type="balance_general",
            entity_type=entity_type,
            line_items=line_items,
        )
        self._render_statement_section(
            self.estado_resultados_body,
            statement_type="estado_resultados",
            entity_type=entity_type,
            line_items=line_items,
        )
        self.refresh_statement_account_selector()
        self.update_statement_layout()

    def _render_empty_statement_section(self, container, message):
        for widget in container.winfo_children():
            widget.destroy()
        ttk.Label(container, text=message, style="Body.TLabel").grid(row=0, column=0, sticky="w")

    def _render_statement_section(self, container, *, statement_type, entity_type, line_items):
        for widget in container.winfo_children():
            widget.destroy()

        accounts = self.get_accounts_for_statement(statement_type, entity_type)
        account_by_id = {account["id"]: account for account in accounts}
        children_by_parent = {}
        for account in accounts:
            children_by_parent.setdefault(account.get("parent_id"), []).append(account)

        visible_ids = set()
        for account in accounts:
            if account.get("level", 0) == 0:
                visible_ids.add(account["id"])

        selected_ids = {account_id for account_id in line_items if account_id in account_by_id}
        for account_id in selected_ids:
            current_id = account_id
            while current_id:
                visible_ids.add(current_id)
                current = account_by_id.get(current_id)
                current_id = current.get("parent_id") if current else None
            descendant_id = account_id
            visited = set()
            while descendant_id and descendant_id not in visited:
                visited.add(descendant_id)
                visible_ids.add(descendant_id)
                next_children = children_by_parent.get(descendant_id, [])
                descendant_id = next_children[0]["id"] if next_children else None

        roots = [account for account in accounts if account.get("level", 0) == 0]
        row_index = 0
        for root in roots:
            row_index = self._render_statement_account_rows(
                container,
                account=root,
                children_by_parent=children_by_parent,
                visible_ids=visible_ids,
                selected_ids=selected_ids,
                line_items=line_items,
                statement_type=statement_type,
                row_index=row_index,
            )

        self.recalculate_statement_totals(statement_type, children_by_parent)
        if statement_type == "estado_resultados":
            summary_row = ttk.Frame(container, style="AltCard.TFrame", padding=(14, 10))
            summary_row.grid(row=row_index, column=0, sticky="ew", pady=(8, 0))
            summary_row.grid_columnconfigure(0, weight=1)
            ttk.Label(summary_row, text="BENEFICIO ANTES DE IMPUESTOS", style="Section.TLabel").grid(
                row=0,
                column=0,
                sticky="w",
            )
            summary_label = ttk.Label(summary_row, text="0.00", style="CardValue.TLabel")
            summary_label.grid(row=0, column=1, sticky="e")
            self.statement_summary_labels["beneficio_antes_impuestos"] = summary_label
            self.recalculate_statement_totals(statement_type, children_by_parent)

    def _render_statement_account_rows(
        self,
        container,
        *,
        account,
        children_by_parent,
        visible_ids,
        selected_ids,
        line_items,
        statement_type,
        row_index,
    ):
        account_id = account["id"]
        if account_id not in visible_ids:
            return row_index

        row = ttk.Frame(container, style="AltCard.TFrame", padding=(14, 10))
        row.grid(row=row_index, column=0, sticky="ew", pady=(0, 6))
        row.grid_columnconfigure(0, weight=1)

        title = account.get("name", "")
        code = account.get("code", "").strip()
        display_name = f"{code} {title}".strip() if code else title
        indent = max(0, int(account.get("level", 0))) * 18

        ttk.Label(
            row,
            text=display_name,
            style="Section.TLabel" if account.get("level", 0) == 0 else "Body.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(indent, 12))

        if account_id in selected_ids and account.get("level", 0) > 0 and not self.is_auto_statement_account(
            account,
            statement_type,
        ):
            amount = line_items.get(account_id)
            formatted = "" if amount is None else self.format_statement_amount(amount)
            var = tk.StringVar(value=formatted)
            var.trace_add(
                "write",
                lambda *_args, current_statement=statement_type: self.recalculate_statement_totals(
                    current_statement
                ),
            )
            self.statement_value_vars[statement_type][account_id] = var
            entry = ttk.Entry(row, textvariable=var, font=("Segoe UI", 10), justify="right", width=18)
            entry.grid(row=0, column=1, sticky="e")
        else:
            value_label = ttk.Label(row, text="0.00", style="CardValue.TLabel")
            value_label.grid(row=0, column=1, sticky="e")
            self.statement_total_labels[statement_type][account_id] = value_label

        row_index += 1
        for child in children_by_parent.get(account_id, []):
            row_index = self._render_statement_account_rows(
                container,
                account=child,
                children_by_parent=children_by_parent,
                visible_ids=visible_ids,
                selected_ids=selected_ids,
                line_items=line_items,
                statement_type=statement_type,
                row_index=row_index,
            )
        return row_index

    def parse_statement_amount(self, raw_value):
        cleaned = raw_value.strip().replace(",", "")
        if not cleaned:
            return 0.0
        return float(cleaned)

    def format_statement_amount(self, amount):
        return f"{float(amount):,.2f}"

    def is_auto_statement_account(self, account, statement_type):
        return (
            statement_type == "balance_general"
            and account.get("name") == "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL"
        )

    def get_statement_account_id_by_name(self, statement_type, entity_type, account_name):
        for account in self.get_accounts_for_statement(statement_type, entity_type):
            if account.get("name") == account_name:
                return account.get("id")
        return None

    def recalculate_statement_totals(self, statement_type, children_by_parent=None):
        entity_type = self.statement_entity_type_var.get() or "juridica"
        if children_by_parent is None:
            accounts = self.get_accounts_for_statement(statement_type, entity_type)
            children_by_parent = {}
            for account in accounts:
                children_by_parent.setdefault(account.get("parent_id"), []).append(account)

        def walk(account):
            account_id = account["id"]
            total = 0.0
            if account_id in self.statement_value_vars.get(statement_type, {}):
                try:
                    total += self.parse_statement_amount(self.statement_value_vars[statement_type][account_id].get())
                except ValueError:
                    total += 0.0
            total += self.statement_direct_amounts.get(statement_type, {}).get(account_id, 0.0)

            for child in children_by_parent.get(account_id, []):
                total += walk(child)

            label = self.statement_total_labels.get(statement_type, {}).get(account_id)
            if label:
                label.config(text=self.format_statement_amount(total))
            return total

        root_totals = {}
        for account in self.get_accounts_for_statement(statement_type, entity_type):
            if account.get("level", 0) == 0:
                root_totals[account.get("name", "")] = walk(account)

        if statement_type == "estado_resultados":
            beneficio_antes_impuestos = (
                root_totals.get("INGRESOS", 0.0) - root_totals.get("COSTOS", 0.0) - root_totals.get("GASTOS", 0.0)
            )
            summary_label = self.statement_summary_labels.get("beneficio_antes_impuestos")
            if summary_label:
                summary_label.config(text=self.format_statement_amount(beneficio_antes_impuestos))

            balance_account_id = self.get_statement_account_id_by_name(
                "balance_general",
                entity_type,
                "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL",
            )
            if balance_account_id:
                self.statement_direct_amounts.setdefault("balance_general", {})[balance_account_id] = (
                    beneficio_antes_impuestos
                )
                if self.statement_total_labels.get("balance_general"):
                    self.recalculate_statement_totals("balance_general")

    def save_statement_values(self):
        if not self.statement_id:
            messagebox.showwarning("Aviso", "Primero carga o crea un estado.")
            return

        payload = self.validate_statement_header()
        if not payload:
            return

        try:
            updates = {}
            for statement_type, value_vars in self.statement_value_vars.items():
                for account_id, var in value_vars.items():
                    updates[account_id] = self.parse_statement_amount(var.get())
            balance_account_id = self.get_statement_account_id_by_name(
                "balance_general",
                payload["entity_type"],
                "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL",
            )
            if balance_account_id:
                updates[balance_account_id] = self.statement_direct_amounts.get("balance_general", {}).get(
                    balance_account_id,
                    0.0,
                )
        except ValueError:
            messagebox.showwarning("Aviso", "Hay valores no válidos. Usa solo números.")
            return

        with self.get_db_connection() as conn:
            conn.execute(
                """
                UPDATE statement_headers
                SET statement_date = ?, entity_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (payload["statement_date"], payload["entity_type"], self.statement_id),
            )
            for account_id, amount in updates.items():
                conn.execute(
                    """
                    UPDATE statement_line_items
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE statement_id = ? AND account_id = ?
                    """,
                    (amount, self.statement_id, account_id),
                )

        self.log(
            f"[INFO] Estados guardados para {payload['client'].get('name', 'Sin nombre')} / {payload['fiscal_year']}"
        )
        self.refresh_statement_history()
        messagebox.showinfo("Guardado", "Los valores del estado fueron guardados en la base de datos.")

    def get_statement_line_items_from_ui(self):
        if not self.statement_id:
            return {}

        line_items = self.get_statement_line_items(self.statement_id)
        for statement_type, value_vars in self.statement_value_vars.items():
            for account_id, var in value_vars.items():
                try:
                    line_items[account_id] = self.parse_statement_amount(var.get())
                except ValueError:
                    raise ValueError("Hay valores no validos. Usa solo numeros.")

        return line_items

    def build_statement_section_snapshot(self, *, statement_type, entity_type, line_items, extra_direct_amounts=None):
        accounts = self.get_accounts_for_statement(statement_type, entity_type)
        account_by_id = {account["id"]: account for account in accounts}
        children_by_parent = {}
        for account in accounts:
            children_by_parent.setdefault(account.get("parent_id"), []).append(account)

        visible_ids = {account["id"] for account in accounts if account.get("level", 0) == 0}
        selected_ids = {account_id for account_id in line_items if account_id in account_by_id}

        for account_id in selected_ids:
            current_id = account_id
            while current_id:
                visible_ids.add(current_id)
                current = account_by_id.get(current_id)
                current_id = current.get("parent_id") if current else None

            descendant_id = account_id
            visited = set()
            while descendant_id and descendant_id not in visited:
                visited.add(descendant_id)
                visible_ids.add(descendant_id)
                next_children = children_by_parent.get(descendant_id, [])
                descendant_id = next_children[0]["id"] if next_children else None

        direct_amounts = dict(extra_direct_amounts or {})
        rows = []
        root_totals = {}

        def walk(account):
            account_id = account["id"]
            total = 0.0
            row_data = None
            if account_id in visible_ids:
                row_data = {
                    "account_id": account_id,
                    "name": account.get("name", ""),
                    "code": account.get("code", "").strip(),
                    "level": account.get("level", 0),
                    "amount": 0.0,
                }
                rows.append(row_data)

            if account_id in line_items and line_items[account_id] is not None:
                total += float(line_items[account_id])
            total += float(direct_amounts.get(account_id, 0.0))

            for child in children_by_parent.get(account_id, []):
                total += walk(child)

            if row_data is not None:
                row_data["amount"] = total
            return total

        for account in accounts:
            if account.get("level", 0) == 0:
                root_totals[account.get("name", "")] = walk(account)

        return {
            "rows": rows,
            "root_totals": root_totals,
        }

    def build_statement_snapshot(self):
        if not self.statement_id:
            messagebox.showwarning("Aviso", "Primero carga o crea un estado.")
            return None

        payload = self.validate_statement_header()
        if not payload:
            return None

        try:
            line_items = self.get_statement_line_items_from_ui()
        except ValueError:
            messagebox.showwarning("Aviso", "Hay valores no validos. Usa solo numeros.")
            return None

        entity_type = payload["entity_type"]
        results_section = self.build_statement_section_snapshot(
            statement_type="estado_resultados",
            entity_type=entity_type,
            line_items=line_items,
        )

        beneficio_antes_impuestos = (
            results_section["root_totals"].get("INGRESOS", 0.0)
            - results_section["root_totals"].get("COSTOS", 0.0)
            - results_section["root_totals"].get("GASTOS", 0.0)
        )

        balance_benefit_id = self.get_statement_account_id_by_name(
            "balance_general",
            entity_type,
            "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL",
        )
        balance_extra = {}
        if balance_benefit_id:
            balance_extra[balance_benefit_id] = beneficio_antes_impuestos

        balance_section = self.build_statement_section_snapshot(
            statement_type="balance_general",
            entity_type=entity_type,
            line_items=line_items,
            extra_direct_amounts=balance_extra,
        )

        return {
            "statement_id": self.statement_id,
            "client": payload["client"],
            "client_id": payload["client_id"],
            "entity_type": entity_type,
            "entity_label": "Persona juridica" if entity_type == "juridica" else "Persona fisica",
            "fiscal_year": payload["fiscal_year"],
            "statement_date": payload["statement_date"],
            "balance_general": balance_section,
            "estado_resultados": results_section,
            "beneficio_antes_impuestos": beneficio_antes_impuestos,
        }

    def format_statement_preview_text(self, snapshot):
        lines = [
            "ESTADOS FINANCIEROS",
            "",
            f"Cliente: {snapshot['client'].get('name', 'Sin nombre')}",
            f"RNC/Cedula: {snapshot['client'].get('rnc', '').strip() or snapshot['client'].get('cedula', '').strip() or 'Sin dato'}",
            f"Tipo: {snapshot['entity_label']}",
            f"Ano fiscal: {snapshot['fiscal_year']}",
            f"Fecha: {snapshot['statement_date']}",
            "",
            "BALANCE GENERAL",
            "",
        ]

        for row in snapshot["balance_general"]["rows"]:
            prefix = "    " * int(row.get("level", 0))
            code = f"{row['code']} " if row.get("code") else ""
            lines.append(f"{prefix}{code}{row['name']}: {self.format_statement_amount(row['amount'])}")

        lines.extend(
            [
                "",
                "ESTADO DE RESULTADOS",
                "",
            ]
        )
        for row in snapshot["estado_resultados"]["rows"]:
            prefix = "    " * int(row.get("level", 0))
            code = f"{row['code']} " if row.get("code") else ""
            lines.append(f"{prefix}{code}{row['name']}: {self.format_statement_amount(row['amount'])}")

        lines.extend(
            [
                "",
                f"BENEFICIO ANTES DE IMPUESTOS: {self.format_statement_amount(snapshot['beneficio_antes_impuestos'])}",
            ]
        )
        return "\n".join(lines)

    def open_statement_preview(self):
        snapshot = self.build_statement_snapshot()
        if not snapshot:
            return

        if self.statement_preview_window and self.statement_preview_window.winfo_exists():
            self.statement_preview_window.destroy()

        window = tk.Toplevel(self.root)
        window.title("Vista previa de estados")
        window.geometry("900x700")
        window.minsize(720, 560)
        window.configure(bg=self.colors["bg"])
        window.transient(self.root)
        self.statement_preview_window = window

        container = ttk.Frame(window, style="Card.TFrame", padding=20)
        container.pack(fill="both", expand=True, padx=14, pady=14)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Vista previa del estado", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Revisa el contenido antes de generar el PDF. Desde aqui tambien puedes crearlo.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        preview_box = ttk.Frame(container, style="AltCard.TFrame", padding=12)
        preview_box.grid(row=1, column=0, sticky="nsew")
        preview_box.grid_rowconfigure(0, weight=1)
        preview_box.grid_columnconfigure(0, weight=1)

        preview_text = ScrolledText(
            preview_box,
            wrap=tk.WORD,
            bg=self.colors["log_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        preview_text.grid(row=0, column=0, sticky="nsew")
        preview_text.insert("1.0", self.format_statement_preview_text(snapshot))
        preview_text.configure(state="disabled")

        footer = ttk.Frame(container, style="Card.TFrame")
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)

        ttk.Button(
            footer,
            text="Cerrar",
            style="Secondary.TButton",
            command=window.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            footer,
            text="Generar PDF",
            style="Primary.TButton",
            command=lambda: self.generate_statement_pdf(snapshot=snapshot),
        ).grid(row=0, column=1, sticky="ew")

    def build_statement_pdf_filename(self, snapshot):
        client_name = self.sanitize_filename(snapshot["client"].get("name", "CLIENTE"))
        return f"ESTADOS_{snapshot['fiscal_year']}_{client_name}.pdf"

    def choose_statement_pdf_path(self, snapshot):
        initial_dir = snapshot["client"].get("pc_location", "").strip()
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = os.path.dirname(os.path.abspath(__file__))

        return filedialog.asksaveasfilename(
            title="Guardar PDF de estados",
            initialdir=initial_dir,
            initialfile=self.build_statement_pdf_filename(snapshot),
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

    def build_statement_pdf_lines(self, snapshot):
        lines = [
            "ESTADOS FINANCIEROS",
            "",
            f"Cliente: {snapshot['client'].get('name', 'Sin nombre')}",
            f"RNC/Cedula: {snapshot['client'].get('rnc', '').strip() or snapshot['client'].get('cedula', '').strip() or 'Sin dato'}",
            f"Tipo: {snapshot['entity_label']}",
            f"Ano fiscal: {snapshot['fiscal_year']}",
            f"Fecha: {snapshot['statement_date']}",
            "",
            "BALANCE GENERAL",
            "",
        ]

        for row in snapshot["balance_general"]["rows"]:
            prefix = "  " * int(row.get("level", 0))
            code = f"{row['code']} " if row.get("code") else ""
            lines.append(f"{prefix}{code}{row['name']} .... {self.format_statement_amount(row['amount'])}")

        lines.extend(["", "ESTADO DE RESULTADOS", ""])
        for row in snapshot["estado_resultados"]["rows"]:
            prefix = "  " * int(row.get("level", 0))
            code = f"{row['code']} " if row.get("code") else ""
            lines.append(f"{prefix}{code}{row['name']} .... {self.format_statement_amount(row['amount'])}")

        lines.extend(
            [
                "",
                f"BENEFICIO ANTES DE IMPUESTOS .... {self.format_statement_amount(snapshot['beneficio_antes_impuestos'])}",
            ]
        )
        return lines

    def _pdf_escape_text(self, value):
        text = str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return text.encode("latin-1", "replace")

    def write_simple_text_pdf(self, pdf_path, title, lines):
        wrapped_lines = []
        for line in lines:
            if not line:
                wrapped_lines.append("")
                continue
            wrapped_lines.extend(textwrap.wrap(line, width=92) or [""])

        lines_per_page = 48
        page_chunks = [
            wrapped_lines[index:index + lines_per_page]
            for index in range(0, len(wrapped_lines), lines_per_page)
        ] or [[]]

        objects = []

        def add_object(data):
            objects.append(data)
            return len(objects)

        catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
        add_object(b"<< /Type /Pages /Kids [] /Count 0 >>")

        page_ids = []
        content_ids = []
        font_id = None

        for chunk in page_chunks:
            content_lines = [b"BT", b"/F1 11 Tf", b"50 770 Td", b"14 TL"]
            for line in chunk:
                content_lines.append(b"(" + self._pdf_escape_text(line) + b") Tj")
                content_lines.append(b"T*")
            content_lines.append(b"ET")
            stream = b"\n".join(content_lines)
            content_id = add_object(
                b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
            )
            page_id = add_object(
                (
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Contents {content_id} 0 R /Resources << /Font << /F1 "
                    f"{len(objects) + 1} 0 R >> >> >>"
                ).encode("ascii")
            )
            content_ids.append(content_id)
            page_ids.append(page_id)

        font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids).encode("ascii")
        objects[1] = b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode("ascii") + b" >>"

        for index, page_id in enumerate(page_ids):
            content_id = content_ids[index]
            objects[page_id - 1] = (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ).encode("ascii")

        header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        offsets = []
        body = bytearray()

        for index, obj in enumerate(objects, start=1):
            offsets.append(len(header) + len(body))
            body.extend(f"{index} 0 obj\n".encode("ascii"))
            body.extend(obj)
            body.extend(b"\nendobj\n")

        xref_offset = len(header) + len(body)
        xref = bytearray()
        xref.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        xref.extend(b"0000000000 65535 f \n")
        for offset in offsets:
            xref.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

        trailer = (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")

        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(header)
            pdf_file.write(body)
            pdf_file.write(xref)
            pdf_file.write(trailer)

    def generate_statement_pdf(self, snapshot=None):
        snapshot = snapshot or self.build_statement_snapshot()
        if not snapshot:
            return

        pdf_path = self.choose_statement_pdf_path(snapshot)
        if not pdf_path:
            return

        try:
            self.write_simple_text_pdf(
                pdf_path,
                "Estados financieros",
                self.build_statement_pdf_lines(snapshot),
            )
            self.log(f"[OK] PDF de estados generado: {pdf_path}")
        except Exception as e:
            self.log(f"[ERROR] No se pudo generar el PDF de estados. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo generar el PDF de estados.\n\nDetalle: {e}")
            return

        messagebox.showinfo("PDF generado", f"El PDF fue creado correctamente.\n\n{pdf_path}")

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
            with self.get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, version, change_date, change_type, description, affects_macros, requires_manual_update
                    FROM fiscal_template_versions
                    ORDER BY change_date DESC, created_at DESC
                    """
                ).fetchall()
            self.fiscal_versions = [dict(row) for row in rows]
        except Exception:
            self.fiscal_versions = []
        self.refresh_fiscal_template_summary()

    def save_fiscal_version_to_db(self, payload):
        normalized = self.normalize_fiscal_version_record(payload)
        if not normalized:
            return False

        with self.get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO fiscal_template_versions (
                    id,
                    version,
                    change_date,
                    change_type,
                    description,
                    affects_macros,
                    requires_manual_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["id"],
                    normalized["version"],
                    normalized["change_date"],
                    normalized["change_type"],
                    normalized["description"],
                    normalized["affects_macros"],
                    normalized["requires_manual_update"],
                ),
            )
        return True

    def load_fiscal_buyers_from_db(self):
        try:
            with self.get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, name, purchase_date, expiration_date, email, price, channel
                    FROM fiscal_template_buyers
                    ORDER BY purchase_date DESC, created_at DESC
                    """
                ).fetchall()
            self.fiscal_buyers = [dict(row) for row in rows]
        except Exception:
            self.fiscal_buyers = []
        self.refresh_fiscal_template_summary()

    def save_fiscal_buyer_to_db(self, payload):
        normalized = self.normalize_fiscal_buyer_record(payload)
        if not normalized:
            return False

        with self.get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO fiscal_template_buyers (
                    id,
                    name,
                    purchase_date,
                    expiration_date,
                    email,
                    price,
                    channel
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    purchase_date = excluded.purchase_date,
                    expiration_date = excluded.expiration_date,
                    email = excluded.email,
                    price = excluded.price,
                    channel = excluded.channel
                """,
                (
                    normalized["id"],
                    normalized["name"],
                    normalized["purchase_date"],
                    normalized["expiration_date"],
                    normalized["email"],
                    normalized["price"],
                    normalized["channel"],
                ),
            )
        return True

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
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def ensure_table_columns(self, conn, table_name, column_definitions):
        existing_columns = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        for column_name, column_sql in column_definitions.items():
            if column_name in existing_columns:
                continue
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

    def init_database(self):
        with self.get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    rnc TEXT NOT NULL DEFAULT '',
                    pc_location TEXT NOT NULL DEFAULT '',
                    cedula TEXT NOT NULL DEFAULT '',
                    tss_class TEXT NOT NULL DEFAULT '',
                    resource_path TEXT NOT NULL DEFAULT '',
                    work_description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name COLLATE NOCASE)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NULL,
                    title TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    due_date TEXT NOT NULL,
                    due_time TEXT NOT NULL DEFAULT '',
                    urgency TEXT NOT NULL DEFAULT 'amarillo',
                    recurrence TEXT NOT NULL DEFAULT 'none',
                    status TEXT NOT NULL DEFAULT 'pending',
                    completed_at TEXT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_active_lookup
                ON tasks(status, due_date, due_time, urgency)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pomodoro_tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    completed_pomodoros INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_pomodoro_tasks_created
                ON pomodoro_tasks(created_at)
                """
            )
            self.ensure_table_columns(
                conn,
                "pomodoro_tasks",
                {
                    "completed_pomodoros": "INTEGER NOT NULL DEFAULT 0",
                    "created_at": "TEXT",
                    "updated_at": "TEXT",
                },
            )
            conn.execute("UPDATE pomodoro_tasks SET completed_pomodoros = COALESCE(completed_pomodoros, 0)")
            conn.execute("UPDATE pomodoro_tasks SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)")
            conn.execute("UPDATE pomodoro_tasks SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pomodoro_flows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pomodoro_flow_tasks (
                    flow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (flow_id, task_id),
                    FOREIGN KEY(flow_id) REFERENCES pomodoro_flows(id) ON DELETE CASCADE,
                    FOREIGN KEY(task_id) REFERENCES pomodoro_tasks(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pomodoro_flow_tasks_task ON pomodoro_flow_tasks(task_id)"
            )
            self.ensure_table_columns(
                conn,
                "tasks",
                {
                    "client_id": "TEXT NULL",
                    "notes": "TEXT NOT NULL DEFAULT ''",
                    "due_time": "TEXT NOT NULL DEFAULT ''",
                    "urgency": "TEXT NOT NULL DEFAULT 'amarillo'",
                    "recurrence": "TEXT NOT NULL DEFAULT 'none'",
                    "status": "TEXT NOT NULL DEFAULT 'pending'",
                    "completed_at": "TEXT NULL",
                    "created_at": "TEXT",
                    "updated_at": "TEXT",
                },
            )
            conn.execute("UPDATE tasks SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)")
            conn.execute("UPDATE tasks SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fiscal_template_versions (
                    id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    change_date TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affects_macros TEXT NOT NULL DEFAULT 'No',
                    requires_manual_update TEXT NOT NULL DEFAULT 'No',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_fiscal_template_versions_date
                ON fiscal_template_versions(change_date DESC, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fiscal_template_buyers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    purchase_date TEXT NOT NULL,
                    expiration_date TEXT NOT NULL,
                    email TEXT NOT NULL,
                    price REAL NOT NULL DEFAULT 3000,
                    channel TEXT NOT NULL DEFAULT 'desconocido',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.ensure_table_columns(
                conn,
                "fiscal_template_buyers",
                {
                    "price": "REAL NOT NULL DEFAULT 3000",
                    "channel": "TEXT NOT NULL DEFAULT 'desconocido'",
                },
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_fiscal_template_buyers_purchase
                ON fiscal_template_buyers(purchase_date DESC, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS account_catalog (
                    id TEXT PRIMARY KEY,
                    statement_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    root_group TEXT NOT NULL,
                    parent_id TEXT NULL,
                    code TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_system INTEGER NOT NULL DEFAULT 1,
                    is_editable INTEGER NOT NULL DEFAULT 1,
                    is_deletable INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(parent_id) REFERENCES account_catalog(id) ON DELETE CASCADE,
                    UNIQUE(statement_type, entity_type, parent_id, name)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_account_catalog_lookup
                ON account_catalog(statement_type, entity_type, root_group, parent_id, sort_order)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS statement_headers (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    statement_date TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
                    UNIQUE(client_id, fiscal_year)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS statement_line_items (
                    id TEXT PRIMARY KEY,
                    statement_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    amount REAL NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(statement_id) REFERENCES statement_headers(id) ON DELETE CASCADE,
                    FOREIGN KEY(account_id) REFERENCES account_catalog(id) ON DELETE CASCADE,
                    UNIQUE(statement_id, account_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_statement_line_items_lookup
                ON statement_line_items(statement_id, account_id)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS statement_default_accounts (
                    id TEXT PRIMARY KEY,
                    statement_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(account_id) REFERENCES account_catalog(id) ON DELETE CASCADE,
                    UNIQUE(statement_type, entity_type, account_id)
                )
                """
            )

            existing_count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            if existing_count == 0:
                legacy_clients = self.load_legacy_clients_from_config()
                if legacy_clients:
                    conn.executemany(
                        """
                        INSERT INTO clients (
                            id,
                            name,
                            rnc,
                            pc_location,
                            cedula,
                            tss_class,
                            resource_path,
                            work_description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                client["id"],
                                client["name"],
                                client["rnc"],
                                client["pc_location"],
                                client["cedula"],
                                client["tss_class"],
                                client["resource_path"],
                                client["work_description"],
                            )
                            for client in legacy_clients
                        ],
                    )

            self.migrate_account_catalog(conn)
            self.seed_default_account_catalog(conn)

    def migrate_account_catalog(self, conn):
        rename_pairs = [
            ("CAPITAL SUSCRITO Y PAGADO", "CAPITAL SOCIAL AUTORIZADO"),
            ("BENEFICIO (PERDIDA) DEL EJERCICIO ACTUAL", "BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL"),
            (
                "BENEFICIOS (PERDIDAS) DE EJERCICIOS ANTERIORES",
                "BENEFICIO O PERDIDA DE EJERCICIOS ANTERIORES",
            ),
        ]
        for old_name, new_name in rename_pairs:
            conn.execute(
                """
                UPDATE account_catalog
                SET name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE statement_type = 'balance_general'
                  AND entity_type = 'juridica'
                  AND root_group = 'PATRIMONIO'
                  AND name = ?
                """,
                (new_name, old_name),
            )

    def seed_default_account_catalog(self, conn):
        existing_count = conn.execute("SELECT COUNT(*) FROM account_catalog").fetchone()[0]
        if existing_count:
            return

        for catalog in self.get_default_account_catalog():
            for position, root_account in enumerate(catalog["roots"], start=1):
                self.insert_account_node(
                    conn,
                    root_account,
                    statement_type=catalog["statement_type"],
                    entity_type=catalog["entity_type"],
                    root_group=root_account["name"],
                    parent_id=None,
                    level=0,
                    sort_order=position,
                )

    def insert_account_node(
        self,
        conn,
        account,
        *,
        statement_type,
        entity_type,
        root_group,
        parent_id,
        level,
        sort_order,
    ):
        account_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO account_catalog (
                id,
                statement_type,
                entity_type,
                root_group,
                parent_id,
                code,
                name,
                level,
                sort_order,
                is_system,
                is_editable,
                is_deletable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                statement_type,
                entity_type,
                root_group,
                parent_id,
                account.get("code", ""),
                account["name"],
                level,
                sort_order,
                1 if account.get("is_system", True) else 0,
                1 if account.get("is_editable", True) else 0,
                1 if account.get("is_deletable", True) else 0,
            ),
        )

        for child_position, child in enumerate(account.get("children", []), start=1):
            self.insert_account_node(
                conn,
                child,
                statement_type=statement_type,
                entity_type=entity_type,
                root_group=root_group,
                parent_id=account_id,
                level=level + 1,
                sort_order=child_position,
            )

    def get_default_account_catalog(self):
        def account(name, code="", children=None, is_editable=True, is_deletable=True):
            return {
                "name": name,
                "code": code,
                "children": children or [],
                "is_system": True,
                "is_editable": is_editable,
                "is_deletable": is_deletable,
            }

        juridica_balance = [
            account(
                "ACTIVOS",
                children=[
                    account(
                        "ACTIVOS CORRIENTES",
                        code="1",
                        children=[
                            account("CAJAS Y BANCOS", code="1.1"),
                            account("CUENTAS POR COBRAR A CLIENTES", code="1.2"),
                            account("CUENTAS POR COBRAR A RELACIONADOS", code="1.3"),
                            account("OTRAS CUENTAS POR COBRAR", code="1.4"),
                            account("INVENTARIO DE MERCANCIAS O PRODUCTOS TERMINADOS", code="1.5"),
                            account("INVENTARIO DE MATERIA PRIMA", code="1.6"),
                            account("INVENTARIO DE PRODUCTOS EN PROCESO", code="1.7"),
                            account("OTROS INVENTARIOS", code="1.8"),
                            account("MERCANCIAS EN TRANSITO", code="1.9"),
                            account("GASTOS PAGADOS POR ADELANTADO", code="1.10"),
                            account("OTROS ACTIVOS CORRIENTES", code="1.11"),
                            account("DIVIDENDOS A CUENTA ENTREGADOS EN EL EJERCICIO", code="1.12"),
                        ],
                    ),
                    account(
                        "ACTIVOS FIJOS (*)",
                        code="2",
                        children=[
                            account("EDIFICACIONES (CATEGORIA I)", code="2.1"),
                            account(
                                "EDIFICACIONES DE EXPLOTACIONES AGROPECUARIAS (CATEGORIA I)",
                                code="2.2",
                            ),
                            account("AUTOMOVILES Y EQUIPOS (CATEGORIA 2)", code="2.3"),
                            account("OTROS ACTIVOS FIJOS DEPRECIABLES (CATEGORIA 3)", code="2.4"),
                            account(
                                "OTROS ACTIVOS FIJOS NO DEPRECIABLES (INCLUYE TERRENOS URBANOS)",
                                code="2.5",
                            ),
                            account(
                                "OTROS ACTIVOS FIJOS NO DEPRECIABLES (INCLUYE TERRENOS RURALES)",
                                code="2.6",
                            ),
                            account("REVALUACION DE ACTIVOS", code="2.7"),
                        ],
                    ),
                    account(
                        "INVERSIONES",
                        code="3",
                        children=[
                            account("DEPOSITOS", code="3.1"),
                            account("ACCIONES", code="3.2"),
                            account("OTRAS INVERSIONES", code="3.3"),
                        ],
                    ),
                    account(
                        "OTROS ACTIVOS",
                        code="4",
                        children=[
                            account("OTROS ACTIVOS NO AMORTIZABLES", code="4.1"),
                            account("IMPUESTO SOBRE LA RENTA DIFERIDO O ANTICIPADO", code="4.2"),
                            account("OTROS ACTIVOS AMORTIZABLES", code="4.3"),
                        ],
                    ),
                    account(
                        "PROVISIONES PARA RIESGOS Y GASTOS",
                        code="5",
                        children=[
                            account(
                                "DEPRECIACION ACUMULADA ACTIVOS FIJOS (CATEGORIA I)",
                                code="5.1",
                            ),
                            account(
                                "DEPRECIACION ACUMULADA ACTIVOS FIJOS EDIFICACIONES AGROPECUARIAS (CATEGORIA I)",
                                code="5.2",
                            ),
                            account(
                                "DEPRECIACION ACUMULADA ACTIVOS FIJOS (CATEGORIA 2)",
                                code="5.3",
                            ),
                            account(
                                "DEPRECIACION ACUMULADA ACTIVOS FIJOS (CATEGORIA 3)",
                                code="5.4",
                            ),
                            account("PARA CUENTAS INCOBRABLES", code="5.5"),
                            account("PROVISION DE INVENTARIO", code="5.6"),
                            account("OTRAS PROVISIONES", code="5.7"),
                        ],
                    ),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "PASIVOS",
                children=[
                    account(
                        "ACREEDORES A CORTO PLAZO",
                        code="7",
                        children=[
                            account("PRESTAMOS", code="7.1"),
                            account("CUENTAS POR PAGAR", code="7.2"),
                            account("IMPUESTOS POR PAGAR", code="7.3"),
                            account("OTRAS CUENTAS POR PAGAR", code="7.4"),
                            account("COBROS ANTICIPADOS", code="7.5"),
                            account("APORTES PARA FUTURA CAPITALIZACION", code="7.6"),
                        ],
                    ),
                    account(
                        "ACREEDORES A LARGO PLAZO",
                        code="8",
                        children=[
                            account("PRESTAMOS HIPOTECARIOS", code="8.1"),
                            account(
                                "PRESTAMOS COMERCIALES CON INSTITUCIONES FINANCIERAS LOCALES",
                                code="8.2",
                            ),
                            account(
                                "PRESTAMOS COMERCIALES CON INSTITUCIONES FINANCIERAS DEL EXTERIOR",
                                code="8.3",
                            ),
                            account("PRESTAMOS CON ENTIDADES RELACIONADAS LOCALES", code="8.4"),
                            account("PRESTAMOS CON ENTIDADES RELACIONADAS DEL EXTERIOR", code="8.5"),
                            account(
                                "PRESTAMOS CON ENTIDADES ACOGIDAS A REGIMENES ESPECIALES",
                                code="8.6",
                            ),
                            account("PRESTAMOS CON ORGANISMOS INTERNACIONALES", code="8.7"),
                            account("PRESTAMOS CON ACCIONISTAS", code="8.8"),
                        ],
                    ),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "PATRIMONIO",
                children=[
                    account("CAPITAL SOCIAL AUTORIZADO", code="10.1"),
                    account("RESERVA LEGAL", code="10.2"),
                    account("SUPERAVIT REVALUACION DE ACTIVOS", code="10.3"),
                    account("BENEFICIO O PERDIDA DE EJERCICIOS ANTERIORES", code="10.4"),
                    account("BENEFICIO O PERDIDA DEL EJERCICIO ACTUAL", code="10.5"),
                    account("OTRAS RESERVAS", code="10.6"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
        ]

        juridica_results = [
            account(
                "INGRESOS",
                children=[
                    account(
                        "INGRESOS POR OPERACIONES",
                        children=[
                            account("INGRESOS POR VENTAS LOCALES"),
                            account("INGRESOS POR EXPORTACIONES"),
                            account("DEVOLUCIONES EN VENTA (-)"),
                            account("DESCUENTO S/VENTA (-)"),
                            account("OTROS INGRESOS"),
                        ],
                    ),
                    account(
                        "INGRESOS FINANCIEROS",
                        children=[
                            account(
                                "INTERESES PERCIBIDOS POR INVERSIONES FINANCIERAS EN INSTITUCIONES REGULADAS"
                            ),
                            account(
                                "INTERESES PERCIBIDOS POR INVERSIONES FINANCIERAS EN INSTITUCIONES NO REGULADAS"
                            ),
                            account("POR DIVIDENDOS"),
                            account("INTERESES POR PRESTAMOS CON ENTIDADES RELACIONADAS"),
                            account("INTERESES POR PRESTAMOS CON ENTIDADES NO RELACIONADAS"),
                            account("OTROS INGRESOS FINANCIEROS"),
                        ],
                    ),
                    account(
                        "INGRESOS EXTRAORDINARIOS",
                        children=[
                            account("POR VENTAS DE ACTIVOS DEPRECIABLES"),
                            account("POR VENTAS DE BIENES DE CAPITAL"),
                            account("POR DIFERENCIAS POSITIVAS CAMBIARIAS"),
                            account("INGRESOS CORRESPONDIENTES A OTROS INGRESOS"),
                            account("OTROS INGRESOS EXTRAORDINARIOS"),
                        ],
                    ),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "COSTOS",
                children=[
                    account("Inventario Inicial", code="34"),
                    account("Compras Locales del Ejercicio", code="35"),
                    account("Compras en el Exterior del Ejercicio", code="36"),
                    account("ITBIS llevado al Costo", code="37"),
                    account("Inventario Final", code="38"),
                    account("Costo de Venta", code="39"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "GASTOS",
                children=[
                    account(
                        "GASTOS DE PERSONAL",
                        children=[
                            account("SUELDOS Y SALARIOS"),
                            account("RETRIBUCIONES COMPLEMENTARIAS"),
                            account("SEGUROS"),
                            account("APORTACION SEGUIRIDAD SOCIAL"),
                            account("APORTE INFOTEP"),
                            account("OTROS GASTOS DE PERSONAL"),
                        ],
                    ),
                    account("ITBIS PAGADOS EN PROPORCIONALIDAD"),
                    account(
                        "GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS",
                        children=[
                            account("HONORARIOS POR SERVICIOS PROFESIONALES (PER.FIS)"),
                            account("HONORARIOS POR SERVICIOS PROFESIONALES (PER.MOR)"),
                            account("HONORARIOS POR SERVICIOS DEL EXTERIOR (LEY 392-07)"),
                            account(
                                "HONORARIOS POR SERVICIOS DEL EXTERIOR (PERSONAS FISICAS Y MORALES)"
                            ),
                            account(
                                "SEGURIDAD, MENSAJERIA, TRANSPORTES Y OTROS SERVICIOS (PERSONAS FISICAS)"
                            ),
                            account(
                                "SEGURIDAD, MENSAJERIA, TRANSPORTES Y OTROS SERVICIOS (PERSONAS MORALES)"
                            ),
                            account("SUMINISTRO DE COMBUSTIBLE"),
                            account("OTROS GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS"),
                            account("ITBIS PAGADO EN PROPORCIONALIDAD"),
                        ],
                    ),
                    account(
                        "ARRENDAMIENTOS",
                        children=[
                            account("DE INMUEBLES (A PERSONAS FISICAS)"),
                            account("DE INMUEBLES (A PERSONA MORALES)"),
                            account("OTROS ARRENDAMIENTOS"),
                            account("ITBIS PAGADO EN PROPORCIONALIDAD"),
                        ],
                    ),
                    account(
                        "GASTOS DE ACTIVOS FIJOS",
                        children=[
                            account("DEPRECIACION CAT 1"),
                            account("DEPRECIACION CAT 2"),
                            account("DEPRECIACION CAT 3"),
                            account("REPARACION DE ACTIVOS CAT 1"),
                            account("REPARACION DE ACTIVOS CAT 2 Y 3"),
                            account("MANTENIMIENTO DE ACTIVOS FIJOS"),
                            account("AMORTIZACION BIENES INTANGIBLES"),
                            account("AMORTIZACION MEJORAS EN PROPIEDADES ARRENDADAS"),
                            account("ITBIS PAGADO EN PROPORCIONALIDAD"),
                        ],
                    ),
                    account(
                        "GASTOS DE REPRESENTACION",
                        children=[
                            account("RELACIONES PUBLICAS"),
                            account("PUBLICIDAD"),
                            account("VIAJES"),
                            account("DONACIONES"),
                            account("DONACINES A PROINDUSTRIA"),
                            account("OTROS GASTOS DE REPRESENTACION"),
                            account("PROMOCIONES"),
                            account("ITBIS PAGADOS EN PROPORCIONALIDAD"),
                        ],
                    ),
                    account(
                        "OTRAS DEDUCCIONES ADMITIDAS",
                        children=[
                            account("PRIMAS DE SEGURO"),
                            account("CUOTAS Y OTRAS CONTRIBUCIONES"),
                            account("DESTRUCCION AUTORIZADA POR LA DGII"),
                        ],
                    ),
                    account(
                        "GASTOS FINANCIEROS",
                        children=[
                            account("POR PRESTAMOS CON INSTITUCIONES FINANCIERAS LOCALES"),
                            account("POR PRESTAMOS CON ENTIDADES DEL EXTERIOR"),
                            account("POR PRESTAMOS CON ENTIDADES RELACIONADAS LOCALES"),
                            account("POR PRESTAMOS CON ENTIDADES RELACIONADAS DEL EXTERIOR"),
                            account("POR PRESTAMOS CON PERSONAS FISICAS"),
                            account("POR PRESTAMOS CON PERSONAS FISICAS RELACIONADAS LOCALES"),
                            account("POR PRESTAMOS CON PERSONA FISICA RELACIONADAS EN EL EXTERIOR"),
                            account(
                                "POR RETENCION DE IMPUESTO A LA EMISION DE CHEQUES Y PAGOS POR TRANSFERENCIAS ELECTRONICAS"
                            ),
                            account("POR PRESTAMOS POR ENTIDADES ACOGIDAS A REGIMENES ESPECIALES"),
                            account("OTROS GASTOS FINANCIEROS"),
                        ],
                    ),
                    account(
                        "GASTOS EXTRAORDINARIOS",
                        children=[
                            account("POR PERDIDAS EN VENTAS DE ACTIVOS DEPRECIABLES"),
                            account("POR PERDIDAS EN VENTAS DE BIENES DE CAPITAL"),
                            account("POR PERDIDAS POR CUENTAS INCOBRABLES"),
                            account("PROVISIONES CUENTAS INCOBRABLES"),
                            account("POR DIFERENCIA NEGATIVA CAMBIARIA"),
                            account("OTROS GASTOS EXTRAORDINARIOS"),
                            account("PROVISION DE INVENTARIOS"),
                            account("OTRAS PROVISIONES"),
                        ],
                    ),
                ],
                is_editable=False,
                is_deletable=False,
            ),
        ]

        fisica_balance = [
            account(
                "ACTIVOS",
                children=[
                    account("INMUEBLES URBANOS: SOLARES"),
                    account("INMUEBLES URBANOS: MEJORAS"),
                    account("INMUEBLES RURALES: TERRENOS"),
                    account("MEJORAS, INSTALACIONES CONTENIDAS EN TERRENOS RURALES"),
                    account("EXISTENCIA DE GANADO VACUNO, PORCINO, AVICOLA, ETC"),
                    account("EXISTENCIA DE PRODUCTOS AGRICOLAS Y FORESTALES"),
                    account("CAPITAL INVERTIDO COMO DUENO O SOCIO DE NEGOCIOS"),
                    account("ACCIONES QUE POSEEN EN COMPANIAS (VALOR NOMINAL)"),
                    account("TITULOS, BONOS, OTROS DEPOSITOS EN BANCOS O EN SU PODER"),
                    account("CREDITOS HIPOTECARIOS"),
                    account("VEHICULOS MOTOT: AUTOMOVILES"),
                    account("MOBILIARIO DE OFICINA, CONSULTORIO Y CORRIENTE"),
                    account("MOBILIARIO DE LA CASA"),
                    account("DINERO EN CAJA, CUENTAS DE AHORROS Y CORRIENTES"),
                    account("NAVES Y OTRAS EMBARCACIONES DE CUALQUIER TIPO"),
                    account("OTROS"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "PASIVOS",
                children=[
                    account("DEUDAS POR PRESTAMOS HIPOTECARIOS"),
                    account("DEUDAS POR PRESTAMOS PRENDARIOS"),
                    account("OTRAS DEUDAS"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "PATRIMONIO",
                children=[account("PATRIMONIO NETO DEL ANO")],
                is_editable=False,
                is_deletable=False,
            ),
        ]

        fisica_results = [
            account(
                "INGRESOS",
                children=[
                    account("INGRESOS POR VENTAS LOCALES"),
                    account("INGRESOS POR EXPORTACIONES"),
                    account("INGRESOS POR PRESTACION DE SERVICIOS"),
                    account("INGRESOS POR HONORARIOS PROFESIONALES"),
                    account("INGRESOS POR ALQUILER"),
                    account("OTROS INGRESOS"),
                    account("DEVOLUCIONES S/VENTAS"),
                    account("DESCUENTO S/VENTAS"),
                    account("INGRESOS POR SALARIOS"),
                    account(
                        "INTERESES POR INVERSIONES FINANCIERAS EN INSTITUCIONES REGULADAS POR LAS AUTORIDADES MONETARIAS"
                    ),
                    account(
                        "INTERESES POR INVERSIONES FINANCIERAS EN INSTITUCIONES NO REGULADAS POR LAS AUTORIDADES MONETARIAS"
                    ),
                    account("VENTAS DE BIENES DE CAPITAL"),
                    account("INGRESOS POR DIVIDENDOS"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "COSTOS",
                children=[
                    account("INVENTARIO INICIAL"),
                    account("COMPRAS LOCALES"),
                    account("COMPRAS EN EL EXTERIOR (IMPORTACIONES)"),
                    account("ITBIS LLEVADO AL COSTO"),
                    account("INVENTARIO FINAL"),
                ],
                is_editable=False,
                is_deletable=False,
            ),
            account(
                "GASTOS",
                children=[
                    account(
                        "GASTOS DE PERSONAL",
                        children=[
                            account("SUELDOS Y SALARIOS"),
                            account("RETRIBUCIONES COMPLEMENTARIAS"),
                            account("SEGUROS"),
                            account("APORTACION SEGUIRIDAD SOCIAL"),
                            account("APORTE INFOTEP"),
                            account("OTROS GASTOS DE PERSONAL"),
                        ],
                    ),
                    account(
                        "GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS",
                        children=[
                            account("HONORARIOS POR SERVICIOS PROFESIONALES"),
                            account("HONORARIOS POR SERVICIOS DEL EXTERIOR (LEY 392-07)"),
                            account(
                                "HONORARIOS POR SERVICIOS DEL EXTERIOR (PERSONAS FISICAS Y MORALES)"
                            ),
                            account("FACTURAS DE ENERGIA ELECTRICA"),
                            account("FACTURAS TELEFONICAS"),
                            account("SUMINISTRO DE COMBUSTIBLE"),
                            account("SEGURIDAD, MENSAJERIA Y TRANSPORTE"),
                            account("OTROS GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS"),
                        ],
                    ),
                    account(
                        "GASTOS DE ACTIVOS FIJOS",
                        children=[
                            account("DEPRECIACION CAT 1"),
                            account("DEPRECIACION CAT 2"),
                            account("DEPRECIACION CAT 3"),
                            account("REPARACION DE ACTIVOS CAT 1"),
                            account("REPARACION DE ACTIVOS CAT 2 Y 3"),
                            account("MANTENIMIENTO DE ACTIVOS FIJOS"),
                            account("AMORTIZACION BIENES INTANGIBLES"),
                            account("AMORTIZACION MEJORAS EN PROPIEDADES ARRENDADAS"),
                        ],
                    ),
                    account(
                        "GASTOS DE REPRESENTACION",
                        children=[
                            account("RELACIONES PUBLICAS"),
                            account("PUBLICIDAD"),
                            account("VIAJES"),
                            account("PROMOCIONES"),
                            account("OTROS GASTOS DE REPRESENTACION"),
                        ],
                    ),
                    account(
                        "OTRAS DEDUCCIONES ADMITIDAS",
                        children=[
                            account("PRIMAS DE SEGURO"),
                            account("CUOTAS Y OTRAS CONTRIBUCIONES"),
                            account("DESTRUCCION AUTORIZADA POR LA DGII"),
                        ],
                    ),
                ],
                is_editable=False,
                is_deletable=False,
            ),
        ]

        return [
            {
                "statement_type": "balance_general",
                "entity_type": "juridica",
                "roots": juridica_balance,
            },
            {
                "statement_type": "estado_resultados",
                "entity_type": "juridica",
                "roots": juridica_results,
            },
            {
                "statement_type": "balance_general",
                "entity_type": "fisica",
                "roots": fisica_balance,
            },
            {
                "statement_type": "estado_resultados",
                "entity_type": "fisica",
                "roots": fisica_results,
            },
        ]

    def load_legacy_clients_from_config(self):
        if not os.path.exists(self.config_path):
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []

        clients = data.get("clients", [])
        if not isinstance(clients, list):
            return []

        normalized_clients = []
        for client in clients:
            normalized = self.normalize_client_record(client)
            if normalized:
                normalized_clients.append(normalized)

        normalized_clients.sort(key=lambda item: item.get("name", "").lower())
        return normalized_clients

    def load_clients_from_db(self):
        try:
            with self.get_db_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT id, name, rnc, pc_location, cedula, tss_class, resource_path, work_description
                    FROM clients
                    ORDER BY name COLLATE NOCASE
                    """
                ).fetchall()
            self.clients = [dict(row) for row in rows]
        except Exception:
            self.clients = []
        self.update_home_dashboard()

    def save_client_to_db(self, payload):
        normalized = self.normalize_client_record(payload)
        if not normalized:
            return False

        with self.get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO clients (
                    id,
                    name,
                    rnc,
                    pc_location,
                    cedula,
                    tss_class,
                    resource_path,
                    work_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    rnc = excluded.rnc,
                    pc_location = excluded.pc_location,
                    cedula = excluded.cedula,
                    tss_class = excluded.tss_class,
                    resource_path = excluded.resource_path,
                    work_description = excluded.work_description,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    normalized["id"],
                    normalized["name"],
                    normalized["rnc"],
                    normalized["pc_location"],
                    normalized["cedula"],
                    normalized["tss_class"],
                    normalized["resource_path"],
                    normalized["work_description"],
                ),
            )
        return True

    def delete_client_from_db(self, client_id):
        with self.get_db_connection() as conn:
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))

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
        self.refresh_tasks_ui()
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
        self.load_tasks_from_db()
        self.log(f"[INFO] Cliente eliminado: {client.get('name', 'Sin nombre')}")
        self.prepare_new_client(show_form=False)
        self.refresh_clients_ui()
        self.refresh_tasks_ui()

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
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            folders = data.get("saved_folders", [])
            selected_folder = data.get("selected_output_folder", "")
            legacy_folder = data.get("output_folder", "")
            copy_source_pdf = data.get("copy_source_pdf", "")
            organizer_folder = data.get("organizer_folder", "")
            template_workbook_path = data.get("template_workbook_path", "")
            template_sheet_password = data.get("template_sheet_password", "")
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
            if isinstance(organizer_folder, str) and organizer_folder.strip():
                self.organizer_folder = organizer_folder
            if isinstance(template_workbook_path, str):
                self.template_workbook_path = template_workbook_path.strip()
            if isinstance(template_sheet_password, str):
                self.template_sheet_password_var.set(template_sheet_password)
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
            self.organizer_folder = ""
            self.template_workbook_path = ""
            self.template_sheet_password_var.set("")
            self.pomodoro_state = self.get_default_pomodoro_state()
            self.ensure_default_company_routes()
        self.load_clients_from_db()

    def save_config(self):
        data = {
            "output_folder": self.output_folder,
            "selected_output_folder": self.output_folder,
            "saved_folders": self.saved_folders,
            "company_route_mappings": self.company_route_mappings,
            "copy_source_pdf": self.copy_source_pdf,
            "organizer_folder": self.organizer_folder,
            "template_workbook_path": self.template_workbook_path,
            "template_sheet_password": self.template_sheet_password_var.get(),
            "pomodoro_settings": self.get_pomodoro_settings(),
            "pomodoro_state": self.get_serializable_pomodoro_state(),
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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

    def set_organizer_folder(self, folder, *, save=True):
        self.organizer_folder = folder if folder and os.path.isdir(folder) else ""
        self.update_organizer_summary()
        if save:
            self.save_config()

    def ensure_organizer_folder(self):
        if self.organizer_folder and os.path.isdir(self.organizer_folder):
            return True

        selected = self.choose_folder("Selecciona la carpeta con PDFs o JPG", self.organizer_folder)
        if not selected:
            self.organizer_log("[ABORTADO] No se seleccionó carpeta para organizar.")
            return False

        self.set_organizer_folder(selected)
        self.organizer_log(f"[INFO] Carpeta seleccionada: {selected}")
        return True

    def select_organizer_folder(self):
        selected = self.choose_folder("Selecciona la carpeta con PDFs o JPG", self.organizer_folder)
        if not selected:
            return

        self.set_organizer_folder(selected)
        self.organizer_log(f"[INFO] Carpeta seleccionada: {selected}")

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
        reader = PdfReader(pdf_path)
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
        return "\n".join(pages_text)

    def extract_ncf_and_razon_social(self, text):
        ncf_match = self.ncf_pattern.search(text)
        razon_match = self.razon_social_pattern.search(text)

        ncf = ncf_match.group(0).strip() if ncf_match else None
        razon_social = razon_match.group(1).strip() if razon_match else None
        if not razon_social:
            normalized_text = unicodedata.normalize("NFKD", text or "")
            normalized_text = "".join(char for char in normalized_text if not unicodedata.combining(char))
            fallback_match = re.search(
                r"Razon\s+Social\s+Cliente\s*[:\-]?\s*(.+)",
                normalized_text,
                re.IGNORECASE,
            )
            if fallback_match:
                razon_social = fallback_match.group(1).strip()
        return ncf, razon_social

    def sanitize_filename(self, value):
        clean = re.sub(r'[<>:"/\\|?*]', "_", value)
        clean = re.sub(r"\s+", " ", clean).strip(" .")
        return clean

    def parse_organizer_filename(self, file_name):
        name_root, extension = os.path.splitext(file_name)
        extension = extension.lower()
        if extension not in self.organizer_supported_extensions:
            return None

        match = self.organizer_name_pattern.match(name_root.strip())
        if not match:
            return None

        company = self.sanitize_filename(match.group("company"))
        month = match.group("month").lower()
        day = int(match.group("day"))

        if not company or day < 1 or day > 31:
            return None

        return {
            "company": company,
            "month": month,
            "month_number": self.organizer_month_map[month],
            "day": day,
            "extension": extension,
        }

    def build_organizer_target_name(self, company, day, extension):
        return f"{day:02d} {company}{extension}"

    def get_unique_name_for_folder(self, folder, desired_name, reserved_names):
        name_root, extension = os.path.splitext(desired_name)
        candidate = desired_name
        index = 1

        while candidate.lower() in reserved_names or os.path.exists(os.path.join(folder, candidate)):
            candidate = f"{name_root}_{index}{extension}"
            index += 1

        reserved_names.add(candidate.lower())
        return candidate

    def scan_organizer_folder(self):
        if not self.ensure_organizer_folder():
            messagebox.showwarning("Aviso", "Debes seleccionar una carpeta para analizar.")
            return

        try:
            folder_entries = []
            for name in os.listdir(self.organizer_folder):
                full_path = os.path.join(self.organizer_folder, name)
                if os.path.isfile(full_path) and os.path.splitext(name)[1].lower() in self.organizer_supported_extensions:
                    folder_entries.append(name)
        except Exception as e:
            self.organizer_log(f"[ERROR] No se pudo leer la carpeta. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo leer la carpeta seleccionada.\n\nDetalle: {e}")
            return

        if not folder_entries:
            self.organizer_scan_results = []
            self.refresh_organizer_tree()
            self.organizer_log("[INFO] No se encontraron archivos PDF/JPG/JPEG en la carpeta.")
            messagebox.showinfo("Sin archivos", "La carpeta no contiene archivos PDF, JPG o JPEG.")
            return

        parsed_items = []
        invalid_items = []
        for name in sorted(folder_entries, key=str.lower):
            full_path = os.path.join(self.organizer_folder, name)
            parsed = self.parse_organizer_filename(name)
            if not parsed:
                invalid_items.append(
                    {
                        "path": full_path,
                        "current_name": name,
                        "day": None,
                        "target_name": "",
                        "status": "Omitido",
                        "is_valid": False,
                    }
                )
                continue

            parsed_items.append(
                {
                    "path": full_path,
                    "current_name": name,
                    "company": parsed["company"],
                    "month": parsed["month"],
                    "month_number": parsed["month_number"],
                    "day": parsed["day"],
                    "extension": parsed["extension"],
                    "is_valid": True,
                }
            )

        parsed_items.sort(key=lambda item: (item["day"], item["company"].lower(), item["current_name"].lower()))
        originals_in_batch = {item["current_name"].lower() for item in parsed_items}
        reserved_names = {
            name.lower()
            for name in folder_entries
            if name.lower() not in originals_in_batch
        }

        results = []
        for item in parsed_items:
            desired_name = self.build_organizer_target_name(item["company"], item["day"], item["extension"])
            if desired_name.lower() == item["current_name"].lower():
                final_name = item["current_name"]
                reserved_names.add(final_name.lower())
                status = "Sin cambios"
            else:
                final_name = self.get_unique_name_for_folder(self.organizer_folder, desired_name, reserved_names)
                status = "Listo"

            item["target_name"] = final_name
            item["status"] = status
            results.append(item)

        results.extend(invalid_items)
        self.organizer_scan_results = results
        self.refresh_organizer_tree()

        valid_count = len(parsed_items)
        skipped_count = len(invalid_items)
        self.organizer_log(
            f"[INFO] Análisis completado: {valid_count} válidos y {skipped_count} omitidos en {self.organizer_folder}"
        )
        if skipped_count:
            self.organizer_log("[INFO] Algunos archivos no coinciden con el formato esperado: empresa mes día.")
        if not valid_count:
            messagebox.showwarning(
                "Sin coincidencias",
                "Se encontraron archivos compatibles, pero ninguno coincide con el formato esperado.\n\nEjemplo: Empresa mar 25.pdf",
            )

    def apply_organizer_renames(self):
        if not self.organizer_scan_results:
            self.scan_organizer_folder()
            if not self.organizer_scan_results:
                return

        valid_items = [item for item in self.organizer_scan_results if item.get("is_valid")]
        if not valid_items:
            messagebox.showwarning("Aviso", "No hay archivos válidos para renombrar.")
            return

        rename_items = [
            item for item in valid_items
            if item.get("target_name") and item["target_name"].lower() != item["current_name"].lower()
        ]

        for item in self.organizer_scan_results:
            if not item.get("is_valid"):
                self.organizer_log(f"[OMITIDO] {item['current_name']}: no coincide con el formato esperado.")

        if not rename_items:
            self.organizer_log("[INFO] No hubo cambios por aplicar; los archivos válidos ya estaban ordenados.")
            messagebox.showinfo("Sin cambios", "Los archivos válidos ya tienen el nombre final esperado.")
            return

        temp_moves = []
        try:
            for index, item in enumerate(rename_items, start=1):
                original_path = item["path"]
                temp_name = f"__tmp_organizer_{uuid.uuid4().hex}_{index}{item['extension']}"
                temp_path = os.path.join(self.organizer_folder, temp_name)
                os.replace(original_path, temp_path)
                temp_moves.append((item, temp_path, original_path))

            for item, temp_path, _original_path in temp_moves:
                final_path = os.path.join(self.organizer_folder, item["target_name"])
                os.replace(temp_path, final_path)
                item["path"] = final_path
                item["status"] = "Renombrado"
                self.organizer_log(f"[OK] {item['current_name']} -> {item['target_name']}")
                item["current_name"] = item["target_name"]

        except Exception as e:
            for item, temp_path, original_path in reversed(temp_moves):
                if os.path.exists(temp_path):
                    try:
                        os.replace(temp_path, original_path)
                    except Exception:
                        pass
            self.organizer_log(f"[ERROR] No se pudo completar el renombrado. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo completar el renombrado.\n\nDetalle: {e}")
            return

        self.scan_organizer_folder()
        messagebox.showinfo(
            "Proceso completado",
            f"Se renombraron {len(rename_items)} archivos correctamente.",
        )

    def build_proposal_name(self, variable_name, proposal_type="mensual"):
        clean_variable = self.sanitize_filename(variable_name.upper())
        if proposal_type == "renta":
            return f"PROPUESTA DE ASESORIA DE RENTA PARA {clean_variable}"
        return f"PROPUESTA DE ASESORIA PARA {clean_variable}"

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
        if not self.pdf_path:
            messagebox.showwarning("Aviso", "Primero selecciona un PDF.")
            return

        self.processed_count = 0
        if hasattr(self, "counter_label"):
            self.counter_label.config(text="Procesados: 0 / 1")
        self.update_progress(0, 1)
        self.log("[INFO] Iniciando procesamiento de 1 archivo...")

        file_name = os.path.basename(self.pdf_path)
        if hasattr(self, "current_file_label"):
            self.current_file_label.config(text=f"Archivo actual: {file_name}")
        self.root.update_idletasks()

        try:
            text = self.extract_text_from_pdf(self.pdf_path)
            ncf, razon_social = self.extract_ncf_and_razon_social(text)
            company_route = self.find_company_route_for_text(text)

            if not ncf or not razon_social:
                self.log(
                    f"[ABORTADO] {file_name}: faltan datos requeridos (NCF y/o Razon Social Cliente)."
                )
                if hasattr(self, "current_file_label"):
                    self.current_file_label.config(text="Archivo actual: -")
                messagebox.showerror(
                    "Proceso abortado",
                    "No se encontro NCF y/o Razon Social Cliente en el PDF. No se movio el archivo.",
                )
                return

            if not company_route:
                self.log(f"[ABORTADO] {file_name}: no coincide con ninguna empresa configurada.")
                if hasattr(self, "current_file_label"):
                    self.current_file_label.config(text="Archivo actual: -")
                messagebox.showerror(
                    "Empresa no detectada",
                    "No se encontro una empresa configurada en el PDF. Agrega la empresa al mapeo o revisa el nombre.",
                )
                return

            target_folder = company_route.get("folder", "").strip()
            if not target_folder:
                self.log(f"[ABORTADO] {file_name}: la empresa no tiene ruta configurada.")
                if hasattr(self, "current_file_label"):
                    self.current_file_label.config(text="Archivo actual: -")
                messagebox.showerror(
                    "Ruta pendiente",
                    f"La empresa {company_route.get('company', '')} no tiene ruta configurada.",
                )
                return

            os.makedirs(target_folder, exist_ok=True)

            base_name = self.sanitize_filename(f"{ncf}_{razon_social}")
            new_path = self.get_unique_target_path(target_folder, base_name)
            os.replace(self.pdf_path, new_path)
            self.output_folder = target_folder
            self.save_config()
            self.log(
                f"[OK] {file_name} -> {company_route.get('company', '')} / {os.path.basename(new_path)}"
            )

        except Exception as e:
            self.log(f"[ERROR] {file_name}: no se pudo leer/procesar. Detalle: {e}")
            if hasattr(self, "current_file_label"):
                self.current_file_label.config(text="Archivo actual: -")
            messagebox.showerror("Error", f"No se pudo procesar el PDF.\n\nDetalle: {e}")
            return

        self.processed_count = 1
        if hasattr(self, "counter_label"):
            self.counter_label.config(text="Procesados: 1 / 1")
        if hasattr(self, "current_file_label"):
            self.current_file_label.config(text="Archivo actual: -")
        self.update_progress(1, 1)
        self.update_summary()
        self.update_flow_preview()
        self.root.update_idletasks()

        self.log("[INFO] Proceso finalizado.")
        open_folder = messagebox.askyesno(
            "Completado",
            "El procesamiento del PDF ha terminado.\n\n¿Deseas abrir la carpeta destino?",
        )
        if open_folder:
            try:
                os.startfile(self.output_folder)
                self.log(f"[INFO] Carpeta abierta: {self.output_folder}")
            except Exception as e:
                self.log(f"[ERROR] No se pudo abrir la carpeta destino. Detalle: {e}")
                messagebox.showerror(
                    "Error",
                    f"No se pudo abrir la carpeta destino.\n\nDetalle: {e}",
                )

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

    def _on_template_password_change(self, *_args):
        self.save_config()

    def _on_template_date_change(self, *_args):
        self.update_template_summary()

    def update_template_summary(self):
        workbook_text = self.template_workbook_path or "(no seleccionado)"
        file_name = os.path.basename(self.template_workbook_path) if self.template_workbook_path else "Sin libro"
        formatted_date = self.template_date_var.get() or date.today().isoformat()

        if hasattr(self, "template_book_label"):
            self.template_book_label.config(text=f"Libro actual: {workbook_text}")
        if hasattr(self, "template_book_summary"):
            self.template_book_summary.config(text=file_name)
        if hasattr(self, "template_date_summary"):
            self.template_date_summary.config(text=formatted_date)

    def set_template_workbook_path(self, workbook_path, *, save=True):
        self.template_workbook_path = (workbook_path or "").strip()
        self.update_template_summary()
        if save:
            self.save_config()

    def choose_excel_file(self, title, initialdir=""):
        return filedialog.askopenfilename(
            title=title,
            initialdir=initialdir or "",
            filetypes=[("Excel files", "*.xlsx;*.xlsm"), ("All files", "*.*")],
        )

    def select_template_workbook(self):
        initial_dir = os.path.dirname(self.template_workbook_path) if self.template_workbook_path else ""
        selected = self.choose_excel_file("Selecciona el libro de Excel", initial_dir)
        if not selected:
            return

        self.set_template_workbook_path(selected)
        self.template_log(f"[INFO] Libro guardado: {selected}")

    def change_template_workbook(self):
        if not self.template_workbook_path:
            messagebox.showwarning("Aviso", "Primero escoge un libro de Excel.")
            return

        initial_dir = os.path.dirname(self.template_workbook_path)
        selected = self.choose_excel_file("Selecciona el nuevo libro de Excel", initial_dir)
        if not selected or selected == self.template_workbook_path:
            return

        previous = self.template_workbook_path
        self.set_template_workbook_path(selected)
        self.template_log(f"[INFO] Libro actualizado: {previous} -> {selected}")

    def ensure_template_workbook(self):
        if self.template_workbook_path and os.path.isfile(self.template_workbook_path):
            return True

        selected = self.choose_excel_file("Selecciona el libro de Excel", os.path.dirname(self.template_workbook_path))
        if not selected:
            self.template_log("[ABORTADO] No se selecciono un libro de Excel.")
            return False

        self.set_template_workbook_path(selected)
        self.template_log(f"[INFO] Libro guardado: {selected}")
        return True

    def open_template_workbook(self):
        if not self.ensure_template_workbook():
            messagebox.showwarning("Aviso", "Debes seleccionar un libro de Excel valido.")
            return

        try:
            os.startfile(self.template_workbook_path)
            self.template_log(f"[INFO] Libro abierto: {self.template_workbook_path}")
        except Exception as e:
            self.template_log(f"[ERROR] No se pudo abrir el libro. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el libro de Excel.\n\nDetalle: {e}")

    def run_template_excel_update(self, workbook_path, password, date_iso):
        if load_workbook is None:
            raise RuntimeError("openpyxl no esta instalado en este equipo.")

        extension = os.path.splitext(workbook_path)[1].lower()
        if extension not in {".xlsx", ".xlsm"}:
            raise RuntimeError("openpyxl solo admite libros .xlsx o .xlsm.")

        parsed_date = datetime.strptime(date_iso, "%Y-%m-%d")
        candidate_cells = ("AM1", "AN1", "AM5", "AN5")
        output_lines = []
        updated_count = 0
        keep_vba = extension == ".xlsm"

        workbook = load_workbook(workbook_path, keep_vba=keep_vba)
        try:
            for sheet_name in self.template_target_sheets:
                if sheet_name not in workbook.sheetnames:
                    output_lines.append(f"MISSING::{sheet_name}")
                    continue

                try:
                    sheet = workbook[sheet_name]
                    sheet.protection.sheet = False
                    for cell_address in candidate_cells:
                        sheet[cell_address].value = None

                    target_cell = random.choice(candidate_cells)
                    cell = sheet[target_cell]
                    cell.value = parsed_date
                    cell.number_format = "dd/mm/yyyy"
                    updated_font = copy(cell.font)
                    updated_font.color = "FFFFFFFF"
                    cell.font = updated_font

                    if password:
                        sheet.protection.set_password(password)
                    sheet.protection.sheet = True

                    updated_count += 1
                    output_lines.append(f"UPDATED::{sheet_name}::{target_cell}")
                except Exception as exc:
                    output_lines.append(f"ERROR::{sheet_name}::{exc}")

            if updated_count > 0:
                workbook.save(workbook_path)
        finally:
            workbook.close()

        return 0, output_lines

    def apply_date_to_template_workbook(self):
        selected_date = self.template_date_var.get().strip() or date.today().isoformat()
        password = self.template_sheet_password_var.get()

        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Aviso", "La fecha debe estar en formato AAAA-MM-DD.")
            return

        if not self.ensure_template_workbook():
            messagebox.showwarning("Aviso", "Debes seleccionar un libro de Excel valido.")
            return

        extension = os.path.splitext(self.template_workbook_path)[1].lower()
        if extension not in {".xlsx", ".xlsm"}:
            messagebox.showwarning(
                "Aviso",
                "Para esta funcion con openpyxl el libro debe ser .xlsx o .xlsm.",
            )
            return

        self.template_log(f"[INFO] Procesando libro: {self.template_workbook_path}")
        self.template_log(f"[INFO] Fecha a colocar: {selected_date}")

        try:
            return_code, output_lines = self.run_template_excel_update(
                self.template_workbook_path,
                password,
                selected_date,
            )
        except PermissionError:
            self.template_log(
                "[ERROR] El libro no se pudo guardar porque esta bloqueado o sin permisos de escritura."
            )
            messagebox.showerror(
                "Libro bloqueado",
                "No se pudo guardar el libro.\n\n"
                "Cierra el archivo en Excel si esta abierto, verifica que no este en solo lectura "
                "y espera a que OneDrive termine de sincronizar si lo esta usando.\n\n"
                f"Archivo:\n{self.template_workbook_path}",
            )
            return
        except Exception as e:
            self.template_log(f"[ERROR] No se pudo actualizar el libro. Detalle: {e}")
            messagebox.showerror("Error", f"No se pudo actualizar el libro de Excel.\n\nDetalle: {e}")
            return

        updated = 0
        missing = 0
        errors = 0
        for line in output_lines:
            if line.startswith("UPDATED::"):
                _, sheet_name, cell_address = line.split("::", 2)
                updated += 1
                self.template_log(f"[OK] {sheet_name}: fecha colocada en {cell_address}")
            elif line.startswith("MISSING::"):
                _, sheet_name = line.split("::", 1)
                missing += 1
                self.template_log(f"[AVISO] No se encontro la hoja: {sheet_name}")
            elif line.startswith("ERROR::"):
                _, sheet_name, detail = line.split("::", 2)
                errors += 1
                self.template_log(f"[ERROR] {sheet_name}: {detail}")
            else:
                self.template_log(line)

        if return_code != 0 and updated == 0:
            messagebox.showerror(
                "Error",
                "Excel no pudo completar la actualizacion del libro. Revisa el log para mas detalle.",
            )
            return

        self.update_template_summary()
        messagebox.showinfo(
            "Plantilla actualizada",
            f"Fecha aplicada: {selected_date}\n\nHojas actualizadas: {updated}\nHojas no encontradas: {missing}\nHojas con error: {errors}",
        )

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

        source_folder = os.path.dirname(self.copy_source_pdf)
        base_name = self.build_proposal_name(variable_name, proposal_type)
        target_path = self.get_unique_target_path(source_folder, base_name)

        try:
            shutil.copy2(self.copy_source_pdf, target_path)
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


