# pip install PyPDF2

import json
import os
import re
import shutil
import tkinter as tk
import uuid
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
        self.copy_name_var = tk.StringVar()
        self.client_search_var = tk.StringVar()
        self.client_name_var = tk.StringVar()
        self.client_rnc_var = tk.StringVar()
        self.client_pc_location_var = tk.StringVar()
        self.client_cedula_var = tk.StringVar()
        self.client_tss_class_var = tk.StringVar()
        self.client_resource_path_var = tk.StringVar()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.processed_count = 0
        self.clients = []
        self.selected_client_id = None
        self.client_extra_visible = False

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

        self.load_config()
        self._configure_app_icon()
        self._configure_styles()
        self._build_ui()
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

        clients_tab = ttk.Frame(notebook, style="App.TFrame", padding=0)
        clients_tab.grid_rowconfigure(1, weight=1)
        clients_tab.grid_columnconfigure(0, weight=1)
        notebook.add(clients_tab, text="Clientes")

        self._build_header(rename_tab)
        self._build_destinations(rename_tab)
        self._build_visual_flow(rename_tab)
        self._build_activity(rename_tab)
        self._build_copy_tab(copy_tab)
        self._build_clients_tab(clients_tab)

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
            self.save_config()

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
        if existing:
            existing.update(payload)
            self.clients.sort(key=lambda item: item.get("name", "").lower())
            self.log(f"[INFO] Cliente actualizado: {payload['name']}")
        else:
            self.clients.append(payload)
            self.clients.sort(key=lambda item: item.get("name", "").lower())
            self.log(f"[INFO] Cliente agregado: {payload['name']}")

        self.selected_client_id = payload["id"]
        self.save_config()
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

        self.clients = [item for item in self.clients if item.get("id") != self.selected_client_id]
        self.log(f"[INFO] Cliente eliminado: {client.get('name', 'Sin nombre')}")
        self.save_config()
        self.prepare_new_client(show_form=False)
        self.refresh_clients_ui()

    def load_config(self):
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            folders = data.get("saved_folders", [])
            selected_folder = data.get("selected_output_folder", "")
            legacy_folder = data.get("output_folder", "")
            copy_source_pdf = data.get("copy_source_pdf", "")
            clients = data.get("clients", [])

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
            if isinstance(clients, list):
                normalized_clients = []
                for client in clients:
                    if not isinstance(client, dict):
                        continue
                    name = str(client.get("name", "")).strip()
                    if not name:
                        continue
                    normalized_clients.append(
                        {
                            "id": str(client.get("id") or uuid.uuid4()),
                            "name": name,
                            "rnc": str(client.get("rnc", "")).strip(),
                            "pc_location": str(client.get("pc_location", "")).strip(),
                            "cedula": str(client.get("cedula", "")).strip(),
                            "tss_class": str(client.get("tss_class", "")).strip(),
                            "resource_path": str(client.get("resource_path", "")).strip(),
                            "work_description": str(client.get("work_description", "")).strip(),
                        }
                    )
                self.clients = sorted(normalized_clients, key=lambda item: item.get("name", "").lower())
        except Exception:
            self.output_folder = ""
            self.saved_folders = []
            self.copy_source_pdf = ""
            self.clients = []

    def save_config(self):
        data = {
            "output_folder": self.output_folder,
            "selected_output_folder": self.output_folder,
            "saved_folders": self.saved_folders,
            "copy_source_pdf": self.copy_source_pdf,
            "clients": self.clients,
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
