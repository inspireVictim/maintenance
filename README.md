# Учёт заявок на техническое обслуживание (ВКР)

## Стек
- SQLite 3.35+
- Python 3.10+ / FastAPI / Pydantic 2
- HTML5 / CSS3 / Vanilla JS (Fetch API)

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m backend.init_db
uvicorn backend.main:app --port 8004 --reload
```
Откройте http://localhost:8004/ в браузере.

## Сборка ПЗ
```bash
python scripts/generate_pz.py
```
Результат: `ПЗ_Учет_Заявок_на_Техническое_Обслуживание.docx`
