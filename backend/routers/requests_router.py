"""Заявки на техническое обслуживание.

Ключевой алгоритм закрытия заявки реализован в complete_request():
в рамках одной транзакции выполняется проверка остатков на складе,
списание запчастей, фиксация дат и перевод заявки в статус 'Выполнена'.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import db_cursor
from ..schemas import (
    AssignIn, RequestCompleteIn, RequestIn, RequestOut, StatusChangeIn,
    StatusHistoryOut,
)

router = APIRouter(prefix="/api/requests", tags=["requests"])


_LIST_SQL = """
SELECT
    r.id,
    r.equipment_id, e.inventory_number AS equipment_inv_number, e.name AS equipment_name,
    l.name AS location_name,
    r.priority_id, p.code AS priority_code, p.name AS priority_name,
    p.color AS priority_color, p.sla_hours AS priority_sla_hours,
    r.status_id, s.code AS status_code, s.name AS status_name,
    s.color AS status_color, s.is_closed,
    r.title, r.description, r.planned_date,
    r.assigned_to, a.full_name AS assignee_name,
    r.created_by, c.full_name AS creator_name,
    r.created_at, r.started_at, r.closed_at,
    r.completion_note
FROM maintenance_requests r
JOIN equipment        e ON e.id = r.equipment_id
JOIN locations        l ON l.id = e.location_id
JOIN priorities       p ON p.id = r.priority_id
JOIN request_statuses s ON s.id = r.status_id
JOIN staff            c ON c.id = r.created_by
LEFT JOIN staff       a ON a.id = r.assigned_to
"""


def _load_parts(cur, request_id: int):
    cur.execute(
        """SELECT rp.part_id, sp.sku, sp.name, sp.unit,
                  rp.quantity_used, rp.unit_price_at_use,
                  (rp.quantity_used * rp.unit_price_at_use) AS line_total
             FROM request_parts rp
             JOIN spare_parts sp ON sp.id = rp.part_id
            WHERE rp.request_id = ?
            ORDER BY sp.name""",
        (request_id,),
    )
    parts = [dict(r) for r in cur.fetchall()]
    total = round(sum(p["line_total"] for p in parts), 2)
    return parts, total


def _assemble(cur, row) -> dict:
    d = dict(row)
    parts, total = _load_parts(cur, d["id"])
    d["parts"] = parts
    d["parts_total"] = total
    return d


@router.get("", response_model=list[RequestOut])
def list_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    equipment_id: Optional[int] = None,
    open_only: bool = False,
):
    sql = _LIST_SQL + " WHERE 1=1"
    params: list = []
    if status:
        sql += " AND s.code = ?"; params.append(status)
    if priority:
        sql += " AND p.code = ?"; params.append(priority)
    if assigned_to:
        sql += " AND r.assigned_to = ?"; params.append(assigned_to)
    if equipment_id:
        sql += " AND r.equipment_id = ?"; params.append(equipment_id)
    if open_only:
        sql += " AND s.is_closed = 0"
    sql += " ORDER BY p.sort_order DESC, r.created_at DESC"
    with db_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [_assemble(cur, r) for r in rows]


@router.get("/{request_id}", response_model=RequestOut)
def get_request(request_id: int):
    with db_cursor() as cur:
        cur.execute(_LIST_SQL + " WHERE r.id = ?", (request_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Заявка не найдена")
        return _assemble(cur, row)


@router.post("", response_model=RequestOut, status_code=201)
def create_request(payload: RequestIn):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM request_statuses WHERE code = 'received'")
        received_id = cur.fetchone()["id"]
        try:
            cur.execute(
                """INSERT INTO maintenance_requests
                   (equipment_id, priority_id, status_id, title, description,
                    planned_date, assigned_to, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (payload.equipment_id, payload.priority_id, received_id,
                 payload.title, payload.description, payload.planned_date,
                 payload.assigned_to, payload.created_by),
            )
        except Exception as exc:
            raise HTTPException(400, f"Не удалось создать заявку: {exc}")
        new_id = cur.lastrowid
        cur.execute(_LIST_SQL + " WHERE r.id = ?", (new_id,))
        return _assemble(cur, cur.fetchone())


