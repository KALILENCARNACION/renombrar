from __future__ import annotations

import json
import re
import shutil
import sqlite3
import unicodedata
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader


NCF_PATTERN = re.compile(r"\b[A-Z]\d{12}\b")
RAZON_SOCIAL_PATTERN = re.compile(
    r"Raz[oó]n\s+Social\s+Cliente\s*[:\-]?\s*(.+)", re.IGNORECASE
)

ACTIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, rnc TEXT NOT NULL DEFAULT '',
    pc_location TEXT NOT NULL DEFAULT '', cedula TEXT NOT NULL DEFAULT '',
    tss_class TEXT NOT NULL DEFAULT '', resource_path TEXT NOT NULL DEFAULT '',
    work_description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS pomodoro_tasks (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, completed_pomodoros INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pomodoro_flows (
    id TEXT PRIMARY KEY, name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pomodoro_flow_tasks (
    flow_id TEXT NOT NULL, task_id TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (flow_id, task_id),
    FOREIGN KEY(flow_id) REFERENCES pomodoro_flows(id) ON DELETE CASCADE,
    FOREIGN KEY(task_id) REFERENCES pomodoro_tasks(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS fiscal_template_versions (
    id TEXT PRIMARY KEY, version TEXT NOT NULL, change_date TEXT NOT NULL,
    change_type TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
    affects_macros TEXT NOT NULL DEFAULT 'No', requires_manual_update TEXT NOT NULL DEFAULT 'No',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS fiscal_template_buyers (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, purchase_date TEXT NOT NULL,
    expiration_date TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
    price REAL NOT NULL DEFAULT 0, channel TEXT NOT NULL DEFAULT 'desconocido',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

REMOVED_TABLES = (
    "statement_line_items", "statement_default_accounts", "statement_headers",
    "account_catalog", "tasks",
)
REMOVED_CONFIG_KEYS = ("organizer_folder", "template_workbook_path", "template_sheet_password")


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(ACTIVE_SCHEMA)
            self._ensure_columns(connection, "fiscal_template_buyers", {
                "expiration_date": "TEXT NOT NULL DEFAULT ''",
                "email": "TEXT NOT NULL DEFAULT ''",
                "price": "REAL NOT NULL DEFAULT 0",
                "channel": "TEXT NOT NULL DEFAULT 'desconocido'",
                "created_at": "TEXT NOT NULL DEFAULT ''",
                "updated_at": "TEXT NOT NULL DEFAULT ''",
            })
            self._ensure_columns(connection, "pomodoro_flow_tasks", {
                "sort_order": "INTEGER NOT NULL DEFAULT 0",
            })

    def _ensure_columns(self, connection: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
        existing = {row["name"] for row in connection.execute(f'PRAGMA table_info("{table}")')}
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}')

    def remove_inactive_modules(self) -> None:
        with self.connect() as connection:
            for table in REMOVED_TABLES:
                connection.execute(f'DROP TABLE IF EXISTS "{table}"')


class ConfigService:
    DEFAULTS = {
        "selected_output_folder": "", "saved_folders": [], "company_route_mappings": [],
        "copy_source_pdf": "", "pomodoro_settings": {
            "auto_start_break": True, "auto_start_work": True,
        }, "pomodoro_state": {},
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
        result = dict(self.DEFAULTS)
        result.update(data)
        return result

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        cleaned = {key: value for key, value in data.items() if key not in REMOVED_CONFIG_KEYS}
        cleaned.pop("output_folder", None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
        return cleaned

    def update(self, changes: dict[str, Any]) -> dict[str, Any]:
        data = self.load()
        data.update(changes)
        return self.save(data)

    def remove_inactive_modules(self) -> dict[str, Any]:
        return self.save(self.load())


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).casefold().strip()


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]', " ", value or "")
    return re.sub(r"\s+", " ", value).strip(" .")


def unique_path(folder: str | Path, stem: str, suffix: str = ".pdf") -> Path:
    folder_path = Path(folder)
    candidate = folder_path / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = folder_path / f"{stem} ({counter}){suffix}"
        counter += 1
    return candidate


class ClientService:
    FIELDS = ("name", "rnc", "pc_location", "cedula", "tss_class", "resource_path", "work_description")

    def __init__(self, database: Database):
        self.database = database

    def list(self, search: str = "") -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM clients ORDER BY name COLLATE NOCASE").fetchall()
        clients = [dict(row) for row in rows]
        if search:
            needle = normalize_text(search)
            clients = [item for item in clients if needle in normalize_text(item["name"]) or needle in normalize_text(item["rnc"])]
        return clients

    def get(self, client_id: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ValueError("El nombre del cliente es obligatorio.")
        client_id = str(payload.get("id") or uuid.uuid4())
        values = [str(payload.get(field, "")).strip() for field in self.FIELDS]
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO clients (id,name,rnc,pc_location,cedula,tss_class,resource_path,work_description)
                VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,rnc=excluded.rnc,pc_location=excluded.pc_location,
                cedula=excluded.cedula,tss_class=excluded.tss_class,resource_path=excluded.resource_path,
                work_description=excluded.work_description,updated_at=CURRENT_TIMESTAMP""",
                (client_id, *values),
            )
        return self.get(client_id) or {}

    def delete(self, client_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        return cursor.rowcount > 0


class PdfService:
    def extract_text(self, path: str | Path) -> str:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def extract_fields(self, text: str) -> tuple[str, str]:
        ncf_match = NCF_PATTERN.search(text or "")
        social_match = RAZON_SOCIAL_PATTERN.search(text or "")
        social = social_match.group(1).splitlines()[0].strip() if social_match else ""
        return (ncf_match.group(0) if ncf_match else "", social)

    def analyze(self, paths: list[str], routes: list[dict[str, Any]], default_folder: str = "") -> list[dict[str, Any]]:
        results = []
        for raw_path in paths:
            path = Path(raw_path)
            item: dict[str, Any] = {"source": str(path), "status": "ready"}
            try:
                if path.suffix.lower() != ".pdf" or not path.is_file():
                    raise ValueError("La ruta no corresponde a un PDF existente.")
                text = self.extract_text(path)
                ncf, company = self.extract_fields(text)
                if not ncf or not company:
                    raise ValueError("No se encontró NCF o Razón Social Cliente.")
                normalized_text = normalize_text(text)
                matching_routes = [
                    r for r in routes
                    if r.get("active", True)
                    and normalize_text(r.get("company", ""))
                    and normalize_text(r.get("company", "")) in normalized_text
                ]
                matching_routes.sort(key=lambda r: len(normalize_text(r.get("company", ""))), reverse=True)
                route = matching_routes[0] if matching_routes else None
                destination = str(route.get("folder", "")) if route else default_folder
                if not destination:
                    raise ValueError("No hay carpeta de destino para este cliente.")
                item.update(
                    ncf=ncf,
                    company=company,
                    route_company=str(route.get("company", "")) if route else "Destino general",
                    destination=destination,
                    proposed_name=f"{sanitize_filename(ncf + '_' + company)}.pdf",
                )
            except Exception as exc:
                item.update(status="error", error=str(exc))
            results.append(item)
        return results

    def execute(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for item in items:
            result = dict(item)
            try:
                if item.get("status") == "error":
                    raise ValueError(str(item.get("error", "Elemento inválido.")))
                source = Path(str(item["source"]))
                folder = Path(str(item["destination"]))
                folder.mkdir(parents=True, exist_ok=True)
                stem = Path(str(item["proposed_name"])).stem
                target = unique_path(folder, stem, ".pdf")
                shutil.move(str(source), target)
                result.update(status="completed", target=str(target))
            except Exception as exc:
                result.update(status="error", error=str(exc))
            results.append(result)
        return results


class ProposalService:
    def preview(self, variable_name: str, proposal_type: str = "mensual") -> str:
        name = sanitize_filename(variable_name.upper())
        if not name:
            raise ValueError("El nombre variable es obligatorio.")
        prefix = "PROPUESTA DE ASESORIA DE RENTA PARA" if proposal_type == "renta" else "PROPUESTA DE ASESORIA PARA"
        return f"{prefix} {name}.pdf"

    def create(self, source: str, variable_name: str, proposal_type: str = "mensual") -> dict[str, str]:
        source_path = Path(source)
        if not source_path.is_file() or source_path.suffix.lower() != ".pdf":
            raise ValueError("El PDF base no existe.")
        filename = self.preview(variable_name, proposal_type)
        target = unique_path(source_path.parent, Path(filename).stem, ".pdf")
        shutil.copy2(source_path, target)
        return {"source": str(source_path), "target": str(target), "filename": target.name}


class FiscalService:
    def __init__(self, database: Database):
        self.database = database

    def versions(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM fiscal_template_versions ORDER BY change_date DESC, created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def save_version(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("version", "change_date", "change_type")
        if any(not str(payload.get(key, "")).strip() for key in required):
            raise ValueError("Versión, fecha y tipo de cambio son obligatorios.")
        item = {**payload, "id": str(payload.get("id") or uuid.uuid4())}
        with self.database.connect() as connection:
            connection.execute("""INSERT INTO fiscal_template_versions
                (id,version,change_date,change_type,description,affects_macros,requires_manual_update)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,
                change_date=excluded.change_date,change_type=excluded.change_type,description=excluded.description,
                affects_macros=excluded.affects_macros,requires_manual_update=excluded.requires_manual_update""",
                (item["id"], item["version"], item["change_date"], item["change_type"], item.get("description", ""),
                 item.get("affects_macros", "No"), item.get("requires_manual_update", "No")))
        return next(row for row in self.versions() if row["id"] == item["id"])

    def buyers(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM fiscal_template_buyers ORDER BY purchase_date DESC, name COLLATE NOCASE").fetchall()
        return [dict(row) for row in rows]

    def save_buyer(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not str(payload.get("name", "")).strip() or not str(payload.get("purchase_date", "")).strip():
            raise ValueError("Nombre y fecha de compra son obligatorios.")
        item = {**payload, "id": str(payload.get("id") or uuid.uuid4())}
        price = float(str(payload.get("price", 0)).replace(",", "") or 0)
        with self.database.connect() as connection:
            connection.execute("""INSERT INTO fiscal_template_buyers
                (id,name,purchase_date,expiration_date,email,price,channel) VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,purchase_date=excluded.purchase_date,
                expiration_date=excluded.expiration_date,email=excluded.email,price=excluded.price,
                channel=excluded.channel,updated_at=CURRENT_TIMESTAMP""",
                (item["id"], item["name"], item["purchase_date"], item.get("expiration_date", ""),
                 item.get("email", ""), price, item.get("channel", "desconocido")))
        return next(row for row in self.buyers() if row["id"] == item["id"])

    def summary(self) -> dict[str, Any]:
        buyers = self.buyers()
        gross = sum(float(row["price"] or 0) for row in buyers)
        net = gross / 1.18 if gross else 0
        return {"versions": len(self.versions()), "buyers": len(buyers), "gross_profit": gross, "net_profit": net}

    def message(self, buyer_name: str, message_type: str, email: str = "") -> str:
        labels = {"Plantilla fiscal": "la plantilla fiscal", "Actualizacion": "la actualización de la plantilla fiscal"}
        subject = labels.get(message_type, message_type.strip().lower() or "la plantilla fiscal")
        greeting = f"Hola {buyer_name.strip()}," if buyer_name.strip() else "Hola,"
        contact = f" Te estaremos contactando también en {email.strip()}." if email.strip() else ""
        return f"{greeting}\n\nGracias por adquirir {subject}.{contact}\n\nQuedamos atentos a cualquier pregunta."


class PomodoroService:
    DURATIONS = {"work": 25 * 60, "short_break": 5 * 60, "long_break": 15 * 60}

    def __init__(self, database: Database, config: ConfigService):
        self.database, self.config = database, config

    def _default_state(self) -> dict[str, Any]:
        return {"date": date.today().isoformat(), "completed_count": 0, "phase": "work",
                "remaining_seconds": self.DURATIONS["work"], "running": False,
                "phase_end_at": None, "ten_minute_alert_played": False,
                "selected_task_id": None, "selected_flow_id": None, "completed_task_ids": [], "flow_pomodoros": {}}

    def settings(self) -> dict[str, bool]:
        return self.config.load().get("pomodoro_settings") or {"auto_start_break": True, "auto_start_work": True}

    def update_settings(self, payload: dict[str, Any]) -> dict[str, bool]:
        settings = {"auto_start_break": bool(payload.get("auto_start_break", True)),
                    "auto_start_work": bool(payload.get("auto_start_work", True))}
        self.config.update({"pomodoro_settings": settings})
        return settings

    def state(self) -> dict[str, Any]:
        state = {**self._default_state(), **(self.config.load().get("pomodoro_state") or {})}
        if state["date"] != date.today().isoformat():
            state = self._default_state()
            self._save_state(state)
        if state.get("running") and state.get("phase_end_at"):
            remaining = max(0, int((datetime.fromisoformat(state["phase_end_at"]) - datetime.now()).total_seconds()))
            state["remaining_seconds"] = remaining
            if remaining == 0:
                finished_work = state["phase"] == "work"
                if finished_work:
                    state["completed_count"] += 1
                    if state.get("selected_task_id"):
                        self.increment_task(state["selected_task_id"])
                    if state.get("selected_flow_id"):
                        flow_pomodoros = state.get("flow_pomodoros") or {}
                        flow_id = state["selected_flow_id"]
                        flow_pomodoros[flow_id] = int(flow_pomodoros.get(flow_id, 0)) + 1
                        state["flow_pomodoros"] = flow_pomodoros
                    state["phase"] = "long_break" if state["completed_count"] % 4 == 0 else "short_break"
                else:
                    state["phase"] = "work"
                state["remaining_seconds"] = self.DURATIONS[state["phase"]]
                settings = self.settings()
                auto_start = settings["auto_start_break"] if finished_work else settings["auto_start_work"]
                state["running"] = auto_start
                state["phase_end_at"] = (
                    datetime.fromtimestamp(datetime.now().timestamp() + state["remaining_seconds"]).isoformat()
                    if auto_start else None
                )
                self._save_state(state)
        return state

    def _save_state(self, state: dict[str, Any]) -> dict[str, Any]:
        self.config.update({"pomodoro_state": state})
        return state

    def command(self, action: str) -> dict[str, Any]:
        state = self.state()
        if action == "start":
            state["running"] = True
            state["phase_end_at"] = datetime.fromtimestamp(datetime.now().timestamp() + int(state["remaining_seconds"])).isoformat()
        elif action == "pause":
            state["running"] = False
            state["phase_end_at"] = None
        elif action == "skip":
            if state["phase"] == "work":
                state["completed_count"] += 1
                if state.get("selected_flow_id"):
                    flow_pomodoros = state.get("flow_pomodoros") or {}
                    flow_id = state["selected_flow_id"]
                    flow_pomodoros[flow_id] = int(flow_pomodoros.get(flow_id, 0)) + 1
                    state["flow_pomodoros"] = flow_pomodoros
                state["phase"] = "long_break" if state["completed_count"] % 4 == 0 else "short_break"
            else:
                state["phase"] = "work"
            state["remaining_seconds"] = self.DURATIONS[state["phase"]]
            state["running"] = False
            state["phase_end_at"] = None
        elif action == "reset":
            state = self._default_state()
        else:
            raise ValueError("Acción de Pomodoro desconocida.")
        return self._save_state(state)

    def tasks(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM pomodoro_tasks ORDER BY created_at").fetchall()
        return [dict(row) for row in rows]

    def save_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("El título es obligatorio.")
        task_id = str(payload.get("id") or uuid.uuid4())
        count = max(0, int(payload.get("completed_pomodoros", 0)))
        with self.database.connect() as connection:
            connection.execute("""INSERT INTO pomodoro_tasks (id,title,completed_pomodoros) VALUES (?,?,?)
                ON CONFLICT(id) DO UPDATE SET title=excluded.title,completed_pomodoros=excluded.completed_pomodoros,
                updated_at=CURRENT_TIMESTAMP""", (task_id, title, count))
        return next(item for item in self.tasks() if item["id"] == task_id)

    def delete_task(self, task_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM pomodoro_tasks WHERE id=?", (task_id,))
        return cursor.rowcount > 0

    def select_task(self, task_id: str | None, flow_id: str | None = None) -> dict[str, Any]:
        state = self.state()
        if task_id:
            with self.database.connect() as connection:
                exists = connection.execute("SELECT 1 FROM pomodoro_tasks WHERE id=?", (task_id,)).fetchone()
            if not exists:
                raise ValueError("Tarea no encontrada.")
        if flow_id:
            with self.database.connect() as connection:
                exists = connection.execute("SELECT 1 FROM pomodoro_flows WHERE id=?", (flow_id,)).fetchone()
            if not exists:
                raise ValueError("Flujo no encontrado.")
        completed = set(state.get("completed_task_ids") or [])
        if task_id in completed:
            completed.remove(task_id)
            state["completed_task_ids"] = sorted(completed)
        state["selected_task_id"] = task_id
        state["selected_flow_id"] = flow_id
        return self._save_state(state)

    def complete_task(self, task_id: str, completed: bool) -> dict[str, Any]:
        with self.database.connect() as connection:
            exists = connection.execute("SELECT 1 FROM pomodoro_tasks WHERE id=?", (task_id,)).fetchone()
        if not exists:
            raise ValueError("Tarea no encontrada.")
        state = self.state()
        completed_ids = set(state.get("completed_task_ids") or [])
        if completed:
            completed_ids.add(task_id)
            if state.get("selected_task_id") == task_id:
                state["selected_task_id"] = None
        else:
            completed_ids.discard(task_id)
        state["completed_task_ids"] = sorted(completed_ids)
        return self._save_state(state)

    def increment_task(self, task_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute("""UPDATE pomodoro_tasks SET completed_pomodoros=completed_pomodoros+1,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""", (task_id,))

    def flows(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            flows = [dict(row) for row in connection.execute("SELECT * FROM pomodoro_flows ORDER BY created_at")]
            for flow in flows:
                flow["tasks"] = [dict(row) for row in connection.execute("""SELECT t.*,ft.completed,ft.sort_order FROM pomodoro_flow_tasks ft
                    JOIN pomodoro_tasks t ON t.id=ft.task_id WHERE ft.flow_id=? ORDER BY ft.sort_order,t.created_at""", (flow["id"],))]
        return flows

    def save_flow(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ValueError("El nombre del flujo es obligatorio.")
        flow_id = str(payload.get("id") or uuid.uuid4())
        with self.database.connect() as connection:
            connection.execute("""INSERT INTO pomodoro_flows(id,name) VALUES (?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,updated_at=CURRENT_TIMESTAMP""", (flow_id, name))
        return next(item for item in self.flows() if item["id"] == flow_id)

    def delete_flow(self, flow_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM pomodoro_flows WHERE id=?", (flow_id,))
        return cursor.rowcount > 0

    def assign(self, flow_id: str, task_id: str, assigned: bool) -> None:
        with self.database.connect() as connection:
            if assigned:
                next_order = connection.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM pomodoro_flow_tasks WHERE flow_id=?",
                    (flow_id,),
                ).fetchone()[0]
                connection.execute(
                    "INSERT OR IGNORE INTO pomodoro_flow_tasks(flow_id,task_id,sort_order) VALUES (?,?,?)",
                    (flow_id, task_id, next_order),
                )
                connection.execute("UPDATE pomodoro_flow_tasks SET completed=0 WHERE flow_id=? AND task_id=?", (flow_id, task_id))
            else:
                connection.execute("DELETE FROM pomodoro_flow_tasks WHERE flow_id=? AND task_id=?", (flow_id, task_id))

    def reorder(self, flow_id: str, task_ids: list[str]) -> None:
        with self.database.connect() as connection:
            existing = {
                row["task_id"] for row in connection.execute(
                    "SELECT task_id FROM pomodoro_flow_tasks WHERE flow_id=?",
                    (flow_id,),
                )
            }
            for index, task_id in enumerate(task_ids):
                if task_id in existing:
                    connection.execute(
                        "UPDATE pomodoro_flow_tasks SET sort_order=? WHERE flow_id=? AND task_id=?",
                        (index, flow_id, task_id),
                    )

    def complete(self, flow_id: str, task_id: str, completed: bool) -> None:
        with self.database.connect() as connection:
            connection.execute("UPDATE pomodoro_flow_tasks SET completed=? WHERE flow_id=? AND task_id=?",
                               (1 if completed else 0, flow_id, task_id))


class AppServices:
    def __init__(self, db_path: str | Path, config_path: str | Path):
        self.database = Database(db_path)
        self.config = ConfigService(config_path)
        self.database.initialize()
        self.clients = ClientService(self.database)
        self.pdf = PdfService()
        self.proposals = ProposalService()
        self.fiscal = FiscalService(self.database)
        self.pomodoro = PomodoroService(self.database, self.config)

    def remove_inactive_modules(self) -> None:
        self.database.remove_inactive_modules()
        self.config.remove_inactive_modules()
