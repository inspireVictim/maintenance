"""Управление подключением к SQLite и инициализация схемы."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data" / "maintenance.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def seed_data() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM staff_roles")
        if cur.fetchone()[0] > 0:
            return

        cur.executemany(
            "INSERT INTO staff_roles (code, name) VALUES (?, ?)",
            [
                ("admin",       "Администратор системы"),
                ("dispatcher",  "Диспетчер"),
                ("engineer",    "Инженер"),
                ("technician",  "Техник"),
            ],
        )

        cur.executemany(
            """INSERT INTO staff
               (full_name, role_id, login, password_hash, phone, email, hire_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                ("Иванов Иван Иванович",      1, "admin",  "hash_admin",  "+996700110011", "admin@plant.kg",     "2023-01-15"),
                ("Петрова Анна Сергеевна",    2, "disp",   "hash_disp",   "+996700220022", "petrova@plant.kg",   "2023-03-01"),
                ("Кузнецов Дмитрий Олегович", 3, "kuzn",   "hash_kuzn",   "+996700330033", "kuznetsov@plant.kg", "2023-04-10"),
                ("Беков Тимур Эркинович",     3, "bekov",  "hash_bekov",  "+996700440044", "bekov@plant.kg",     "2023-05-20"),
                ("Турсунов Алмаз Жакыпович",  4, "turs",   "hash_turs",   "+996700550055", "tursunov@plant.kg",  "2023-08-01"),
                ("Эркинов Айбек Каныбекович", 4, "erkin",  "hash_erkin",  "+996700660066", "erkinov@plant.kg",   "2024-02-15"),
            ],
        )

        cur.executemany(
            "INSERT INTO locations (name, building, notes) VALUES (?, ?, ?)",
            [
                ("Цех №1 — Механический",   "Корпус А", "Токарные и фрезерные станки"),
                ("Цех №2 — Сборочный",      "Корпус Б", "Сборочные конвейерные линии"),
                ("Склад готовой продукции", "Корпус В", "Погрузчики и подъёмные механизмы"),
            ],
        )

        cur.executemany(
            "INSERT INTO equipment_types (name, description, normative_mttr_hours, icon) VALUES (?, ?, ?, ?)",
            [
                ("Токарный станок",    "Станки металлорежущие с ЧПУ",              4.0, "🔧"),
                ("Конвейерная линия",  "Линии сборки и упаковки",                  6.0, "🏭"),
                ("Вилочный погрузчик", "Электропогрузчики и дизельные погрузчики", 2.5, "🚜"),
                ("Система вентиляции", "Промышленные вентиляторы и фильтры",       3.0, "💨"),
            ],
        )

        cur.executemany(
            "INSERT INTO priorities (code, name, color, sla_hours, sort_order) VALUES (?, ?, ?, ?, ?)",
            [
                ("low",      "Низкий",      "#10B981", 72, 1),
                ("medium",   "Средний",     "#F59E0B", 24, 2),
                ("critical", "Критический", "#EF4444",  4, 3),
            ],
        )

        cur.executemany(
            "INSERT INTO request_statuses (code, name, color, is_closed, sort_order) VALUES (?, ?, ?, ?, ?)",
            [
                ("received", "Получена",    "#3B82F6", 0, 1),
                ("in_work",  "В работе",    "#F59E0B", 0, 2),
                ("review",   "На проверке", "#A855F7", 0, 3),
                ("done",     "Выполнена",   "#10B981", 1, 4),
                ("rejected", "Отклонена",   "#64748B", 1, 5),
            ],
        )

        cur.executemany(
            """INSERT INTO equipment
               (inventory_number, name, equipment_type_id, location_id, manufacturer, serial_number, install_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                ("TC-001", "Токарный станок DMG MORI NLX-2500", 1, 1, "DMG MORI", "SN-DMG-001", "2022-04-10"),
                ("TC-002", "Токарный станок Haas ST-10",         1, 1, "Haas",     "SN-HAAS-002","2023-09-22"),
                ("CL-001", "Конвейер сборки А-1",                2, 2, "Beumer",   "SN-BMR-003", "2021-12-01"),
                ("FL-001", "Погрузчик Toyota 8FBE15",            3, 3, "Toyota",   "SN-TOY-004", "2023-03-15"),
                ("FL-002", "Погрузчик Linde E25",                3, 3, "Linde",    "SN-LND-005", "2024-01-20"),
                ("VS-001", "Промышленный вентилятор Systemair",  4, 1, "Systemair","SN-SYS-006","2022-06-05"),
            ],
        )

        cur.executemany(
            "INSERT INTO spare_parts (sku, name, unit, unit_price, quantity, min_quantity) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("SP-001", "Подшипник 6204-2RS",          "шт", 320.00,  45, 10),
                ("SP-002", "Ремень приводной A-1180",     "шт", 480.00,  20,  5),
                ("SP-003", "Масло гидравлическое HLP 46", "л",  220.00, 120, 30),
                ("SP-004", "Фильтр воздушный SF-FA-150",  "шт", 380.00,  18,  4),
                ("SP-005", "Резец токарный CCMT 09",      "шт", 850.00,  30,  6),
                ("SP-006", "Контактор Schneider LC1D32",  "шт", 1200.00,  8,  2),
                ("SP-007", "Тормозные колодки погрузчика","шт", 750.00,  12,  4),
                ("SP-008", "Лента конвейерная EP400",     "м",  680.00,  60, 15),
            ],
        )

        cur.executemany(
            """INSERT INTO maintenance_requests
               (equipment_id, priority_id, status_id, title, description,
                planned_date, assigned_to, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (1, 3, 2,
                 "Остановка станка по перегрузке",
                 "При запуске программы X-104 сработала защита по току. Требуется диагностика и замена контактора.",
                 "2026-06-04", 3, 2, "2026-06-03 08:14:00"),
                (3, 2, 2,
                 "Скрип подшипника привода конвейера",
                 "Слышен характерный скрип, требует замены подшипника 6204-2RS на приводном валу.",
                 "2026-06-04", 4, 2, "2026-06-03 09:30:00"),
                (4, 1, 1,
                 "Плановая замена тормозных колодок",
                 "Согласно регламенту наработки 800 моточасов.",
                 "2026-06-08", None, 2, "2026-06-03 10:20:00"),
                (6, 2, 3,
                 "Замена воздушного фильтра вентустановки",
                 "Перепад давления превышает норму. Требуется замена фильтра.",
                 "2026-06-03", 5, 2, "2026-06-02 16:45:00"),
                (2, 1, 4,
                 "Плановое ТО — замена резцов",
                 "Заменены резцы CCMT 09 (3 шт), долита СОЖ. Работа завершена.",
                 "2026-06-02", 6, 2, "2026-06-01 14:00:00"),
                (5, 2, 1,
                 "Стук в редукторе погрузчика",
                 "Машинист сообщил о посторонних шумах при подъёме груза свыше 1 т.",
                 "2026-06-05", None, 2, "2026-06-03 11:00:00"),
            ],
        )

        # Закрываем заявку #5 (статус 'Выполнена'): задаём даты и списываем запчасти
        cur.execute(
            """UPDATE maintenance_requests
                  SET started_at = '2026-06-02 09:00:00',
                      closed_at  = '2026-06-02 11:30:00',
                      completion_note = 'ТО проведено по регламенту, нарушений не выявлено.'
                WHERE id = 5""",
        )

        cur.execute(
            "INSERT INTO request_parts (request_id, part_id, quantity_used, unit_price_at_use) VALUES (5, 5, 3, 850.00)"
        )
        cur.execute("UPDATE spare_parts SET quantity = quantity - 3 WHERE id = 5")

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_schema()
    seed_data()
    print(f"База данных создана: {DB_PATH}")
