"""Справочники: роли, статусы, приоритеты, локации, типы оборудования."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from ..database import db_cursor
from ..schemas import (
    EquipmentTypeOut, LocationOut, PriorityOut,
    StaffOut, StatusOut,
)

router = APIRouter(prefix="/api", tags=["references"])


@router.get("/priorities", response_model=list[PriorityOut])
def list_priorities():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM priorities ORDER BY sort_order")
        return [dict(r) for r in cur.fetchall()]


@router.get("/statuses", response_model=list[StatusOut])
def list_statuses():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM request_statuses ORDER BY sort_order")
        return [dict(r) for r in cur.fetchall()]


@router.get("/locations", response_model=list[LocationOut])
def list_locations():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM locations ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


@router.get("/equipment_types", response_model=list[EquipmentTypeOut])
def list_equipment_types():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM equipment_types ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


@router.get("/staff", response_model=list[StaffOut])
def list_staff(role: Optional[str] = None):
    sql = """
        SELECT s.id, s.full_name, r.code AS role_code, r.name AS role_name,
               s.login, s.phone, s.email, s.hire_date, s.is_active
          FROM staff s
          JOIN staff_roles r ON r.id = s.role_id
         WHERE s.is_active = 1
    """
    params: list = []
    if role:
        sql += " AND r.code = ?"
        params.append(role)
    sql += " ORDER BY s.full_name"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
