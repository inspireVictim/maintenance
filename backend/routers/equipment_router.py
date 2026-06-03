"""Оборудование предприятия."""
from __future__ import annotations

from fastapi import APIRouter

from ..database import db_cursor
from ..schemas import EquipmentOut

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


_LIST_SQL = """
SELECT
    e.id, e.inventory_number, e.name,
    e.equipment_type_id, et.name AS equipment_type_name, et.icon AS equipment_type_icon,
    e.location_id, l.name AS location_name, l.building AS location_building,
    e.manufacturer, e.serial_number, e.install_date, e.is_active,
    (SELECT COUNT(*) FROM maintenance_requests mr
       JOIN request_statuses s ON s.id = mr.status_id
      WHERE mr.equipment_id = e.id AND s.is_closed = 0) AS open_requests_count,
    (SELECT COUNT(*) FROM maintenance_requests mr
       JOIN request_statuses s ON s.id = mr.status_id
       JOIN priorities       p ON p.id = mr.priority_id
      WHERE mr.equipment_id = e.id AND s.is_closed = 0 AND p.code = 'critical') AS critical_open_count
FROM equipment e
JOIN equipment_types et ON et.id = e.equipment_type_id
JOIN locations        l  ON l.id  = e.location_id
WHERE e.is_active = 1
"""


@router.get("", response_model=list[EquipmentOut])
def list_equipment():
    with db_cursor() as cur:
        cur.execute(_LIST_SQL + " ORDER BY e.inventory_number")
        return [dict(r) for r in cur.fetchall()]


@router.get("/critical", response_model=list[EquipmentOut])
def list_critical_equipment():
    """Оборудование с открытыми критическими заявками."""
    sql = _LIST_SQL + """
          AND EXISTS (
              SELECT 1 FROM maintenance_requests mr
                JOIN request_statuses s ON s.id = mr.status_id
                JOIN priorities       p ON p.id = mr.priority_id
               WHERE mr.equipment_id = e.id
                 AND s.is_closed = 0
                 AND p.code = 'critical'
          )
        ORDER BY e.inventory_number
    """
    with db_cursor() as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]
