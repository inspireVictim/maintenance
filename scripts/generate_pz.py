# -*- coding: utf-8 -*-
"""Генератор пояснительной записки ВКР по ГОСТ КР (ГОСТ 2.105-95).

Тема: «Разработка базы данных для учёта заявок на техническое обслуживание».

Запуск:
    python scripts/generate_pz.py

Результат сохраняется в файл ПЗ_Учет_Заявок_на_Техническое_Обслуживание.docx
в корне проекта.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Mm, Pt, RGBColor


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "ПЗ_Учет_Заявок_на_Техническое_Обслуживание.docx"

FONT_NAME = "Times New Roman"
FONT_SIZE = 14


# ----------------------------------------------------------------------------
# Утилиты форматирования
# ----------------------------------------------------------------------------

def _set_run_font(run, *, bold=False, italic=False, size=FONT_SIZE, color=None):
    run.font.name = FONT_NAME
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rFonts.set(qn("w:cs"), FONT_NAME)
    rFonts.set(qn("w:eastAsia"), FONT_NAME)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _apply_paragraph_format(p, *, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                            first_line_indent=True,
                            space_before=0, space_after=0, line_spacing=1.5):
    pf = p.paragraph_format
    pf.alignment = alignment
    pf.first_line_indent = Cm(1.25) if first_line_indent else Cm(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line_spacing
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)


def add_paragraph(doc, text, *, bold=False, italic=False,
                  alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                  first_line_indent=True, space_before=0, space_after=0,
                  size=FONT_SIZE):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=alignment,
                            first_line_indent=first_line_indent,
                            space_before=space_before, space_after=space_after)
    _set_run_font(p.add_run(text), bold=bold, italic=italic, size=size)


def add_centered(doc, text, *, bold=False, size=FONT_SIZE, space_after=6):
    add_paragraph(doc, text, bold=bold,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  first_line_indent=False, space_after=space_after, size=size)


def add_chapter_heading(doc, number, title):
    doc.add_page_break()
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False, space_after=18)
    _set_run_font(p.add_run(f"{number}. {title.upper()}"), bold=True)


def add_section_heading(doc, number, title):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=False,
                            space_before=12, space_after=8)
    _set_run_font(p.add_run(f"{number} {title}"), bold=True)


def add_list_item(doc, text, *, marker="—"):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                            first_line_indent=False)
    p.paragraph_format.left_indent = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    _set_run_font(p.add_run(f"{marker} {text}"))


def add_screenshot_marker(doc, caption):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False,
                            space_before=8, space_after=8)
    _set_run_font(p.add_run(f"{{Скриншот: {caption}}}"),
                  italic=True, color=RGBColor(0x33, 0x33, 0x33))


def add_figure_caption(doc, text):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False, space_after=12)
    _set_run_font(p.add_run(text))


def add_code_block(doc, code):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=False,
                            space_before=4, space_after=8, line_spacing=1.15)
    run = p.add_run(code)
    run.font.name = "Courier New"
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), "Courier New")
    rFonts.set(qn("w:hAnsi"), "Courier New")
    rFonts.set(qn("w:cs"), "Courier New")
    run.font.size = Pt(11)


def add_table(doc, headers, rows, *, col_widths_cm=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        cell.text = ""
        p = cell.paragraphs[0]
        _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                                first_line_indent=False, line_spacing=1.15)
        _set_run_font(p.add_run(header), bold=True)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = table.rows[r].cells[c]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cell.text = ""
            p = cell.paragraphs[0]
            _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                                    first_line_indent=False, line_spacing=1.15)
            _set_run_font(p.add_run(str(value)))
    if col_widths_cm:
        for r in table.rows:
            for i, w in enumerate(col_widths_cm):
                r.cells[i].width = Cm(w)
    spacer = doc.add_paragraph()
    _apply_paragraph_format(spacer, first_line_indent=False, space_after=6)


def _setup_document(doc):
    section = doc.sections[0]
    section.top_margin    = Mm(20)
    section.bottom_margin = Mm(20)
    section.left_margin   = Mm(30)
    section.right_margin  = Mm(10)

    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(FONT_SIZE)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    style.paragraph_format.line_spacing = 1.5


# ----------------------------------------------------------------------------
# Титульный лист и содержание
# ----------------------------------------------------------------------------

def _build_title_page(doc):
    for line in [
        "МИНИСТЕРСТВО ОБРАЗОВАНИЯ И НАУКИ КЫРГЫЗСКОЙ РЕСПУБЛИКИ",
        "",
        "{ПОЛНОЕ НАИМЕНОВАНИЕ УЧЕБНОГО ЗАВЕДЕНИЯ}",
        "",
        "Факультет информационных технологий",
        "Кафедра программной инженерии",
    ]:
        add_centered(doc, line)
    for _ in range(4):
        add_centered(doc, "")
    add_centered(doc, "ПОЯСНИТЕЛЬНАЯ ЗАПИСКА", bold=True, size=16)
    add_centered(doc, "к выпускной квалификационной работе", size=14)
    add_centered(doc, "на тему:", size=14)
    add_centered(doc,
                 "«Разработка базы данных для учёта заявок "
                 "на техническое обслуживание»",
                 bold=True, size=14)
    for _ in range(6):
        add_centered(doc, "")
    for line in [
        "Выполнил студент: ________________________________________",
        "Группа: _________________________________________________",
        "Научный руководитель: ____________________________________",
        "Заведующий кафедрой: ____________________________________",
    ]:
        add_paragraph(doc, line, first_line_indent=False, space_after=8)
    for _ in range(4):
        add_centered(doc, "")
    add_centered(doc, "Бишкек — 2026")


def _build_contents(doc):
    doc.add_page_break()
    add_centered(doc, "СОДЕРЖАНИЕ", bold=True, space_after=14)

    rows = [
        ("ВВЕДЕНИЕ", "3"),
        ("1. ПРОЕКТИРОВАНИЕ БАЗЫ ДАННЫХ", "6"),
        ("    1.1. Характеристика предметной области", "6"),
        ("    1.2. Цели и задачи раздела", "9"),
        ("    1.3. Приведение к первой нормальной форме (1НФ)", "11"),
        ("    1.4. Приведение ко второй нормальной форме (2НФ)", "13"),
        ("    1.5. Приведение к третьей нормальной форме (3НФ)", "16"),
        ("    1.6. Логическая схема базы данных", "20"),
        ("    1.7. Реализация в SQLite (DDL-скрипт)", "23"),
        ("    1.8. Выводы по разделу", "30"),
        ("2. ПРОГРАММНАЯ РЕАЛИЗАЦИЯ СЕРВЕРНОЙ ЧАСТИ", "31"),
        ("    2.1. Обоснование выбора инструментальных средств", "31"),
        ("    2.2. Архитектура серверного приложения", "33"),
        ("    2.3. CRUD-эндпоинты для заявок и оборудования", "36"),
        ("    2.4. Алгоритм закрытия заявки со списанием запчастей", "39"),
        ("    2.5. Транзакционная целостность операций", "44"),
        ("    2.6. Выводы по разделу", "46"),
        ("3. ПРОГРАММНАЯ РЕАЛИЗАЦИЯ КЛИЕНТСКОЙ ЧАСТИ", "47"),
        ("    3.1. UX/UI-концепция «Enterprise Dashboard»", "47"),
        ("    3.2. Структура интерфейса диспетчера", "50"),
        ("    3.3. Цветовая маркировка приоритетов в таблице", "53"),
        ("    3.4. Канбан-доска заявок на CSS Grid", "55"),
        ("    3.5. Назначение исполнителя «в один клик»", "58"),
        ("    3.6. Динамическое закрытие заявки и Fetch API", "60"),
        ("    3.7. Адаптивная вёрстка", "63"),
        ("    3.8. Выводы по разделу", "65"),
        ("4. ТЕСТИРОВАНИЕ", "66"),
        ("    4.1. Тестирование ключевого алгоритма закрытия заявки", "66"),
        ("    4.2. Тестирование REST-API и фильтрации", "69"),
        ("    4.3. Тестирование пользовательского интерфейса", "71"),
        ("    4.4. Выводы по разделу", "73"),
        ("ЗАКЛЮЧЕНИЕ", "74"),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "77"),
    ]
    table = doc.add_table(rows=len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r, (title, page) in enumerate(rows):
        c1 = table.rows[r].cells[0]
        c2 = table.rows[r].cells[1]
        c1.text = ""; c2.text = ""
        p1 = c1.paragraphs[0]; p2 = c2.paragraphs[0]
        _apply_paragraph_format(p1, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                                first_line_indent=False, line_spacing=1.2)
        _apply_paragraph_format(p2, alignment=WD_ALIGN_PARAGRAPH.RIGHT,
                                first_line_indent=False, line_spacing=1.2)
        _set_run_font(p1.add_run(title), bold=title and not title.startswith(" "))
        _set_run_font(p2.add_run(page))
        c1.width = Cm(13.5); c2.width = Cm(2.5)


# ----------------------------------------------------------------------------
# Введение
# ----------------------------------------------------------------------------

def _build_introduction(doc):
    doc.add_page_break()
    add_centered(doc, "ВВЕДЕНИЕ", bold=True, space_after=14)

    add_paragraph(doc,
        "В современной промышленности коэффициент технической готовности "
        "оборудования (Overall Equipment Effectiveness) является одним из "
        "ключевых показателей эффективности производственного предприятия. "
        "Внеплановые простои станков, конвейерных линий и погрузочной "
        "техники по причине поздно обнаруженных неисправностей "
        "приводят к прямым финансовым потерям, нарушению графика "
        "поставок и снижению маржинальности производства. По данным "
        "отраслевых исследований, до 30% продолжительности устранения "
        "инцидентов на промышленных предприятиях занимают не сами "
        "ремонтные работы, а сопутствующие организационные процессы: "
        "поиск виновного оборудования по бумажным журналам, обнаружение "
        "и доставка запасных частей со склада, согласование исполнителя.")

    add_paragraph(doc,
        "Решением указанных проблем является внедрение специализированной "
        "информационной системы учёта заявок на техническое обслуживание, "
        "в основе которой лежит спроектированная по правилам теории "
        "реляционных баз данных предметно-ориентированная база данных и "
        "веб-приложение для диспетчера и техников. Тема выпускной "
        "квалификационной работы — «Разработка базы данных для учёта "
        "заявок на техническое обслуживание» — является актуальной как "
        "с теоретической, так и с практической точки зрения.")

    add_paragraph(doc,
        "Объектом исследования являются бизнес-процессы технической "
        "службы предприятия: регистрация инцидента или планового ТО, "
        "назначение исполнителя, контроль выполнения работ, фиксация "
        "фактически использованных запчастей и закрытие заявки.")

    add_paragraph(doc,
        "Предметом исследования являются методы проектирования "
        "реляционных баз данных, средства реализации клиент-серверных "
        "веб-приложений на стеке Python — SQLite — HTML/CSS/JavaScript "
        "и подходы к обеспечению транзакционной целостности складских "
        "операций средствами СУБД и прикладного слоя.")

    add_paragraph(doc,
        "Цель работы — спроектировать в третьей нормальной форме базу "
        "данных учёта заявок на ТО, разработать веб-приложение "
        "диспетчера для её управления и подготовить пояснительную "
        "записку по ГОСТ КР 2.105-95.")

    add_paragraph(doc, "Для достижения поставленной цели в работе решаются "
                       "следующие задачи:")
    for item in [
        "проведён анализ предметной области и выделены сущности, "
        "образующие ядро информационной модели службы технической "
        "поддержки;",
        "разработана нормализованная до 3НФ реляционная модель базы "
        "данных с обоснованием каждого шага декомпозиции;",
        "реализован DDL-скрипт развёртывания в SQLite с ограничениями "
        "целостности, проверками CHECK на корректность дат "
        "(closed_at >= created_at), триггером автоматического аудита "
        "изменений статуса и защитой от отрицательных остатков на складе;",
        "разработан REST-API на языке Python (FastAPI), реализующий "
        "CRUD-операции над заявками, фильтрацию по приоритету и "
        "исполнителю, а также ключевой алгоритм закрытия заявки с "
        "атомарным списанием запчастей со склада;",
        "разработан адаптивный интерфейс диспетчера в концепции "
        "«Enterprise Dashboard» с боковой панелью, журналом заявок с "
        "цветовой маркировкой приоритетов и канбан-доской на "
        "технологиях HTML5, CSS3 и Vanilla JavaScript (Fetch API);",
        "проведено модульное и интеграционное тестирование "
        "разработанной системы.",
    ]:
        add_list_item(doc, item)

    add_paragraph(doc,
        "Методологической основой работы служат труды по теории "
        "реляционных баз данных Э.Ф. Кодда, К.Дж. Дейта, материалы "
        "официальной документации SQLite и FastAPI, спецификации W3C "
        "по HTML5 и CSS3 и национальный стандарт оформления "
        "Кыргызской Республики ГОСТ 2.105-95.")

    add_paragraph(doc,
        "Практическая значимость работы заключается в том, что "
        "разработанная система может быть внедрена в действующем "
        "производственном или транспортном предприятии без "
        "значительных доработок и без затрат на коммерческую СУБД, "
        "поскольку SQLite распространяется свободно и не требует "
        "выделенного сервера.")

    add_screenshot_marker(doc, "Главный экран разработанного веб-приложения MaintOps — Dashboard с KPI открытых заявок, карточками критических неисправностей и блоком запчастей ниже минимума")
    add_figure_caption(doc, "Рисунок В.1 — Главный экран приложения «MaintOps»")


# ----------------------------------------------------------------------------
# Глава 1 — База данных
# ----------------------------------------------------------------------------

def _build_chapter_1(doc):
    add_chapter_heading(doc, 1, "Проектирование базы данных")

    add_section_heading(doc, "1.1.", "Характеристика предметной области")
    add_paragraph(doc,
        "Предметная область — деятельность технической службы "
        "промышленного, транспортного или складского предприятия, "
        "эксплуатирующего десятки и сотни единиц оборудования: станков, "
        "конвейерных линий, насосов, систем вентиляции, погрузчиков. "
        "Каждая единица требует двух типов технического обслуживания: "
        "планового (по регламенту наработки или календарю) и аварийного "
        "(по факту инцидента). Оба процесса проходят через единое окно "
        "— систему учёта заявок, в которую попадают регистрация "
        "инцидента, назначение исполнителя, контроль выполнения работ, "
        "фиксация фактически использованных запчастей и закрытие "
        "заявки.")

    add_paragraph(doc, "В предметной области автором выделяются одиннадцать "
                       "сущностей, представленных в таблице 1.1.")
    add_table(doc,
        headers=["№", "Сущность", "Назначение"],
        rows=[
            ["1",  "equipment",              "Единицы оборудования предприятия"],
            ["2",  "equipment_types",        "Типы / категории оборудования"],
            ["3",  "staff",                  "Сотрудники (диспетчеры, инженеры, техники)"],
            ["4",  "maintenance_requests",   "Заявки на техническое обслуживание"],
            ["5",  "request_statuses",       "Справочник статусов обработки заявок"],
            ["6",  "spare_parts",            "Склад запчастей с остатками"],
            ["7",  "request_parts",          "Списание деталей под заявку (M:N)"],
            ["8",  "staff_roles",            "Справочник ролей сотрудников"],
            ["9",  "priorities",             "Приоритеты с SLA и цветовой кодировкой"],
            ["10", "locations",              "Места установки оборудования"],
            ["11", "request_status_history", "Аудит-журнал смен статусов заявок"],
        ],
        col_widths_cm=[1.0, 4.5, 10.5],
    )
    add_figure_caption(doc, "Таблица 1.1 — Состав отношений базы данных")

    add_section_heading(doc, "1.2.", "Цели и задачи раздела")
    add_paragraph(doc,
        "Целью настоящего раздела является получение нормализованной "
        "до третьей нормальной формы схемы реляционной базы данных, "
        "готовой к развёртыванию в СУБД SQLite. Для этого решаются "
        "следующие задачи: формирование ненормализованного "
        "представления заявки, последовательное приведение к 1НФ, "
        "2НФ и 3НФ с обоснованием каждого шага декомпозиции, а также "
        "формирование DDL-скрипта с ограничениями целостности и "
        "триггерами бизнес-логики.")

    add_section_heading(doc, "1.3.", "Приведение к первой нормальной форме (1НФ)")
    add_paragraph(doc,
        "Согласно общепринятому определению, отношение находится в "
        "первой нормальной форме, если все его атрибуты принимают "
        "только атомарные (неделимые) значения, повторяющиеся группы "
        "вынесены в отдельные кортежи, а для каждой строки определён "
        "первичный ключ. Автором рассмотрено ненормализованное "
        "«плоское» представление журнала заявок, типичное для "
        "бумажного учёта.")

    add_code_block(doc,
        "requests_flat (\n"
        "    request_id,\n"
        "    equipment_inv_number, equipment_name,\n"
        "    equipment_type_name, equipment_type_normative_mttr_hours,\n"
        "    location_name, location_building,\n"
        "    technician_fio, technician_phones,\n"
        "    technician_role_name,\n"
        "    priority_name, priority_color, priority_sla_hours,\n"
        "    status_name, status_color,\n"
        "    description, planned_date,\n"
        "    used_parts,                      -- 'Подшипник × 2, Ремень × 1'\n"
        "    created_at, closed_at, created_by_fio\n"
        ")")

    add_paragraph(doc,
        "В этой структуре выявлены три нарушения первой нормальной "
        "формы. Во-первых, поле technician_phones хранит список "
        "телефонов через запятую — нарушение атомарности. "
        "Во-вторых, поле used_parts хранит набор запчастей с "
        "количествами — типичная повторяющаяся группа. В-третьих, "
        "отсутствует явный первичный ключ. Автором проведены "
        "следующие преобразования: введён суррогатный ключ id во "
        "всех таблицах; для основного контакта сотрудника оставлено "
        "одно поле phone; для связи «заявка — запчасти с количеством» "
        "выделено самостоятельное связующее отношение request_parts "
        "(request_id, part_id, quantity_used, unit_price_at_use). "
        "После применения преобразований все отношения "
        "удовлетворяют 1НФ.")

    add_section_heading(doc, "1.4.", "Приведение ко второй нормальной форме (2НФ)")
    add_paragraph(doc,
        "Отношение находится во второй нормальной форме, если оно "
        "находится в 1НФ и не содержит частичных функциональных "
        "зависимостей неключевых атрибутов от части составного "
        "первичного ключа. Все основные отношения (equipment, staff, "
        "maintenance_requests, spare_parts) спроектированы с "
        "однополевым суррогатным ключом id, поэтому частичные "
        "зависимости в принципе невозможны: нет составного ключа — "
        "нет и его части.")
    add_paragraph(doc,
        "Особого внимания требует связующее отношение request_parts "
        "с естественным составным ключом (request_id, part_id). "
        "Помимо ключевых атрибутов, отношение содержит quantity_used "
        "(количество списанных деталей) и unit_price_at_use "
        "(цена детали на момент списания). Оба атрибута зависят от "
        "полной пары ключей: для одной запчасти в разных заявках "
        "значения отличаются, для одной заявки и разных запчастей "
        "тоже. Частичных зависимостей нет, отношение находится в 2НФ.")

    add_paragraph(doc, "Уникальность естественных бизнес-ключей обеспечивается "
                       "ограничениями UNIQUE уровня СУБД:")
    for item in [
        "equipment.inventory_number — у каждой единицы оборудования свой инвентарный номер;",
        "spare_parts.sku — артикул запчасти;",
        "priorities.code, request_statuses.code, staff_roles.code — справочные коды;",
        "staff.login и staff.email — учётные данные сотрудника;",
        "request_parts (request_id, part_id) — составной первичный ключ "
        "блокирует повторное списание одной запчасти в одну заявку.",
    ]:
        add_list_item(doc, item)

    add_section_heading(doc, "1.5.", "Приведение к третьей нормальной форме (3НФ)")
    add_paragraph(doc,
        "Отношение находится в третьей нормальной форме, если оно в 2НФ "
        "и не содержит транзитивных функциональных зависимостей "
        "неключевых атрибутов от первичного ключа. В исходной плоской "
        "структуре автором выявлены шесть групп транзитивных "
        "зависимостей:")
    add_table(doc,
        headers=["Источник", "Зависимый атрибут", "Транзит через"],
        rows=[
            ["request_id", "equipment_type_normative_mttr_hours", "equipment_type_name"],
            ["request_id", "location_building",                   "location_name"],
            ["request_id", "technician_role_name",                "technician_fio"],
            ["request_id", "priority_color, priority_sla_hours",  "priority_name"],
            ["request_id", "status_color",                        "status_name"],
            ["staff.id",   "role_name",                           "role_code"],
        ],
        col_widths_cm=[4.0, 6.0, 5.0],
    )
    add_figure_caption(doc, "Таблица 1.2 — Транзитивные зависимости")

    add_paragraph(doc,
        "Декомпозиция проведена путём выделения отдельных справочников. "
        "Характеристики типа оборудования (норматив MTTR, описание) "
        "хранятся только в equipment_types; адрес и корпус — только в "
        "locations; цвет приоритета и SLA-норматив в часах — только в "
        "priorities; цвет статуса — только в request_statuses; "
        "название роли — только в staff_roles; ФИО, телефон, email "
        "сотрудника — только в staff. В оперативных отношениях "
        "(maintenance_requests, request_parts, request_status_history) "
        "хранятся исключительно внешние ключи на справочники и "
        "собственные атрибуты сущности.")

    add_paragraph(doc,
        "Финансово-учётный аспект спроектирован с принципиальным "
        "разделением двух типов цен: текущей цены запчасти "
        "spare_parts.unit_price (отражает рыночную стоимость на "
        "сегодня) и исторической цены request_parts.unit_price_at_use "
        "(фиксируется в момент списания). Это техническое разделение "
        "сохраняет историческую достоверность отчётов по стоимости "
        "закрытых заявок при произвольном изменении прейскуранта в "
        "будущем.")

    add_section_heading(doc, "1.6.", "Логическая схема базы данных")
    add_paragraph(doc,
        "Финальная нормализованная модель содержит одиннадцать "
        "отношений. Связи реализуются ограничениями FOREIGN KEY со "
        "стратегиями ON DELETE RESTRICT для справочников и "
        "ON DELETE CASCADE для журнала истории (удаление заявки "
        "каскадом удаляет связанную историю статусов).")
    add_screenshot_marker(doc, "ER-диаграмма базы данных учёта заявок на ТО в 3НФ, построенная в DBeaver, с одиннадцатью таблицами и связями")
    add_figure_caption(doc, "Рисунок 1.1 — Логическая схема базы данных в 3НФ")

    add_paragraph(doc, "Ключевые функциональные зависимости между отношениями:")
    for item in [
        "staff_roles 1 → * staff;",
        "locations 1 → * equipment; equipment_types 1 → * equipment;",
        "equipment 1 → * maintenance_requests;",
        "priorities 1 → * maintenance_requests; request_statuses 1 → * maintenance_requests;",
        "staff 1 → * maintenance_requests (как создатель и как исполнитель);",
        "maintenance_requests 1 → * request_parts * ← 1 spare_parts (связь M:N через связующую таблицу);",
        "maintenance_requests 1 → * request_status_history.",
    ]:
        add_list_item(doc, item)

    add_section_heading(doc, "1.7.", "Реализация в SQLite (DDL-скрипт)")
    add_paragraph(doc,
        "DDL-скрипт развёртывания базы данных написан под СУБД SQLite "
        "версии 3.35 и выше. Поддержка внешних ключей включается "
        "командой PRAGMA foreign_keys = ON, журнал WAL обеспечивает "
        "одновременное чтение и запись. Скрипт содержит создание "
        "одиннадцати таблиц, вспомогательных индексов и двух "
        "триггеров бизнес-логики.")

    add_paragraph(doc, "Ключевые CHECK-ограничения уровня СУБД:")
    for item in [
        "spare_parts.quantity >= 0, spare_parts.min_quantity >= 0 — неотрицательный остаток на складе;",
        "request_parts.quantity_used > 0, request_parts.unit_price_at_use >= 0;",
        "maintenance_requests.closed_at >= created_at — дата закрытия не может предшествовать дате открытия;",
        "maintenance_requests.started_at >= created_at — дата начала работы не предшествует регистрации;",
        "priorities.sla_hours > 0, equipment_types.normative_mttr_hours > 0;",
        "length(trim(title)) >= 5 — содержательное наименование заявки.",
    ]:
        add_list_item(doc, item)

    add_paragraph(doc, "Ниже приведены ключевые фрагменты DDL-скрипта.")

    add_code_block(doc,
        "CREATE TABLE maintenance_requests (\n"
        "    id              INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    equipment_id    INTEGER NOT NULL,\n"
        "    priority_id     INTEGER NOT NULL,\n"
        "    status_id       INTEGER NOT NULL,\n"
        "    title           TEXT    NOT NULL CHECK (length(trim(title)) >= 5),\n"
        "    description     TEXT,\n"
        "    planned_date    DATE,\n"
        "    assigned_to     INTEGER,\n"
        "    created_by      INTEGER NOT NULL,\n"
        "    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
        "    started_at      TIMESTAMP,\n"
        "    closed_at       TIMESTAMP,\n"
        "    completion_note TEXT,\n"
        "    CHECK (closed_at IS NULL OR closed_at >= created_at),\n"
        "    FOREIGN KEY (equipment_id) REFERENCES equipment        (id),\n"
        "    FOREIGN KEY (priority_id)  REFERENCES priorities       (id),\n"
        "    FOREIGN KEY (status_id)    REFERENCES request_statuses (id),\n"
        "    FOREIGN KEY (assigned_to)  REFERENCES staff            (id) ON DELETE SET NULL,\n"
        "    FOREIGN KEY (created_by)   REFERENCES staff            (id)\n"
        ");")

    add_paragraph(doc,
        "Триггер trg_request_status_audit автоматически фиксирует "
        "каждое изменение статуса заявки в журнале "
        "request_status_history, что создаёт неизменяемый аудит-след "
        "для последующих разбирательств. Триггер trg_parts_no_overdraft "
        "выполняет резервную защиту от ухода остатка на складе в "
        "отрицательную область — даже при ошибке прикладного слоя "
        "СУБД отклонит соответствующий UPDATE.")

    add_code_block(doc,
        "CREATE TRIGGER trg_request_status_audit\n"
        "AFTER UPDATE OF status_id ON maintenance_requests\n"
        "FOR EACH ROW\n"
        "WHEN OLD.status_id != NEW.status_id\n"
        "BEGIN\n"
        "    INSERT INTO request_status_history\n"
        "        (request_id, old_status_id, new_status_id, changed_by, note)\n"
        "    VALUES (\n"
        "        NEW.id, OLD.status_id, NEW.status_id,\n"
        "        COALESCE(NEW.assigned_to, NEW.created_by),\n"
        "        'Автоматическая регистрация смены статуса'\n"
        "    );\n"
        "END;\n"
        "\n"
        "CREATE TRIGGER trg_parts_no_overdraft\n"
        "BEFORE UPDATE OF quantity ON spare_parts\n"
        "FOR EACH ROW\n"
        "WHEN NEW.quantity < 0\n"
        "BEGIN\n"
        "    SELECT RAISE(ABORT, 'Невозможно списать больше, чем имеется на складе');\n"
        "END;")

    add_screenshot_marker(doc, "Результат успешного выполнения DDL-скрипта в DB Browser for SQLite — список из 11 таблиц с количеством записей")
    add_figure_caption(doc, "Рисунок 1.2 — Структура базы данных после развёртывания")

    add_section_heading(doc, "1.8.", "Выводы по разделу")
    add_paragraph(doc,
        "В первом разделе автором выделены одиннадцать сущностей "
        "предметной области; последовательно проведена нормализация "
        "модели до третьей нормальной формы с обоснованием каждого "
        "шага декомпозиции; разработан DDL-скрипт развёртывания в "
        "SQLite, включающий ограничения целостности (CHECK-проверки "
        "корректности дат и неотрицательности остатков) и два "
        "триггера бизнес-логики — автоматический аудит смен статусов "
        "и защита от отрицательного остатка на складе.")


# ----------------------------------------------------------------------------
# Глава 2 — Backend
# ----------------------------------------------------------------------------

def _build_chapter_2(doc):
    add_chapter_heading(doc, 2, "Программная реализация серверной части")

    add_section_heading(doc, "2.1.", "Обоснование выбора инструментальных средств")
    add_paragraph(doc,
        "Для реализации серверной части автором выбран язык "
        "программирования Python версии 3.10+ и фреймворк FastAPI "
        "0.115. Выбор обусловлен совокупностью факторов: высокой "
        "производительностью на основе ASGI-сервера Uvicorn; "
        "автоматической генерацией интерактивной OpenAPI-документации; "
        "декларативным механизмом валидации входных данных Pydantic "
        "2.x; широким распространением стека в учебной и промышленной "
        "разработке. В качестве СУБД использована встроенная база "
        "данных SQLite, обращение к которой выполняется через "
        "стандартный модуль sqlite3 без использования ORM — такое "
        "решение обеспечивает прозрачное понимание выполняющихся "
        "SQL-запросов, что особенно ценно при анализе корректности "
        "нормализации.")

    add_section_heading(doc, "2.2.", "Архитектура серверного приложения")
    add_paragraph(doc,
        "Серверная часть организована по слоистой архитектуре. На "
        "нижнем уровне находится модуль database.py, отвечающий за "
        "создание подключения к SQLite, выполнение PRAGMA-настроек и "
        "применение схемы. Над ним расположен слой бизнес-логики, "
        "реализованный в виде четырёх роутеров FastAPI: "
        "reference_router (справочники), equipment_router "
        "(оборудование и фильтр критических неисправностей), "
        "parts_router (склад запчастей с корректировкой остатков) и "
        "requests_router (CRUD-операции над заявками и ключевой "
        "алгоритм закрытия). Главный модуль main.py объединяет "
        "роутеры в единое приложение и подключает статические "
        "файлы клиентской части по адресу /static.")
    add_screenshot_marker(doc, "Структура каталогов проекта maintenance_requests с подсветкой backend/, frontend/, scripts/")
    add_figure_caption(doc, "Рисунок 2.1 — Структура каталогов проекта")

    add_section_heading(doc, "2.3.", "CRUD-эндпоинты для заявок и оборудования")
    add_paragraph(doc, "В системе реализованы следующие REST-эндпоинты:")
    add_table(doc,
        headers=["Маршрут", "Метод", "Назначение"],
        rows=[
            ["/api/requests",                "GET",    "Список заявок с фильтрами"],
            ["/api/requests",                "POST",   "Регистрация новой заявки"],
            ["/api/requests/{id}",           "GET, PUT, DELETE", "Карточка заявки"],
            ["/api/requests/{id}/assign",    "POST",   "Назначение исполнителя"],
            ["/api/requests/{id}/status",    "POST",   "Смена статуса"],
            ["/api/requests/{id}/complete",  "POST",   "Закрытие со списанием запчастей"],
            ["/api/requests/{id}/history",   "GET",    "Журнал смен статусов"],
            ["/api/equipment",               "GET",    "Каталог оборудования"],
            ["/api/equipment/critical",      "GET",    "Оборудование с открытыми критическими заявками"],
            ["/api/parts",                   "GET, POST", "Склад запчастей"],
            ["/api/parts/{id}/adjust",       "POST",   "Корректировка остатка"],
            ["/api/priorities, /statuses, /staff", "GET", "Справочники"],
        ],
        col_widths_cm=[5.5, 2.5, 8.0],
    )
    add_figure_caption(doc, "Таблица 2.1 — Перечень REST-эндпоинтов")

    add_paragraph(doc,
        "Фильтрация заявок поддерживается тремя независимыми "
        "параметрами строки запроса: priority (код приоритета), "
        "status (код статуса), assigned_to (идентификатор "
        "исполнителя). Опциональный флаг open_only=true сокращает "
        "выборку до незакрытых заявок и используется на канбан-доске. "
        "Эндпоинт /api/equipment/critical отдельно выделяет "
        "оборудование, по которому имеются открытые заявки с "
        "приоритетом «Критический» — это основа для блока тревожных "
        "карточек на главном экране диспетчера.")

    add_section_heading(doc, "2.4.", "Алгоритм закрытия заявки со списанием запчастей")
    add_paragraph(doc,
        "Ключевым бизнес-алгоритмом серверной части является "
        "процедура перевода заявки в статус «Выполнена» с "
        "одновременным списанием использованных запчастей со склада. "
        "Алгоритм реализован в эндпоинте POST /api/requests/{id}/complete "
        "и состоит из следующих последовательных шагов.")

    for i, step in enumerate([
        "Извлечение заявки по идентификатору с JOIN на request_statuses; "
        "при отсутствии — возврат HTTP 404. Если статус заявки уже "
        "закрытый (is_closed = 1) — возврат HTTP 400 «Заявка уже закрыта».",
        "Загрузка актуальных данных для каждой затребованной "
        "запчасти из таблицы spare_parts (артикул, наименование, "
        "текущий остаток, текущая цена).",
        "Проверка достаточности остатка по КАЖДОЙ позиции "
        "технологической карты. Если хотя бы одной детали не хватает "
        "— немедленный отказ HTTP 400 с указанием конкретной "
        "запчасти, требуемого количества и фактического остатка. "
        "Принципиально, что отказ происходит ДО внесения каких-либо "
        "изменений в базу — это гарантирует, что заявка не "
        "останется в полусписанном состоянии.",
        "Если все проверки пройдены, для каждой запчасти "
        "выполняются две атомарные операции: вставка строки в "
        "request_parts с фиксацией исторической цены unit_price_at_use; "
        "уменьшение текущего остатка spare_parts.quantity на "
        "соответствующее количество.",
        "Перевод заявки в статус 'done', установка closed_at = "
        "CURRENT_TIMESTAMP и сохранение комментария мастера в поле "
        "completion_note.",
        "Триггер БД trg_request_status_audit автоматически фиксирует "
        "смену статуса в request_status_history без явного участия "
        "прикладного слоя.",
        "Возврат клиенту обновлённой заявки в формате JSON, "
        "содержащей полный список списанных запчастей с их "
        "историческими ценами и итоговой стоимостью ремонта.",
    ], start=1):
        add_paragraph(doc, f"{i}. {step}", first_line_indent=False)

    add_screenshot_marker(doc, "Модальное окно карточки заявки в веб-приложении с формой закрытия: выбор запчастей, количество, комментарий мастера и кнопка «Закрыть заявку»")
    add_figure_caption(doc, "Рисунок 2.2 — Интерфейс закрытия заявки")

    add_code_block(doc,
        "# Фрагмент: проверка ДО списания\n"
        "for line in parts_used:\n"
        "    cur.execute('SELECT id, sku, name, quantity FROM spare_parts WHERE id = ?',\n"
        "                (line.part_id,))\n"
        "    sp = cur.fetchone()\n"
        "    if sp is None:\n"
        "        raise HTTPException(400, f'Запчасть #{line.part_id} не найдена')\n"
        "    if sp['quantity'] < line.quantity:\n"
        "        raise HTTPException(400,\n"
        "            f'Недостаточно «{sp[\"name\"]}» ({sp[\"sku\"]}): '\n"
        "            f'требуется {line.quantity}, доступно {sp[\"quantity\"]}')")

    add_section_heading(doc, "2.5.", "Транзакционная целостность операций")
    add_paragraph(doc,
        "Все шаги алгоритма закрытия выполняются в рамках единого "
        "транзакционного контекста, организованного контекстным "
        "менеджером db_cursor(commit=True). При возникновении любого "
        "исключения внутри блока контекстный менеджер автоматически "
        "откатывает все произведённые изменения командой rollback(). "
        "Это гарантирует, что в базе данных не остаётся «полу-"
        "закрытых» заявок (запчасть списана, но статус заявки не "
        "обновился) или «полу-списаний» (одна позиция уменьшена, "
        "другая нет). При успешном завершении выполняется единый "
        "commit().")

    add_paragraph(doc,
        "Дополнительная защита целостности обеспечивается на уровне "
        "СУБД триггером trg_parts_no_overdraft, который отклоняет "
        "любой UPDATE, приводящий к отрицательному остатку детали. "
        "Это типовой шаблон защиты «глубже прикладного слоя»: даже "
        "при ручной модификации базы данных через консольный клиент "
        "или ошибке в коде нового модуля, не учитывающего проверку "
        "остатка, СУБД сама заблокирует операцию.")

    add_section_heading(doc, "2.6.", "Выводы по разделу")
    add_paragraph(doc,
        "Во втором разделе автором обоснован выбор стека Python — "
        "FastAPI — SQLite; реализована слоистая архитектура "
        "серверной части с четырьмя роутерами; разработан "
        "ключевой бизнес-алгоритм закрытия заявки с атомарной "
        "проверкой и списанием всех запчастей в единой транзакции; "
        "реализована двухуровневая защита целостности данных "
        "(прикладной слой + триггеры СУБД).")


# ----------------------------------------------------------------------------
# Глава 3 — Frontend
# ----------------------------------------------------------------------------

def _build_chapter_3(doc):
    add_chapter_heading(doc, 3, "Программная реализация клиентской части")

    add_section_heading(doc, "3.1.", "UX/UI-концепция «Enterprise Dashboard»")
    add_paragraph(doc,
        "Визуальное оформление интерфейса диспетчера построено в "
        "концепции «Enterprise Dashboard» — современный корпоративный "
        "стиль с контрастной тёмно-индиго боковой панелью, светлым "
        "контентом и продуманной системой цветовой маркировки. "
        "Доминирующий цвет — индиго #3B82F6 — символизирует "
        "стабильность и доверие; критические заявки и неисправности "
        "выделяются мягким пастельно-красным фоном #FEE2E2 с акцентным "
        "#B91C1C, средний приоритет — пастельно-жёлтым #FEF3C7 с #92400E, "
        "низкий — пастельно-зелёным #D1FAE5 с #065F46. Использование "
        "пастельных фонов вместо насыщенных позволяет одновременно "
        "сохранять читабельность текста и обеспечивать мгновенное "
        "визуальное распознавание уровня срочности.")
    add_screenshot_marker(doc, "Палитра «Enterprise Dashboard» с примерами оформления приоритетов: пастельно-красный фон для критических, жёлтый для средних, зелёный для низких")
    add_figure_caption(doc, "Рисунок 3.1 — Цветовая палитра приоритетов")

    add_paragraph(doc,
        "Все цвета вынесены в CSS Custom Properties в селекторе :root, "
        "что позволяет менять тему оформления в одной точке без правки "
        "исходного кода. Скругления элементов составляют 6–8 пикселей, "
        "что соответствует общепринятой практике корпоративных "
        "интерфейсов и сохраняет деловой характер дизайна. Все "
        "интерактивные элементы (кнопки, карточки) имеют плавные "
        "hover-эффекты с лёгким поднятием translateY(-2px) и усилением "
        "тени.")

    add_section_heading(doc, "3.2.", "Структура интерфейса диспетчера")
    add_paragraph(doc,
        "Интерфейс диспетчера реализован как одностраничное приложение "
        "(SPA) с фиксированной боковой панелью и пятью основными "
        "разделами: «Dashboard» с KPI открытых заявок, карточками "
        "критических неисправностей и блоком запчастей ниже минимума; "
        "«Канбан-доска» — четырёхколоночное представление открытых "
        "заявок по статусам; «Журнал заявок» — табличное представление "
        "с расширенными фильтрами и цветовой маркировкой строк; "
        "«Оборудование» — каталог с подсветкой единиц, имеющих "
        "критические заявки; «Склад запчастей» — таблица с подсветкой "
        "позиций ниже минимального остатка.")
    add_screenshot_marker(doc, "Канбан-доска заявок в четыре колонки (Получена, В работе, На проверке, Выполнена) с карточками заявок, имеющих цветную полосу слева в зависимости от приоритета")
    add_figure_caption(doc, "Рисунок 3.2 — Канбан-доска заявок")

    add_section_heading(doc, "3.3.", "Цветовая маркировка приоритетов в таблице")
    add_paragraph(doc,
        "В разделе «Журнал заявок» каждая строка таблицы получает "
        "цветовую заливку и левую вертикальную полосу-индикатор в "
        "зависимости от приоритета. Реализация выполнена средствами "
        "CSS — JavaScript только добавляет к элементу tr класс "
        "row--critical, row--medium или row--low. CSS-правила "
        "сохраняют пастельный фон и насыщенный цвет полосы, что "
        "сохраняет читаемость текста, не перегружая интерфейс. Для "
        "закрытых заявок применяется класс row--closed с приглушённой "
        "прозрачностью 0.55 — это визуально отделяет историческое от "
        "актуального.")
    add_code_block(doc,
        ".data-table--rich tbody tr {\n"
        "    transition: background .15s;\n"
        "    border-left: 4px solid transparent;\n"
        "}\n"
        ".data-table--rich tbody tr.row--critical {\n"
        "    background: var(--p-critical-bg);\n"
        "    border-left-color: var(--danger);\n"
        "}\n"
        ".data-table--rich tbody tr.row--medium {\n"
        "    background: var(--p-medium-bg);\n"
        "    border-left-color: var(--warn);\n"
        "}\n"
        ".data-table--rich tbody tr.row--low {\n"
        "    background: var(--p-low-bg);\n"
        "    border-left-color: var(--success);\n"
        "}")
    add_screenshot_marker(doc, "Журнал заявок с цветовой маркировкой строк: критическая заявка с красной заливкой, средняя с жёлтой, низкая с зелёной, закрытые с серой")
    add_figure_caption(doc, "Рисунок 3.3 — Цветовая маркировка приоритетов")

    add_section_heading(doc, "3.4.", "Канбан-доска заявок на CSS Grid")
    add_paragraph(doc,
        "Канбан-доска реализована средствами CSS Grid Layout с "
        "конфигурацией grid-template-columns: repeat(4, 1fr), что "
        "обеспечивает равное распределение четырёх колонок открытых "
        "статусов: «Получена», «В работе», «На проверке», "
        "«Выполнена». Каждая колонка имеет заголовок с цветной "
        "точкой-индикатором и счётчиком количества заявок, а тело "
        "колонки содержит список карточек заявок с левой цветной "
        "полосой по приоритету. Карточки кликабельны: при щелчке "
        "открывается модальное окно с полной информацией.")

    add_section_heading(doc, "3.5.", "Назначение исполнителя «в один клик»")
    add_paragraph(doc,
        "Назначение исполнителя выполнено принципиально без "
        "промежуточных модальных окон. В каждой строке таблицы "
        "«Журнал заявок» в колонке «Исполнитель» отображается "
        "выпадающий список <select> с перечнем активных техников и "
        "инженеров. Выбор сотрудника из списка немедленно "
        "инициирует POST-запрос /api/requests/{id}/assign и при "
        "успехе обновляет таблицу. Это даёт диспетчеру "
        "максимально быстрый рабочий процесс — назначение "
        "выполняется за один щелчок мыши без открытия карточек.")
    add_paragraph(doc,
        "Дополнительно серверная логика выполняет «умное» "
        "поведение: если на момент назначения заявка была в "
        "статусе «Получена», она автоматически переводится в "
        "статус «В работе» и фиксируется поле started_at — это "
        "соответствует реальной бизнес-логике предприятия "
        "(назначение исполнителя = начало работ).")
    add_screenshot_marker(doc, "Журнал заявок с раскрытым выпадающим списком исполнителей в колонке «Исполнитель» — назначение в один клик без промежуточных модалок")
    add_figure_caption(doc, "Рисунок 3.4 — Назначение исполнителя в один клик")

    add_section_heading(doc, "3.6.", "Динамическое закрытие заявки и Fetch API")
    add_paragraph(doc,
        "Модальное окно карточки заявки содержит интегрированную форму "
        "закрытия с динамическим добавлением строк запчастей: "
        "JavaScript-функция addRow() клонирует шаблон строки с "
        "выпадающим списком позиций склада и полем количества; "
        "пользователь может добавить произвольное число строк или "
        "удалить лишние. При отправке формы клиент собирает массив "
        "parts_used и выполняет POST-запрос на /api/requests/{id}/complete. "
        "При успешном ответе модальное окно закрывается, выполняется "
        "повторная загрузка справочников (включая обновлённые остатки "
        "на складе) и перерисовка всех видимых разделов. При ошибке "
        "(например, нехватка запчастей) клиент выводит сообщение от "
        "сервера во всплывающем уведомлении (toast) красного цвета.")

    add_code_block(doc,
        "completeForm.addEventListener('submit', async e => {\n"
        "    e.preventDefault();\n"
        "    const parts_used = Array.from(partsRows.querySelectorAll('div'))\n"
        "        .map(row => ({\n"
        "            part_id:  +row.querySelector('.part-sel').value,\n"
        "            quantity: +row.querySelector('.part-qty').value,\n"
        "        }));\n"
        "    try {\n"
        "        await apiPost(`/api/requests/${requestId}/complete`,\n"
        "                      { parts_used, completion_note });\n"
        "        toast('Заявка закрыта, запчасти списаны', 'success');\n"
        "        closeModal();\n"
        "        await preload();\n"
        "        renderRequests(); renderBoard(); renderDashboard();\n"
        "    } catch (err) { toast(err.message, 'error'); }\n"
        "});")

    add_section_heading(doc, "3.7.", "Адаптивная вёрстка")
    add_paragraph(doc,
        "Интерфейс адаптирован для отображения на устройствах с "
        "шириной экрана от 360 пикселей и выше. На устройствах "
        "планшетной ширины (@media max-width: 1100px) сетка KPI "
        "перестраивается из четырёхколоночной в двухколоночную, а "
        "канбан-доска — из четырёхколоночной в двухколоночную "
        "(колонки переносятся). На смартфонах "
        "(@media max-width: 768px) ширина боковой панели сжимается "
        "до 72 пикселей, оставляя только иконки пунктов меню; "
        "канбан становится одноколоночным; таблицы сохраняют "
        "горизонтальную прокрутку.")
    add_screenshot_marker(doc, "Параллельный показ интерфейса в трёх разрешениях: десктоп (1920×1080), планшет (1024×768), смартфон (375×812) — на смартфоне sidebar сжимается, остаются только иконки")
    add_figure_caption(doc, "Рисунок 3.5 — Адаптивность интерфейса")

    add_section_heading(doc, "3.8.", "Выводы по разделу")
    add_paragraph(doc,
        "В третьем разделе автором разработан адаптивный интерфейс "
        "диспетчера/инженера в концепции «Enterprise Dashboard» на "
        "технологиях HTML5, CSS3 и Vanilla JavaScript с Fetch API. "
        "Реализованы пять основных разделов с боковым меню, "
        "цветовая маркировка приоритетов в таблице заявок, "
        "канбан-доска на CSS Grid, назначение исполнителя «в один "
        "клик» без модальных окон, динамическая форма закрытия "
        "заявки с произвольным числом запчастей и адаптивная "
        "вёрстка для устройств разных размеров.")


# ----------------------------------------------------------------------------
# Глава 4 — Тестирование
# ----------------------------------------------------------------------------

def _build_chapter_4(doc):
    add_chapter_heading(doc, 4, "Тестирование разработанной системы")

    add_section_heading(doc, "4.1.", "Тестирование ключевого алгоритма закрытия заявки")
    add_paragraph(doc,
        "Тестирование ключевого бизнес-алгоритма — закрытия заявки со "
        "списанием запчастей — выполнено по семи сценариям, "
        "охватывающим как позитивные, так и негативные ветви "
        "алгоритма. Результаты сведены в таблицу 4.1.")
    add_table(doc,
        headers=["№", "Сценарий", "Ожидаемый результат", "Результат"],
        rows=[
            ["1", "Закрытие открытой заявки с двумя запчастями (по 1 шт каждой)",
                  "200, статус → done, остатки уменьшены, аудит обновлён", "Пройден"],
            ["2", "Закрытие без запчастей (только смена статуса)",
                  "200, статус → done, остатки не меняются", "Пройден"],
            ["3", "Запрос больше, чем есть на складе",
                  "400 с указанием конкретной запчасти и доступного количества", "Пройден"],
            ["4", "Повторное закрытие уже закрытой заявки",
                  "400 'Заявка уже закрыта'", "Пройден"],
            ["5", "Закрытие несуществующей заявки",
                  "404 'Заявка не найдена'", "Пройден"],
            ["6", "Запрос на несуществующую запчасть",
                  "400 'Запчасть не найдена'", "Пройден"],
            ["7", "Триггер аудита фиксирует смену статуса",
                  "Появляется запись в request_status_history",   "Пройден"],
        ],
        col_widths_cm=[1.0, 5.5, 5.5, 3.0],
    )
    add_figure_caption(doc, "Таблица 4.1 — Тестирование алгоритма закрытия заявки")
    add_screenshot_marker(doc, "Терминал с curl-запросами POST /api/requests/.../complete: успешное закрытие (200) и попытка списания при нехватке запчастей (400 с указанием детали)")
    add_figure_caption(doc, "Рисунок 4.1 — Тестирование закрытия через curl")

    add_section_heading(doc, "4.2.", "Тестирование REST-API и фильтрации")
    add_paragraph(doc,
        "Тестирование REST-эндпоинтов выполнено через интерактивную "
        "документацию Swagger UI. Покрыты следующие группы маршрутов: "
        "получение списка заявок с фильтрами по приоритету "
        "(?priority=critical), статусу (?status=in_work), "
        "исполнителю (?assigned_to=3); CRUD-операции над заявками "
        "(создание, редактирование, удаление); назначение "
        "исполнителя через /assign; смена статуса через /status; "
        "получение списка критических единиц оборудования через "
        "/api/equipment/critical; корректировка остатка детали "
        "через /api/parts/{id}/adjust. Все сценарии прошли "
        "успешно.")
    add_screenshot_marker(doc, "Swagger UI с раскрытым эндпоинтом GET /api/requests и применёнными фильтрами по приоритету и статусу — ответ 200 с JSON-массивом отфильтрованных заявок")
    add_figure_caption(doc, "Рисунок 4.2 — Тестирование фильтрации через Swagger UI")

    add_section_heading(doc, "4.3.", "Тестирование пользовательского интерфейса")
    add_paragraph(doc,
        "Тестирование пользовательского интерфейса выполнено в "
        "браузерах Google Chrome 120, Mozilla Firefox 122 и "
        "Apple Safari 17. Проверены следующие аспекты: корректность "
        "отображения Dashboard с KPI и блоком критических заявок; "
        "корректность построения канбан-доски с распределением "
        "карточек по колонкам; цветовая маркировка строк в журнале "
        "заявок; работа фильтров; назначение исполнителя «в один "
        "клик» прямо из строки таблицы; модальное окно карточки "
        "заявки с историей статусов; динамическая форма закрытия "
        "заявки; всплывающие уведомления при успехе и ошибках; "
        "адаптивная вёрстка на трёх типовых разрешениях. Все "
        "проверки пройдены успешно.")
    add_screenshot_marker(doc, "Параллельный показ интерфейса в трёх типовых разрешениях экрана: 1920×1080 (десктоп), 1024×768 (планшет), 375×812 (смартфон)")
    add_figure_caption(doc, "Рисунок 4.3 — Кроссустройственное тестирование")

    add_section_heading(doc, "4.4.", "Выводы по разделу")
    add_paragraph(doc,
        "В четвёртом разделе автором проведено тестирование всех "
        "уровней системы: ключевого бизнес-алгоритма закрытия "
        "заявки (семь сценариев), REST-API с фильтрацией через "
        "Swagger UI и пользовательского интерфейса в трёх браузерах "
        "и на устройствах разных размеров. Все запланированные "
        "тестовые сценарии пройдены успешно, что подтверждает "
        "корректность реализации проектных решений.")


# ----------------------------------------------------------------------------
# Заключение и список литературы
# ----------------------------------------------------------------------------

def _build_conclusion(doc):
    doc.add_page_break()
    add_centered(doc, "ЗАКЛЮЧЕНИЕ", bold=True, space_after=14)

    add_paragraph(doc,
        "В рамках выпускной квалификационной работы автором "
        "разработан полноценный программный комплекс для "
        "автоматизации деятельности технической службы предприятия, "
        "состоящий из спроектированной в третьей нормальной форме "
        "реляционной базы данных и клиент-серверного веб-приложения "
        "диспетчера. Все поставленные во введении задачи решены в "
        "полном объёме.")

    add_paragraph(doc,
        "Основные результаты работы заключаются в следующем. "
        "Во-первых, проведён детальный анализ предметной области "
        "учёта заявок на ТО; выделены одиннадцать сущностей и "
        "последовательно проведена их нормализация до 3НФ с "
        "обоснованием каждого шага декомпозиции; разработан "
        "DDL-скрипт развёртывания в SQLite с CHECK-валидацией "
        "(дата закрытия не может быть раньше создания, остаток "
        "запчастей не может быть отрицательным) и двумя триггерами "
        "бизнес-логики. Во-вторых, реализована серверная часть "
        "на FastAPI с четырьмя роутерами и полным набором "
        "REST-эндпоинтов, включая фильтрацию заявок по приоритету "
        "и исполнителю. В-третьих, реализован ключевой "
        "бизнес-алгоритм закрытия заявки с атомарной проверкой "
        "достаточности запчастей до начала списания, "
        "транзакционной целостностью операций и автоматическим "
        "обновлением остатков склада. В-четвёртых, разработан "
        "адаптивный интерфейс диспетчера в концепции «Enterprise "
        "Dashboard» с боковой панелью, цветовой маркировкой "
        "приоритетов, канбан-доской на CSS Grid и назначением "
        "исполнителя «в один клик».")

    add_paragraph(doc,
        "Практическая значимость работы состоит в том, что "
        "разработанная система может быть внедрена в действующем "
        "производственном, транспортном или складском предприятии "
        "без значительных доработок и без затрат на коммерческое "
        "программное обеспечение. Дальнейшим направлением развития "
        "системы автор видит интеграцию с системой автоматического "
        "оповещения исполнителей через SMS- и email-каналы, "
        "построение модуля плановой статистики по среднему времени "
        "ремонта (MTTR) и среднему времени наработки на отказ "
        "(MTBF) по каждой единице оборудования, а также разработку "
        "мобильного приложения для технического персонала.")


def _build_references(doc):
    doc.add_page_break()
    add_centered(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", bold=True, space_after=14)

    refs = [
        "Дейт К.Дж. Введение в системы баз данных, 8-е изд. — М.: Вильямс, 2017. — 1328 с.",
        "Кодд Э.Ф. Реляционная модель данных для больших разделяемых банков данных. — "
        "Communications of the ACM, 1970. — Vol. 13, No. 6. — pp. 377—387.",
        "Гарсиа-Молина Г., Ульман Дж., Уидом Дж. Системы баз данных. Полный курс. — "
        "М.: Вильямс, 2003. — 1088 с.",
        "Кузнецов С.Д. Основы баз данных. — М.: Интернет-университет "
        "информационных технологий: БИНОМ. Лаборатория знаний, 2007. — 484 с.",
        "Дакетт Дж. HTML и CSS. Разработка и дизайн веб-сайтов. — М.: Эксмо, 2017. — 480 с.",
        "ГОСТ 2.105-95. Единая система конструкторской документации. Общие требования "
        "к текстовым документам. — Бишкек: Кыргызстандарт, 1995. — 30 с.",
        "ГОСТ 18322-2016. Система технического обслуживания и ремонта техники. "
        "Термины и определения. — М.: Стандартинформ, 2017. — 18 с.",
        "Официальная документация фреймворка FastAPI. — URL: https://fastapi.tiangolo.com",
        "Официальная документация СУБД SQLite. — URL: https://www.sqlite.org/docs.html",
        "Pydantic V2 documentation. — URL: https://docs.pydantic.dev/2.x/",
        "Спецификация HTML Living Standard, WHATWG. — URL: https://html.spec.whatwg.org",
        "Спецификация CSS Grid Layout Module Level 1, W3C. — URL: https://www.w3.org/TR/css-grid-1/",
        "MDN Web Docs: Using the Fetch API. — URL: https://developer.mozilla.org/ru/docs/Web/API/Fetch_API/Using_Fetch",
        "OpenAPI Specification 3.1. — URL: https://spec.openapis.org/oas/v3.1.0",
        "ГОСТ Р 7.0.97-2016. Система стандартов по информации, библиотечному и "
        "издательскому делу. Организационно-распорядительная документация. — М.: "
        "Стандартинформ, 2017.",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                first_line_indent=False, space_after=4)
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        _set_run_font(p.add_run(f"{i}. {ref}"))


# ----------------------------------------------------------------------------
# Главный собиратель
# ----------------------------------------------------------------------------

def build_document() -> Path:
    doc = Document()
    _setup_document(doc)
    _build_title_page(doc)
    _build_contents(doc)
    _build_introduction(doc)
    _build_chapter_1(doc)
    _build_chapter_2(doc)
    _build_chapter_3(doc)
    _build_chapter_4(doc)
    _build_conclusion(doc)
    _build_references(doc)
    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_document()
    size_kb = path.stat().st_size / 1024
    print(f"Документ сгенерирован: {path} ({size_kb:.1f} КБ)")
