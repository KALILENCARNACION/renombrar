from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import *
from .services import AppServices


def create_app(db_path: str | Path | None = None, config_path: str | Path | None = None) -> FastAPI:
    root = Path(__file__).resolve().parent.parent
    services = AppServices(db_path or os.getenv("APP_DB_PATH", root / "app.db"),
                           config_path or os.getenv("APP_CONFIG_PATH", root / "config.json"))
    app = FastAPI(title="Renombrar API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|null)$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.state.services = services

    def call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/health")
    def health(): return {"status": "ok"}

    @app.get("/api/v1/renamer/settings")
    def renamer_settings():
        data = services.config.load()
        return {key: data.get(key) for key in ("selected_output_folder", "saved_folders", "company_route_mappings")}

    @app.put("/api/v1/renamer/settings")
    def update_renamer_settings(payload: dict): return services.config.update(payload)

    @app.post("/api/v1/renamer/analyze")
    def analyze(payload: RenameAnalyzePayload): return services.pdf.analyze(payload.paths, payload.routes, payload.default_folder)

    @app.post("/api/v1/renamer/execute")
    def execute(payload: RenameExecutePayload): return services.pdf.execute(payload.items)

    @app.get("/api/v1/proposals/settings")
    def proposal_settings(): return {"copy_source_pdf": services.config.load().get("copy_source_pdf", "")}

    @app.put("/api/v1/proposals/settings")
    def update_proposal_settings(payload: dict): return services.config.update({"copy_source_pdf": payload.get("copy_source_pdf", "")})

    @app.post("/api/v1/proposals/preview")
    def proposal_preview(payload: ProposalPreviewPayload): return {"filename": call(services.proposals.preview, payload.variable_name, payload.proposal_type)}

    @app.post("/api/v1/proposals/create")
    def proposal_create(payload: ProposalCreatePayload): return call(services.proposals.create, payload.source, payload.variable_name, payload.proposal_type)

    @app.get("/api/v1/clients")
    def clients(search: str = Query(default="")): return services.clients.list(search)

    @app.get("/api/v1/clients/{client_id}")
    def client(client_id: str):
        item = services.clients.get(client_id)
        if not item: raise HTTPException(404, "Cliente no encontrado.")
        return item

    @app.post("/api/v1/clients", status_code=201)
    def create_client(payload: ClientPayload): return call(services.clients.save, payload.model_dump())

    @app.put("/api/v1/clients/{client_id}")
    def update_client(client_id: str, payload: ClientPayload): return call(services.clients.save, {**payload.model_dump(), "id": client_id})

    @app.delete("/api/v1/clients/{client_id}", status_code=204)
    def delete_client(client_id: str):
        if not services.clients.delete(client_id): raise HTTPException(404, "Cliente no encontrado.")

    @app.get("/api/v1/fiscal/versions")
    def versions(): return services.fiscal.versions()

    @app.post("/api/v1/fiscal/versions", status_code=201)
    def save_version(payload: FiscalVersionPayload): return call(services.fiscal.save_version, payload.model_dump())

    @app.get("/api/v1/fiscal/buyers")
    def buyers(): return services.fiscal.buyers()

    @app.post("/api/v1/fiscal/buyers", status_code=201)
    def save_buyer(payload: FiscalBuyerPayload): return call(services.fiscal.save_buyer, payload.model_dump())

    @app.put("/api/v1/fiscal/buyers/{buyer_id}")
    def update_buyer(buyer_id: str, payload: FiscalBuyerPayload): return call(services.fiscal.save_buyer, {**payload.model_dump(), "id": buyer_id})

    @app.get("/api/v1/fiscal/summary")
    def fiscal_summary(): return services.fiscal.summary()

    @app.post("/api/v1/fiscal/messages")
    def fiscal_message(payload: MessagePayload): return {"message": services.fiscal.message(payload.buyer_name, payload.message_type, payload.email)}

    @app.get("/api/v1/pomodoro/state")
    def pomodoro_state(): return services.pomodoro.state()

    @app.post("/api/v1/pomodoro/commands")
    def pomodoro_command(payload: PomodoroCommandPayload): return call(services.pomodoro.command, payload.action)

    @app.get("/api/v1/pomodoro/settings")
    def pomodoro_settings(): return services.pomodoro.settings()

    @app.put("/api/v1/pomodoro/settings")
    def pomodoro_settings_update(payload: PomodoroSettingsPayload): return services.pomodoro.update_settings(payload.model_dump())

    @app.get("/api/v1/pomodoro/tasks")
    def pomodoro_tasks(): return services.pomodoro.tasks()

    @app.post("/api/v1/pomodoro/tasks", status_code=201)
    def pomodoro_task_create(payload: PomodoroTaskPayload): return call(services.pomodoro.save_task, payload.model_dump())

    @app.put("/api/v1/pomodoro/tasks/{task_id}")
    def pomodoro_task_update(task_id: str, payload: PomodoroTaskPayload): return call(services.pomodoro.save_task, {**payload.model_dump(), "id": task_id})

    @app.delete("/api/v1/pomodoro/tasks/{task_id}", status_code=204)
    def pomodoro_task_delete(task_id: str):
        if not services.pomodoro.delete_task(task_id): raise HTTPException(404, "Tarea no encontrada.")

    @app.put("/api/v1/pomodoro/selection")
    def pomodoro_selection(payload: PomodoroSelectionPayload): return call(services.pomodoro.select_task, payload.task_id, payload.flow_id)

    @app.put("/api/v1/pomodoro/tasks/{task_id}/completed")
    def pomodoro_task_completed(task_id: str, payload: PomodoroTaskCompletionPayload):
        return call(services.pomodoro.complete_task, task_id, payload.completed)

    @app.get("/api/v1/pomodoro/flows")
    def pomodoro_flows(): return services.pomodoro.flows()

    @app.post("/api/v1/pomodoro/flows", status_code=201)
    def pomodoro_flow_create(payload: PomodoroFlowPayload): return call(services.pomodoro.save_flow, payload.model_dump())

    @app.put("/api/v1/pomodoro/flows/{flow_id}")
    def pomodoro_flow_update(flow_id: str, payload: PomodoroFlowPayload): return call(services.pomodoro.save_flow, {**payload.model_dump(), "id": flow_id})

    @app.delete("/api/v1/pomodoro/flows/{flow_id}", status_code=204)
    def pomodoro_flow_delete(flow_id: str):
        if not services.pomodoro.delete_flow(flow_id): raise HTTPException(404, "Flujo no encontrado.")

    @app.put("/api/v1/pomodoro/flows/{flow_id}/assignment")
    def pomodoro_assignment(flow_id: str, payload: AssignmentPayload):
        services.pomodoro.assign(flow_id, payload.task_id, payload.assigned); return {"status": "ok"}

    @app.put("/api/v1/pomodoro/flows/{flow_id}/order")
    def pomodoro_order(flow_id: str, payload: FlowOrderPayload):
        services.pomodoro.reorder(flow_id, payload.task_ids); return {"status": "ok"}

    @app.put("/api/v1/pomodoro/flows/{flow_id}/completion")
    def pomodoro_completion(flow_id: str, payload: CompletionPayload):
        services.pomodoro.complete(flow_id, payload.task_id, payload.completed); return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.api:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8765")),
        reload=False,
    )
