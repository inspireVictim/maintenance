"""Склад запчастей."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..database import db_cursor
from ..schemas import SparePartIn, SparePartOut, StockAdjustIn

router = APIRouter(prefix="/api/parts", tags=["parts"])


def _row_to_part(row) -> dict:
    d = dict(row)
    d["is_low_stock"] = d["quantity"] <= d["min_quantity"]
    return d


@router.get("", response_model=list[SparePartOut])
def list_parts(low_only: bool = False):
    sql = "SELECT * FROM spare_parts WHERE is_active = 1"
    if low_only:
        sql += " AND quantity <= min_quantity"
    sql += " ORDER BY name"
    with db_cursor() as cur:
        cur.execute(sql)
        return [_row_to_part(r) for r in cur.fetchall()]


@router.post("", response_model=SparePartOut, status_code=201)
def create_part(payload: SparePartIn):
    with db_cursor(commit=True) as cur:
        try:
            cur.execute(
                """INSERT INTO spare_parts
                   (sku, name, unit, unit_price, quantity, min_quantity)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (payload.sku, payload.name, payload.unit, payload.unit_price,
                 payload.quantity, payload.min_quantity),
            )
        except Exception as exc:
            raise HTTPException(400, f"Не удалось добавить деталь: {exc}")
        new_id = cur.lastrowid
        cur.execute("SELECT * FROM spare_parts WHERE id = ?", (new_id,))
        return _row_to_part(cur.fetchone())


@router.post("/{part_id}/adjust", response_model=SparePartOut)
def adjust_stock(part_id: int, payload: StockAdjustIn):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT quantity FROM spare_parts WHERE id = ?", (part_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Деталь не найдена")
        new_qty = row["quantity"] + payload.delta
        if new_qty < 0:
            raise HTTPException(400, "После операции остаток оказался бы отрицательным")
        cur.execute("UPDATE spare_parts SET quantity = ? WHERE id = ?", (new_qty, part_id))
        cur.execute("SELECT * FROM spare_parts WHERE id = ?", (part_id,))
        return _row_to_part(cur.fetchone())
