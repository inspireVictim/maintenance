-- =====================================================
-- БАЗА ДАННЫХ "Учёт заявок на ТО"
-- СУБД: SQLite 3.35+    Кодировка: UTF-8
-- Схема в 3НФ
-- =====================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA encoding     = 'UTF-8';

-- -------- 1. СПРАВОЧНИКИ -----------------------------

CREATE TABLE IF NOT EXISTS staff_roles (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT    NOT NULL UNIQUE,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS staff (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    role_id       INTEGER NOT NULL,
    login         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    phone         TEXT    CHECK (phone IS NULL OR phone GLOB '+[0-9]*'),
    email         TEXT    UNIQUE CHECK (email IS NULL OR email LIKE '_%@_%._%'),
    hire_date     DATE    NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (role_id) REFERENCES staff_roles (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS locations (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL UNIQUE,
    building TEXT    NOT NULL,
    notes    TEXT
);

CREATE TABLE IF NOT EXISTS equipment_types (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    name                  TEXT    NOT NULL UNIQUE,
    description           TEXT,
    normative_mttr_hours  NUMERIC(6, 1) NOT NULL DEFAULT 4
                          CHECK (normative_mttr_hours > 0),
    icon                  TEXT    NOT NULL DEFAULT '⚙️'
);

CREATE TABLE IF NOT EXISTS priorities (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    color      TEXT    NOT NULL DEFAULT '#64748B',
    sla_hours  INTEGER NOT NULL CHECK (sla_hours > 0),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS request_statuses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    color      TEXT    NOT NULL DEFAULT '#64748B',
    is_closed  INTEGER NOT NULL DEFAULT 0 CHECK (is_closed IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- -------- 2. ОСНОВНЫЕ СУЩНОСТИ -----------------------

CREATE TABLE IF NOT EXISTS equipment (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_number  TEXT    NOT NULL UNIQUE,
    name              TEXT    NOT NULL,
    equipment_type_id INTEGER NOT NULL,
    location_id       INTEGER NOT NULL,
    manufacturer      TEXT,
    serial_number     TEXT,
    install_date      DATE,
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (equipment_type_id) REFERENCES equipment_types (id) ON DELETE RESTRICT,
    FOREIGN KEY (location_id)       REFERENCES locations       (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS spare_parts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sku          TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    unit         TEXT    NOT NULL DEFAULT 'шт',
    unit_price   NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    quantity     INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_quantity INTEGER NOT NULL DEFAULT 0 CHECK (min_quantity >= 0),
    is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- -------- 3. ЗАЯВКИ И ИСТОРИЯ ------------------------

CREATE TABLE IF NOT EXISTS maintenance_requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER NOT NULL,
    priority_id     INTEGER NOT NULL,
    status_id       INTEGER NOT NULL,
    title           TEXT    NOT NULL CHECK (length(trim(title)) >= 5),
    description     TEXT,
    planned_date    DATE,
    assigned_to     INTEGER,
    created_by      INTEGER NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at      TIMESTAMP,
    closed_at       TIMESTAMP,
    completion_note TEXT,
    CHECK (started_at IS NULL OR started_at >= created_at),
    CHECK (closed_at  IS NULL OR closed_at  >= created_at),
    FOREIGN KEY (equipment_id) REFERENCES equipment        (id) ON DELETE RESTRICT,
    FOREIGN KEY (priority_id)  REFERENCES priorities       (id) ON DELETE RESTRICT,
    FOREIGN KEY (status_id)    REFERENCES request_statuses (id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_to)  REFERENCES staff            (id) ON DELETE SET NULL,
    FOREIGN KEY (created_by)   REFERENCES staff            (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS request_parts (
    request_id        INTEGER NOT NULL,
    part_id           INTEGER NOT NULL,
    quantity_used     INTEGER NOT NULL CHECK (quantity_used > 0),
    unit_price_at_use NUMERIC(10, 2) NOT NULL CHECK (unit_price_at_use >= 0),
    PRIMARY KEY (request_id, part_id),
    FOREIGN KEY (request_id) REFERENCES maintenance_requests (id) ON DELETE CASCADE,
    FOREIGN KEY (part_id)    REFERENCES spare_parts          (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS request_status_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id    INTEGER NOT NULL,
    old_status_id INTEGER,
    new_status_id INTEGER NOT NULL,
    changed_by    INTEGER NOT NULL,
    changed_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note          TEXT,
    FOREIGN KEY (request_id)    REFERENCES maintenance_requests (id) ON DELETE CASCADE,
    FOREIGN KEY (old_status_id) REFERENCES request_statuses     (id) ON DELETE RESTRICT,
    FOREIGN KEY (new_status_id) REFERENCES request_statuses     (id) ON DELETE RESTRICT,
    FOREIGN KEY (changed_by)    REFERENCES staff                (id) ON DELETE RESTRICT
);

-- -------- 4. ИНДЕКСЫ ---------------------------------

CREATE INDEX IF NOT EXISTS idx_equipment_type     ON equipment             (equipment_type_id);
CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment             (location_id);
CREATE INDEX IF NOT EXISTS idx_req_status         ON maintenance_requests  (status_id);
CREATE INDEX IF NOT EXISTS idx_req_priority       ON maintenance_requests  (priority_id);
CREATE INDEX IF NOT EXISTS idx_req_assigned       ON maintenance_requests  (assigned_to);
CREATE INDEX IF NOT EXISTS idx_req_equipment      ON maintenance_requests  (equipment_id);
CREATE INDEX IF NOT EXISTS idx_req_created        ON maintenance_requests  (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_request    ON request_status_history(request_id);
CREATE INDEX IF NOT EXISTS idx_parts_sku          ON spare_parts           (sku);

-- -------- 5. ТРИГГЕРЫ БИЗНЕС-ЛОГИКИ -------------------

DROP TRIGGER IF EXISTS trg_request_status_audit;
CREATE TRIGGER trg_request_status_audit
AFTER UPDATE OF status_id ON maintenance_requests
FOR EACH ROW
WHEN OLD.status_id != NEW.status_id
BEGIN
    INSERT INTO request_status_history
        (request_id, old_status_id, new_status_id, changed_by, note)
    VALUES (
        NEW.id, OLD.status_id, NEW.status_id,
        COALESCE(NEW.assigned_to, NEW.created_by),
        'Автоматическая регистрация смены статуса'
    );
END;

DROP TRIGGER IF EXISTS trg_parts_no_overdraft;
CREATE TRIGGER trg_parts_no_overdraft
BEFORE UPDATE OF quantity ON spare_parts
FOR EACH ROW
WHEN NEW.quantity < 0
BEGIN
    SELECT RAISE(ABORT, 'Невозможно списать больше, чем имеется на складе');
END;
