import json
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from PyPDF2 import PdfWriter

from backend.api import create_app
from backend.services import AppServices, ProposalService, unique_path


def make_services(tmp_path: Path) -> AppServices:
    return AppServices(tmp_path / "app.db", tmp_path / "config.json")


def test_client_crud_and_search(tmp_path):
    services = make_services(tmp_path)
    created = services.clients.save({"name": "Débito School", "rnc": "123"})
    assert services.clients.get(created["id"])["name"] == "Débito School"
    assert len(services.clients.list("debito")) == 1
    updated = services.clients.save({**created, "rnc": "456"})
    assert updated["rnc"] == "456"
    assert services.clients.delete(created["id"])
    assert services.clients.get(created["id"]) is None


def test_proposal_names_are_unique(tmp_path):
    source = tmp_path / "base.pdf"
    source.write_bytes(b"pdf")
    service = ProposalService()
    first = service.create(str(source), "Ana Pérez", "mensual")
    second = service.create(str(source), "Ana Pérez", "mensual")
    assert Path(first["target"]).name == "PROPUESTA DE ASESORIA PARA ANA PÉREZ.pdf"
    assert Path(second["target"]).name.endswith("(2).pdf")


def test_pdf_invalid_input_returns_per_file_error(tmp_path):
    services = make_services(tmp_path)
    result = services.pdf.analyze([str(tmp_path / "missing.pdf")], [], str(tmp_path))
    assert result[0]["status"] == "error"
    assert "existente" in result[0]["error"]


def test_fiscal_records_summary_and_message(tmp_path):
    services = make_services(tmp_path)
    services.fiscal.save_version({"version": "1.0", "change_date": "2026-06-20", "change_type": "Lanzamiento"})
    buyer = services.fiscal.save_buyer({"name": "Ana", "purchase_date": "2026-06-20", "price": 3000})
    assert buyer["price"] == 3000
    assert services.fiscal.summary() == {"versions": 1, "buyers": 1, "gross_profit": 3000.0, "net_profit": 3000.0}
    assert "Hola Ana" in services.fiscal.message("Ana", "Plantilla fiscal")


def test_pomodoro_transitions_tasks_and_flows(tmp_path):
    services = make_services(tmp_path)
    task = services.pomodoro.save_task({"title": "Revisar facturas"})
    flow = services.pomodoro.save_flow({"name": "Cierre mensual"})
    services.pomodoro.assign(flow["id"], task["id"], True)
    services.pomodoro.complete(flow["id"], task["id"], True)
    assert services.pomodoro.flows()[0]["tasks"][0]["completed"] == 1
    assert services.pomodoro.command("start")["running"] is True
    paused = services.pomodoro.command("pause")
    assert paused["running"] is False
    skipped = services.pomodoro.command("skip")
    assert skipped["phase"] == "short_break"
    assert skipped["completed_count"] == 1
    assert services.pomodoro.command("reset")["phase"] == "work"
    services.config.update({"pomodoro_state": {
        "date": date.today().isoformat(), "completed_count": 0, "phase": "work",
        "remaining_seconds": 0, "running": True, "phase_end_at": "2000-01-01T00:00:00",
        "selected_task_id": task["id"], "selected_flow_id": None,
    }})
    expired = services.pomodoro.state()
    assert expired["phase"] == "short_break"
    assert expired["completed_count"] == 1
    assert services.pomodoro.tasks()[0]["completed_pomodoros"] == 1


def test_api_contract(tmp_path):
    client = TestClient(create_app(tmp_path / "api.db", tmp_path / "api.json"))
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    created = client.post("/api/v1/clients", json={"name": "Kalil", "rnc": "001"})
    assert created.status_code == 201
    client_id = created.json()["id"]
    assert client.get("/api/v1/clients", params={"search": "kal"}).json()[0]["id"] == client_id
    assert client.put(f"/api/v1/clients/{client_id}", json={"name": "Kalil Editado"}).status_code == 200
    assert client.delete(f"/api/v1/clients/{client_id}").status_code == 204
    assert client.post("/api/v1/proposals/preview", json={"variable_name": "Acme"}).json()["filename"].endswith("ACME.pdf")
    cors = client.options(
        "/api/v1/renamer/settings",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert cors.status_code == 200
    assert cors.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_destructive_migration_preserves_active_data(tmp_path):
    source_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "copy.db"
    config_path = tmp_path / "copy.json"
    shutil.copy2(source_root / "app.db", db_path)
    shutil.copy2(source_root / "config.json", config_path)
    with sqlite3.connect(db_path) as connection:
        before = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("clients", "pomodoro_tasks", "pomodoro_flows", "fiscal_template_versions", "fiscal_template_buyers")
        }
    services = AppServices(db_path, config_path)
    services.remove_inactive_modules()
    with sqlite3.connect(db_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        after = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in before}
    assert before == after
    assert not {"tasks", "account_catalog", "statement_headers", "statement_line_items", "statement_default_accounts"} & tables
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert not {"organizer_folder", "template_workbook_path", "template_sheet_password"} & config.keys()
