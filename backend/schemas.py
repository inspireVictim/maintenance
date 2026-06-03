"""Pydantic-схемы для валидации входных и выходных данных."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Справочники ----------

class StaffRoleOut(BaseModel):
    id: int
    code: str
    name: str


class StaffBrief(BaseModel):
    id: int
    full_name: str
    role_code: str
    role_name: str


class StaffOut(StaffBrief):
    login: str
    phone: Optional[str]
    email: Optional[str]
    hire_date: dt.date
    is_active: int


class LocationOut(BaseModel):
    id: int
    name: str
    building: str
    notes: Optional[str]


class EquipmentTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    normative_mttr_hours: float
    icon: str


class PriorityOut(BaseModel):
    id: int
    code: str
    name: str
    color: str
    sla_hours: int
    sort_order: int


class StatusOut(BaseModel):
    id: int
    code: str
    name: str
    color: str
    is_closed: int
    sort_order: int


# ---------- Оборудование ----------

class EquipmentOut(BaseModel):
    id: int
    inventory_number: str
    name: str
    equipment_type_id: int
    equipment_type_name: str
    equipment_type_icon: str
    location_id: int
    location_name: str
    location_building: str
    manufacturer: Optional[str]
    serial_number: Optional[str]
    install_date: Optional[dt.date]
    is_active: int
    open_requests_count: int
    critical_open_count: int


# ---------- Запчасти ----------

class SparePartOut(BaseModel):
    id: int
    sku: str
    name: str
    unit: str
    unit_price: float
    quantity: int
    min_quantity: int
    is_low_stock: bool


class SparePartIn(BaseModel):
    sku: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=120)
    unit: str = Field(default="шт", max_length=10)
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=0, default=0)
    min_quantity: int = Field(ge=0, default=0)


class StockAdjustIn(BaseModel):
    """Пополнение/корректировка остатка детали."""
    delta: int = Field(description="+ пополнение, - расход; должно приводить к qty >= 0")
    note: Optional[str] = None


# ---------- Заявки ----------

class RequestIn(BaseModel):
    equipment_id: int
    priority_id: int
    title: str = Field(min_length=5, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    planned_date: Optional[dt.date] = None
    assigned_to: Optional[int] = None
    created_by: int


class RequestPartIn(BaseModel):
    part_id: int
    quantity: int = Field(gt=0)


class RequestCompleteIn(BaseModel):
    """Закрытие заявки с указанием фактически использованных запчастей."""
    parts_used: List[RequestPartIn] = Field(default_factory=list)
    completion_note: Optional[str] = Field(default=None, max_length=2000)


class RequestPartOut(BaseModel):
    part_id: int
    sku: str
    name: str
    unit: str
    quantity_used: int
    unit_price_at_use: float
    line_total: float


class RequestOut(BaseModel):
    id: int
    equipment_id: int
    equipment_inv_number: str
    equipment_name: str
    location_name: str
    priority_id: int
    priority_code: str
    priority_name: str
    priority_color: str
    priority_sla_hours: int
    status_id: int
    status_code: str
    status_name: str
    status_color: str
    is_closed: int
    title: str
    description: Optional[str]
    planned_date: Optional[dt.date]
    assigned_to: Optional[int]
    assignee_name: Optional[str]
    created_by: int
    creator_name: str
    created_at: dt.datetime
    started_at: Optional[dt.datetime]
    closed_at: Optional[dt.datetime]
    completion_note: Optional[str]
    parts: List[RequestPartOut] = []
    parts_total: float = 0.0


class AssignIn(BaseModel):
    assigned_to: int


class StatusChangeIn(BaseModel):
    status_code: str
    note: Optional[str] = None


# ---------- История ----------

class StatusHistoryOut(BaseModel):
    id: int
    request_id: int
    old_status_name: Optional[str]
    new_status_name: str
    new_status_color: str
    changed_by_name: str
    changed_at: dt.datetime
    note: Optional[str]