@router.put("/{request_id}", response_model=RequestOut)
def update_request(request_id: int, payload: RequestIn):
    with db_cursor(commit=True) as cur:
        cur.execute(
            """UPDATE maintenance_requests
                  SET equipment_id = ?, priority_id = ?, title = ?,
                      description = ?, planned_date = ?, assigned_to = ?
                WHERE id = ?""",
            (payload.equipment_id, payload.priority_id, payload.title,
             payload.description, payload.planned_date, payload.assigned_to,
             request_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Заявка не найдена")
        cur.execute(_LIST_SQL + " WHERE r.id = ?", (request_id,))
        return _assemble(cur, cur.fetchone())


@router.post("/{request_id}/assign", response_model=RequestOut)
def assign_request(request_id: int, payload: AssignIn):
    """Назначение исполнителя «в один клик» из выпадающего списка."""
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id, full_name FROM staff WHERE id = ? AND is_active = 1",
                    (payload.assigned_to,))
        if cur.fetchone() is None:
            raise HTTPException(400, "Исполнитель не найден или неактивен")

        cur.execute("SELECT status_id FROM maintenance_requests WHERE id = ?", (request_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Заявка не найдена")

        cur.execute("SELECT id, code FROM request_statuses WHERE id = ?", (row["status_id"],))
        cur_status = cur.fetchone()

        # Если статус был 'Получена' — автоматически переводим в 'В работе' и фиксируем started_at
        if cur_status["code"] == "received":
            cur.execute("SELECT id FROM request_statuses WHERE code = 'in_work'")
            in_work_id = cur.fetchone()["id"]
            cur.execute(
                """UPDATE maintenance_requests
                      SET assigned_to = ?, status_id = ?,
                          started_at  = COALESCE(started_at, CURRENT_TIMESTAMP)
                    WHERE id = ?""",
                (payload.assigned_to, in_work_id, request_id),
            )
        else:
            cur.execute(
                "UPDATE maintenance_requests SET assigned_to = ? WHERE id = ?",
                (payload.assigned_to, request_id),
            )

        cur.execute(_LIST_SQL + " WHERE r.id = ?", (request_id,))
        return _assemble(cur, cur.fetchone())


@router.post("/{request_id}/status", response_model=RequestOut)
def change_status(request_id: int, payload: StatusChangeIn):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id, is_closed FROM request_statuses WHERE code = ?",
                    (payload.status_code,))
        st = cur.fetchone()
        if st is None:
            raise HTTPException(400, f"Статус '{payload.status_code}' не найден")

        cur.execute("SELECT id FROM maintenance_requests WHERE id = ?", (request_id,))
        if cur.fetchone() is None:
            raise HTTPException(404, "Заявка не найдена")

        # Простой переход (закрытие через /complete!)
        cur.execute(
            "UPDATE maintenance_requests SET status_id = ? WHERE id = ?",
            (st["id"], request_id),
        )
        cur.execute(_LIST_SQL + " WHERE r.id = ?", (request_id,))
        return _assemble(cur, cur.fetchone())


# ============================================================
# КЛЮЧЕВОЙ БИЗНЕС-АЛГОРИТМ: закрытие заявки со списанием запчастей
# ============================================================

@router.post("/{request_id}/complete", response_model=RequestOut)
def complete_request(request_id: int, payload: RequestCompleteIn):
    """Перевод заявки в статус 'Выполнена' с атомарным списанием запчастей.

    Шаги, выполняемые в рамках единой транзакции:
        1. Загрузить заявку; проверить, что она не закрыта.
        2. Для каждой использованной запчасти проверить остаток на складе.
           Если хотя бы одной детали недостаточно — отказ HTTP 400.
        3. Зафиксировать историческую цену списания (unit_price_at_use)
           по текущей цене из spare_parts.
        4. Вставить строки в request_parts; уменьшить spare_parts.quantity.
        5. Перевести заявку в статус 'done', выставить closed_at.
        6. Триггер trg_request_status_audit автоматически запишет
           изменение статуса в request_status_history.
    """
    with db_cursor(commit=True) as cur:
        # 1. Заявка должна существовать и быть открытой
        cur.execute(
            """SELECT r.id, r.status_id, s.is_closed
                 FROM maintenance_requests r
                 JOIN request_statuses s ON s.id = r.status_id
                WHERE r.id = ?""",
            (request_id,),
        )
        req = cur.fetchone()
        if req is None:
            raise HTTPException(404, "Заявка не найдена")
        if req["is_closed"]:
            raise HTTPException(400, "Заявка уже закрыта")

        # 2. Загружаем актуальные данные по всем затребованным запчастям
        parts_used = payload.parts_used
        for line in parts_used:
            cur.execute(
                "SELECT id, sku, name, quantity, unit_price FROM spare_parts WHERE id = ?",
                (line.part_id,),
            )
            sp = cur.fetchone()
            if sp is None:
                raise HTTPException(400, f"Запчасть #{line.part_id} не найдена")
            if sp["quantity"] < line.quantity:
                raise HTTPException(
                    400,
                    f"Недостаточно «{sp['name']}» ({sp['sku']}) на складе: "
                    f"требуется {line.quantity}, доступно {sp['quantity']}",
                )

        # 3-4. Списываем (один раз — после проверок всех позиций)
        for line in parts_used:
            cur.execute("SELECT unit_price FROM spare_parts WHERE id = ?", (line.part_id,))
            price = float(cur.fetchone()["unit_price"])
            try:
                cur.execute(
                    """INSERT INTO request_parts
                       (request_id, part_id, quantity_used, unit_price_at_use)
                       VALUES (?, ?, ?, ?)""",
                    (request_id, line.part_id, line.quantity, price),
                )
            except Exception as exc:
                raise HTTPException(
                    400,
                    f"Эта запчасть уже была списана ранее по этой заявке: {exc}",
                )
            cur.execute(
                "UPDATE spare_parts SET quantity = quantity - ? WHERE id = ?",
                (line.quantity, line.part_id),
            )

        # 5. Перевод заявки в статус 'done'
        cur.execute("SELECT id FROM request_statuses WHERE code = 'done'")
        done_id = cur.fetchone()["id"]
        cur.execute(
            """UPDATE maintenance_requests
                  SET status_id = ?, closed_at = CURRENT_TIMESTAMP,
                      completion_note = ?
                WHERE id = ?""",
            (done_id, payload.completion_note, request_id),
        )

        # 6. Возврат обновлённой заявки
        cur.execute(_LIST_SQL + " WHERE r.id = ?", (request_id,))
        return _assemble(cur, cur.fetchone())


@router.delete("/{request_id}", status_code=204)
def delete_request(request_id: int):
    """Удаление заявки. Допустимо только в статусе 'Получена'."""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """SELECT s.code FROM maintenance_requests r
                 JOIN request_statuses s ON s.id = r.status_id
                WHERE r.id = ?""",
            (request_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Заявка не найдена")
        if row["code"] != "received":
            raise HTTPException(400, "Удалять можно только заявки в статусе 'Получена'")
        cur.execute("DELETE FROM maintenance_requests WHERE id = ?", (request_id,))


@router.get("/{request_id}/history", response_model=list[StatusHistoryOut])
def get_history(request_id: int):
    with db_cursor() as cur:
        cur.execute(
            """SELECT h.id, h.request_id,
                      os.name AS old_status_name,
                      ns.name AS new_status_name, ns.color AS new_status_color,
                      st.full_name AS changed_by_name,
                      h.changed_at, h.note
                 FROM request_status_history h
                 LEFT JOIN request_statuses os ON os.id = h.old_status_id
                 JOIN      request_statuses ns ON ns.id = h.new_status_id
                 JOIN      staff            st ON st.id = h.changed_by
                WHERE h.request_id = ?
                ORDER BY h.changed_at DESC""",
            (request_id,),
        )
        return [dict(r) for r in cur.fetchall()]
