from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ClientPayload(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1)
    rnc: str = ""
    pc_location: str = ""
    cedula: str = ""
    tss_class: str = ""
    resource_path: str = ""
    work_description: str = ""


class PathsPayload(BaseModel):
    paths: list[str]


class RenameAnalyzePayload(PathsPayload):
    routes: list[dict[str, Any]] = []
    default_folder: str = ""


class RenameExecutePayload(BaseModel):
    items: list[dict[str, Any]]


class ProposalPreviewPayload(BaseModel):
    variable_name: str
    proposal_type: str = "mensual"


class ProposalCreatePayload(ProposalPreviewPayload):
    source: str


class FiscalVersionPayload(BaseModel):
    id: str | None = None
    version: str
    change_date: str
    change_type: str
    description: str = ""
    affects_macros: str = "No"
    requires_manual_update: str = "No"


class FiscalBuyerPayload(BaseModel):
    id: str | None = None
    name: str
    purchase_date: str
    expiration_date: str = ""
    email: str = ""
    price: float = 0
    channel: str = "desconocido"


class MessagePayload(BaseModel):
    buyer_name: str = ""
    message_type: str = "Plantilla fiscal"
    email: str = ""


class PomodoroSettingsPayload(BaseModel):
    auto_start_break: bool = True
    auto_start_work: bool = True


class PomodoroCommandPayload(BaseModel):
    action: Literal["start", "pause", "skip", "reset"]


class PomodoroTaskPayload(BaseModel):
    id: str | None = None
    title: str
    completed_pomodoros: int = 0


class PomodoroSelectionPayload(BaseModel):
    task_id: str | None = None
    flow_id: str | None = None


class PomodoroTaskCompletionPayload(BaseModel):
    completed: bool = True


class PomodoroFlowPayload(BaseModel):
    id: str | None = None
    name: str


class AssignmentPayload(BaseModel):
    task_id: str
    assigned: bool = True


class FlowOrderPayload(BaseModel):
    task_ids: list[str]


class CompletionPayload(BaseModel):
    task_id: str
    completed: bool = True
