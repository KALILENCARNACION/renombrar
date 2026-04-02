# pip install PyPDF2

import json
import os
import re
import shutil
import sqlite3
import textwrap
import tkinter as tk
import uuid
from datetime import date
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from PyPDF2 import PdfReader


class PdfRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renombrador de PDF por NCF y Razon Social Cliente")
        self.root.geometry("1100x760")
        self.root.minsize(980, 700)
        self.root.configure(bg="#f4f1ea")
        self.logo_image = None

        self.pdf_path = ""
        self.output_folder = ""
        self.saved_folders = []
        self.copy_source_pdf = ""
        self.organizer_folder = ""
        self.organizer_scan_results = []
        self.copy_name_var = tk.StringVar()
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
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")
        self.processed_count = 0
        self.clients = []
        self.selected_client_id = None
        self.client_extra_visible = False
        self.statement_id = None
        self.statement_client_map = {}
        self.statement_account_map = {}
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
        self._configure_app_icon()
        self._configure_styles()
        self._build_ui()
        self._maximize_window()
        self.update_summary()
        self.update_flow_preview()

    def _configure_app_icon(self):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_logo.png")
        if not os.path.exists(logo_path):
            return

        try:
            self.logo_image = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(True, self.logo_image)
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

        notebook = ttk.Notebook(outer)
        notebook.grid(row=0, column=0, sticky="nsew")

        rename_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        rename_tab.grid_rowconfigure(2, weight=1)
        rename_tab.grid_columnconfigure(0, weight=1)
        rename_tab.grid_columnconfigure(1, weight=1)
        notebook.add(rename_tab, text="Renombrar PDF")

        copy_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        copy_tab.grid_rowconfigure(1, weight=1)
        copy_tab.grid_columnconfigure(0, weight=1)
        notebook.add(copy_tab, text="Copiar propuesta")

        organizer_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        organizer_tab.grid_rowconfigure(1, weight=1)
        organizer_tab.grid_columnconfigure(0, weight=1)
        organizer_tab.grid_columnconfigure(1, weight=1)
        notebook.add(organizer_tab, text="Organizar por fecha")

        clients_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        clients_tab.grid_rowconfigure(1, weight=1)
        clients_tab.grid_columnconfigure(0, weight=1)
        notebook.add(clients_tab, text="Clientes")

        states_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        states_tab.grid_rowconfigure(1, weight=1)
        states_tab.grid_columnconfigure(1, weight=1)
        notebook.add(states_tab, text="Estados")

        self._build_header(rename_tab)
        self._build_destinations(rename_tab)
        self._build_visual_flow(rename_tab)
        self._build_activity(rename_tab)
        self._build_copy_tab(copy_tab)
        self._build_organizer_tab(organizer_tab)
        self._build_clients_tab(clients_tab)
        self._build_states_tab(states_tab)

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

    def _build_destinations(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 16))
        panel.grid_columnconfigure(0, weight=1)

        ttk.Label(panel, text="Destino y acciones", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Administra carpetas guardadas y controla el flujo principal desde un solo panel.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(panel, text="Carpetas guardadas", style="Body.TLabel").grid(row=2, column=0, sticky="w")

        selector_row = ttk.Frame(panel, style="Card.TFrame")
        selector_row.grid(row=3, column=0, sticky="ew", pady=(6, 12))
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

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=5, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            actions,
            text="📄 Seleccionar PDF",
            style="Secondary.TButton",
            command=self.select_pdf,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            actions,
            text="➜ Procesar PDF",
            style="Primary.TButton",
            command=self.process_pdf,
        ).grid(row=0, column=1, sticky="ew")

        self.refresh_folder_selector()

    def _build_visual_flow(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(0, 16))
        panel.grid_columnconfigure(0, weight=1)

        ttk.Label(panel, text="Vista del flujo", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Resumen visual de entrada, cambio de nombre y carpeta de salida.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.flow_canvas = tk.Canvas(
            panel,
            height=290,
            highlightthickness=0,
            bg=self.colors["card"],
        )
        self.flow_canvas.grid(row=2, column=0, sticky="nsew")
        self.flow_canvas.bind("<Configure>", lambda _event: self.update_flow_preview())

    def _build_activity(self, parent):
        status_panel = ttk.Frame(parent, style="Card.TFrame", padding=22)
        status_panel.grid(row=2, column=0, columnspan=2, sticky="ew")
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

        ttk.Label(
            form_panel,
            text='Resultado: "PROPUESTA DE ASESORIA PARA NOMBRE.pdf"',
            style="Body.TLabel",
        ).grid(row=6, column=0, sticky="w")

        ttk.Button(
            form_panel,
            text="Crear copia renombrada",
            style="Primary.TButton",
            command=self.create_proposal_copy,
        ).grid(row=7, column=0, sticky="ew", pady=(18, 0))

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
        self.update_copy_summary()

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

    def _truncate_middle(self, text, limit=46):
        if not text:
            return ""
        if len(text) <= limit:
            return text
        half = (limit - 3) // 2
        return f"{text[:half]}...{text[-half:]}"

    def update_summary(self):
        pdf_name = os.path.basename(self.pdf_path) if self.pdf_path else "Ningun archivo"
        folder_name = self.output_folder if self.output_folder else "Sin carpeta"
        if hasattr(self, "pdf_summary"):
            self.pdf_summary.config(text=self._truncate_middle(pdf_name, 32))
        if hasattr(self, "folder_summary"):
            self.folder_summary.config(text=self._truncate_middle(folder_name, 36))

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
        target_folder = os.path.basename(self.output_folder.rstrip("/\\")) if self.output_folder else "Carpeta destino"
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

    def _on_copy_name_change(self, *_args):
        self.update_copy_summary()

    def update_copy_summary(self):
        source_name = os.path.basename(self.copy_source_pdf) if self.copy_source_pdf else "Sin archivo"
        folder_name = os.path.dirname(self.copy_source_pdf) if self.copy_source_pdf else ""
        variable_name = self.copy_name_var.get().strip() or "NOMBRE"
        preview_name = self.build_proposal_name(variable_name)

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

    def get_db_connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

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
            button.config(text="Copiar")

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

        return {
            "id": self.selected_client_id or str(uuid.uuid4()),
            "name": name,
            "rnc": rnc,
            "pc_location": pc_location,
            "cedula": cedula,
            "tss_class": tss_class,
            "resource_path": resource_path,
            "work_description": work_description,
        }

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

    def load_config(self):
        if not os.path.exists(self.config_path):
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
        except Exception:
            self.output_folder = ""
            self.saved_folders = []
            self.copy_source_pdf = ""
            self.organizer_folder = ""
        self.load_clients_from_db()

    def save_config(self):
        data = {
            "output_folder": self.output_folder,
            "selected_output_folder": self.output_folder,
            "saved_folders": self.saved_folders,
            "copy_source_pdf": self.copy_source_pdf,
            "organizer_folder": self.organizer_folder,
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
        selected = filedialog.askopenfilename(
            title="Selecciona un archivo PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if selected:
            self.pdf_path = selected
            self.update_summary()
            self.update_flow_preview()
            self.log(f"[INFO] PDF seleccionado: {self.pdf_path}")

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

    def build_proposal_name(self, variable_name):
        clean_variable = self.sanitize_filename(variable_name.upper())
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

        if not self.ensure_output_folder():
            messagebox.showwarning("Aviso", "Debes seleccionar una carpeta destino para continuar.")
            return

        self.processed_count = 0
        self.counter_label.config(text="Procesados: 0 / 1")
        self.update_progress(0, 1)
        self.log("[INFO] Iniciando procesamiento de 1 archivo...")

        file_name = os.path.basename(self.pdf_path)
        self.current_file_label.config(text=f"Archivo actual: {file_name}")
        self.root.update_idletasks()

        try:
            text = self.extract_text_from_pdf(self.pdf_path)
            ncf, razon_social = self.extract_ncf_and_razon_social(text)

            if not ncf or not razon_social:
                self.log(
                    f"[ABORTADO] {file_name}: faltan datos requeridos (NCF y/o Razon Social Cliente)."
                )
                self.current_file_label.config(text="Archivo actual: -")
                messagebox.showerror(
                    "Proceso abortado",
                    "No se encontro NCF y/o Razon Social Cliente en el PDF. No se movio el archivo.",
                )
                return

            base_name = self.sanitize_filename(f"{ncf}_{razon_social}")
            new_path = self.get_unique_target_path(self.output_folder, base_name)
            os.replace(self.pdf_path, new_path)
            self.log(f"[OK] {file_name} -> {os.path.basename(new_path)}")

        except Exception as e:
            self.log(f"[ERROR] {file_name}: no se pudo leer/procesar. Detalle: {e}")
            self.current_file_label.config(text="Archivo actual: -")
            messagebox.showerror("Error", f"No se pudo procesar el PDF.\n\nDetalle: {e}")
            return

        self.processed_count = 1
        self.counter_label.config(text="Procesados: 1 / 1")
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
        if not variable_name:
            messagebox.showwarning("Aviso", "Escribe el nombre variable para crear la copia.")
            return

        if not self.ensure_copy_source_pdf():
            messagebox.showwarning("Aviso", "Debes seleccionar un PDF base para continuar.")
            return

        source_folder = os.path.dirname(self.copy_source_pdf)
        base_name = self.build_proposal_name(variable_name)
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
