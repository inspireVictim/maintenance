/* ============================================================
   MaintOps — клиент диспетчера/инженера
   Vanilla JS + Fetch API
   ============================================================ */

const STATE = {
    priorities: [], statuses: [], staff: [], equipment: [], parts: [], requests: [],
    filterPriority: '', filterStatus: '', filterAssignee: '', filterOpenOnly: false,
    today: new Date().toISOString().slice(0, 10),
    currentUserId: 2,    // Петрова — диспетчер (в учебной версии «текущий пользователь» зашит)
};

const VIEW_TITLES = {
    dashboard: 'Dashboard',
    board:     'Канбан-доска заявок',
    requests:  'Журнал заявок',
    equipment: 'Оборудование',
    parts:     'Склад запчастей',
};

/* ---------- API ---------- */

async function apiGet(path) {
    const res = await fetch(path);
    if (!res.ok) throw await asErr(res);
    return res.json();
}
async function apiSend(method, path, body) {
    const res = await fetch(path, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw asErrFromData(res.status, data);
    return data;
}
function apiPost(p, b)   { return apiSend('POST', p, b); }
function apiPut(p, b)    { return apiSend('PUT',  p, b); }
function apiDelete(p)    { return apiSend('DELETE', p); }

async function asErr(res) {
    const data = await res.json().catch(() => ({}));
    return asErrFromData(res.status, data);
}
function asErrFromData(status, data) {
    const detail = data.detail || `Ошибка ${status}`;
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    err.status = status;
    return err;
}

/* ---------- Init ---------- */

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('today-label').textContent =
        new Date().toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' });

    document.querySelectorAll('.nav-item').forEach(b =>
        b.addEventListener('click', () => switchView(b.dataset.view))
    );
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', e => {
        if (e.target.id === 'modal-overlay') closeModal();
    });

    document.getElementById('filter-priority').addEventListener('change', e => { STATE.filterPriority = e.target.value; renderRequests(); });
    document.getElementById('filter-status').addEventListener('change', e => { STATE.filterStatus = e.target.value; renderRequests(); });
    document.getElementById('filter-assignee').addEventListener('change', e => { STATE.filterAssignee = e.target.value; renderRequests(); });
    document.getElementById('filter-open-only').addEventListener('change', e => { STATE.filterOpenOnly = e.target.checked; renderRequests(); });

    await preload();
    fillFilters();
    switchView('dashboard');
});

async function preload() {
    try {
        const [priorities, statuses, staff, equipment, parts] = await Promise.all([
            apiGet('/api/priorities'),
            apiGet('/api/statuses'),
            apiGet('/api/staff'),
            apiGet('/api/equipment'),
            apiGet('/api/parts'),
        ]);
        Object.assign(STATE, { priorities, statuses, staff, equipment, parts });
    } catch (e) { toast('Не удалось загрузить справочники: ' + e.message, 'error'); }
}

function fillFilters() {
    const p = document.getElementById('filter-priority');
    const s = document.getElementById('filter-status');
    const a = document.getElementById('filter-assignee');
    p.innerHTML = '<option value="">Все</option>' + STATE.priorities.map(x => `<option value="${x.code}">${x.name}</option>`).join('');
    s.innerHTML = '<option value="">Все</option>' + STATE.statuses.map(x => `<option value="${x.code}">${x.name}</option>`).join('');
    a.innerHTML = '<option value="">Все</option>' + STATE.staff.filter(x => x.role_code !== 'dispatcher' && x.role_code !== 'admin')
        .map(x => `<option value="${x.id}">${x.full_name}</option>`).join('');
}

/* ---------- View switching ---------- */

async function switchView(view) {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.toggle('is-active', b.dataset.view === view));
    document.querySelectorAll('.view').forEach(v => v.hidden = (v.id !== 'view-' + view));
    document.getElementById('view-title').textContent = VIEW_TITLES[view];

    const actions = document.getElementById('content-actions');
    actions.innerHTML = '';
    if (view === 'requests' || view === 'board' || view === 'dashboard') {
        actions.innerHTML = '<button class="btn btn--primary btn--small" id="btn-new-req">+ Новая заявка</button>';
        document.getElementById('btn-new-req').addEventListener('click', openNewRequestModal);
    }
    if (view === 'parts') {
        actions.innerHTML = '<button class="btn btn--primary btn--small" id="btn-new-part">+ Новая деталь</button>';
        document.getElementById('btn-new-part').addEventListener('click', openNewPartModal);
    }

    const loaders = {
        dashboard: renderDashboard,
        board:     renderBoard,
        requests:  renderRequests,
        equipment: renderEquipment,
        parts:     renderParts,
    };
    if (loaders[view]) await loaders[view]();
}

/* ---------- Dashboard ---------- */

async function renderDashboard() {
    try {
        const all = await apiGet('/api/requests');
        STATE.requests = all;
        const open = all.filter(r => !r.is_closed);
        const critical = open.filter(r => r.priority_code === 'critical');
        const inWork = open.filter(r => r.status_code === 'in_work');
        const doneToday = all.filter(r => r.is_closed && r.closed_at && r.closed_at.startsWith(STATE.today));

        document.getElementById('kpi-open').textContent = open.length;
        document.getElementById('kpi-critical').textContent = critical.length;
        document.getElementById('kpi-work').textContent = inWork.length;
        document.getElementById('kpi-done').textContent = doneToday.length;

        // Критические заявки — карточки
        const critGrid = document.getElementById('critical-grid');
        if (critical.length === 0) {
            critGrid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:#94A3B8">Критических заявок нет ✓</div>';
        } else {
            critGrid.innerHTML = critical.map(r => `
                <div class="crit-card" data-id="${r.id}">
                    <div class="crit-card__icon">⚠️</div>
                    <div>
                        <div class="crit-card__title">${r.title}</div>
                        <div class="crit-card__sub">${r.equipment_inv_number} · ${r.equipment_name}</div>
                    </div>
                </div>
            `).join('');
            critGrid.querySelectorAll('[data-id]').forEach(c => c.addEventListener('click', () => openRequestDetail(+c.dataset.id)));
        }

        // Запчасти ниже минимума
        const lowParts = STATE.parts.filter(p => p.is_low_stock);
        const partsLow = document.getElementById('parts-low');
        if (lowParts.length === 0) {
            partsLow.innerHTML = '<div style="text-align:center;padding:14px;color:#94A3B8">Все запчасти в норме ✓</div>';
        } else {
            partsLow.innerHTML = lowParts.map(p => `
                <div class="part-low">
                    <span class="part-low__name">${p.name}</span>
                    <span class="part-low__qty">${p.quantity} / мин ${p.min_quantity} ${p.unit}</span>
                </div>
            `).join('');
        }
    } catch (e) { toast(e.message, 'error'); }
}

/* ---------- Kanban Board ---------- */

async function renderBoard() {
    const reqs = await apiGet('/api/requests?open_only=true');
    STATE.requests = reqs;
    const board = document.getElementById('board');
    const cols = STATE.statuses.filter(s => !s.is_closed);
    board.innerHTML = cols.map(s => {
        const items = reqs.filter(r => r.status_code === s.code);
        return `
            <div class="board-col" data-status="${s.code}">
                <header class="board-col__head">
                    <span><span class="dot" style="background:${s.color}"></span> ${s.name}</span>
                    <span class="board-col__count">${items.length}</span>
                </header>
                <div class="board-col__body">
                    ${items.map(r => `
                        <article class="board-card board-card--${r.priority_code}" data-id="${r.id}">
                            <div class="board-card__title">${r.title}</div>
                            <div class="board-card__meta">
                                <span>${r.equipment_inv_number}</span>
                                <span>${r.assignee_name ? r.assignee_name.split(' ').slice(0,2).join(' ') : '— не назначен —'}</span>
                            </div>
                        </article>
                    `).join('') || '<div style="text-align:center;color:#94A3B8;padding:14px;font-size:12px">Пусто</div>'}
                </div>
            </div>`;
    }).join('');
    board.querySelectorAll('.board-card').forEach(c =>
        c.addEventListener('click', () => openRequestDetail(+c.dataset.id))
    );
}

/* ---------- Requests Table ---------- */

async function renderRequests() {
    let url = '/api/requests?';
    if (STATE.filterPriority)  url += `&priority=${STATE.filterPriority}`;
    if (STATE.filterStatus)    url += `&status=${STATE.filterStatus}`;
    if (STATE.filterAssignee)  url += `&assigned_to=${STATE.filterAssignee}`;
    if (STATE.filterOpenOnly)  url += `&open_only=true`;
    const reqs = await apiGet(url);

    const tbody = document.getElementById('requests-tbody');
    if (reqs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#94A3B8">Заявок не найдено</td></tr>';
        return;
    }
    tbody.innerHTML = reqs.map(r => {
        const rowClass = r.is_closed ? 'row--closed' : `row--${r.priority_code}`;
        return `
            <tr class="${rowClass}">
                <td class="cell-id">#${r.id}</td>
                <td class="cell-title">
                    ${r.title}
                    <small>${r.location_name}</small>
                </td>
                <td>${r.equipment_inv_number}<br><small style="color:#64748B">${r.equipment_name}</small></td>
                <td><span class="badge" style="background:${r.priority_color}22;color:${r.priority_color}">${r.priority_name}</span></td>
                <td><span class="badge" style="background:${r.status_color}22;color:${r.status_color}">${r.status_name}</span></td>
                <td>${assigneeCell(r)}</td>
                <td>${new Date(r.created_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</td>
                <td style="text-align:right">
                    <button class="btn btn--ghost btn--small" data-act="open" data-id="${r.id}">Открыть</button>
                </td>
            </tr>`;
    }).join('');

    // Назначение «в один клик» прямо из таблицы
    tbody.querySelectorAll('select[data-act="assign"]').forEach(sel => sel.addEventListener('change', async e => {
        const id = +sel.dataset.id;
        const newAssignee = +sel.value;
        if (!newAssignee) return;
        try {
            await apiPost(`/api/requests/${id}/assign`, { assigned_to: newAssignee });
            toast('Заявка назначена', 'success');
            renderRequests();
            renderDashboard();
        } catch (err) { toast(err.message, 'error'); }
    }));
    tbody.querySelectorAll('[data-act="open"]').forEach(b => b.addEventListener('click', () => openRequestDetail(+b.dataset.id)));
}

function assigneeCell(r) {
    const techs = STATE.staff.filter(s => s.role_code !== 'dispatcher' && s.role_code !== 'admin');
    if (r.is_closed) return r.assignee_name || '—';
    const opts = ['<option value="">— назначить —</option>',
        ...techs.map(t => `<option value="${t.id}" ${t.id === r.assigned_to ? 'selected' : ''}>${t.full_name}</option>`)
    ].join('');
    return `<select data-act="assign" data-id="${r.id}" style="padding:5px 8px;border-radius:6px;border:1px solid #CBD5E1;font-size:13px;background:#fff">${opts}</select>`;
}

/* ---------- Equipment ---------- */

async function renderEquipment() {
    const eq = await apiGet('/api/equipment');
    STATE.equipment = eq;
    const grid = document.getElementById('equipment-grid');
    grid.innerHTML = eq.map(e => `
        <article class="eq-card ${e.critical_open_count > 0 ? 'eq-card--alert' : ''}">
            <div class="eq-card__inv">${e.inventory_number}</div>
            <div class="eq-card__name">${e.equipment_type_icon} ${e.name}</div>
            <div class="eq-card__location">${e.location_name} · ${e.location_building}</div>
            <div class="eq-card__status">
                ${e.critical_open_count > 0
                    ? `<span class="badge" style="background:#FEE2E2;color:#B91C1C">⚠️ ${e.critical_open_count} критических</span>`
                    : `<span class="badge" style="background:#D1FAE5;color:#065F46">✓ исправно</span>`}
                <span style="color:#94A3B8;font-size:12px;margin-left:auto">${e.open_requests_count} откр. заявок</span>
            </div>
        </article>
    `).join('');
}

/* ---------- Parts ---------- */

async function renderParts() {
    const parts = await apiGet('/api/parts');
    STATE.parts = parts;
    document.getElementById('parts-tbody').innerHTML = parts.map(p => `
        <tr ${p.is_low_stock ? 'style="background:#FEF3C7"' : ''}>
            <td class="cell-id">${p.sku}</td>
            <td><strong>${p.name}</strong></td>
            <td>${p.unit}</td>
            <td>${p.unit_price.toLocaleString('ru-RU')} с</td>
            <td><strong style="color:${p.is_low_stock ? '#B91C1C' : '#065F46'}">${p.quantity}</strong> ${p.unit}</td>
            <td>${p.min_quantity}</td>
            <td style="text-align:right">
                <button class="btn btn--ghost btn--small" data-act="adjust" data-id="${p.id}" data-name="${p.name}">Пополнить</button>
            </td>
        </tr>
    `).join('');
    document.querySelectorAll('[data-act="adjust"]').forEach(b => b.addEventListener('click', () =>
        openAdjustModal(+b.dataset.id, b.dataset.name)
    ));
}

/* ---------- Request detail modal ---------- */

async function openRequestDetail(requestId) {
    const r = await apiGet(`/api/requests/${requestId}`);
    const history = await apiGet(`/api/requests/${requestId}/history`).catch(() => []);

    const techs = STATE.staff.filter(s => s.role_code !== 'dispatcher' && s.role_code !== 'admin');
    const assignOpts = ['<option value="">— назначить —</option>',
        ...techs.map(t => `<option value="${t.id}" ${t.id === r.assigned_to ? 'selected' : ''}>${t.full_name}</option>`)
    ].join('');

    const partsHtml = r.parts.length === 0 ? '<em>Запчасти не списаны</em>' : `
        <table class="parts-table">
            <thead><tr><th>Артикул</th><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Итого</th></tr></thead>
            <tbody>
                ${r.parts.map(p => `<tr>
                    <td>${p.sku}</td><td>${p.name}</td>
                    <td>${p.quantity_used} ${p.unit}</td>
                    <td>${p.unit_price_at_use.toFixed(2)}</td>
                    <td><strong>${p.line_total.toFixed(2)}</strong></td>
                </tr>`).join('')}
                <tr><td colspan="4" style="text-align:right"><strong>Всего использовано на:</strong></td>
                    <td><strong>${r.parts_total.toFixed(2)} сом</strong></td></tr>
            </tbody>
        </table>`;

    const historyHtml = history.length === 0 ? '<em>История пуста</em>' : history.map(h => `
        <div class="history-line">
            <span class="history-line__time">${new Date(h.changed_at).toLocaleString('ru-RU', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}</span>
            <span style="color:#64748B">${h.old_status_name || '—'} →</span>
            <span class="badge" style="background:${h.new_status_color}22;color:${h.new_status_color}">${h.new_status_name}</span>
            <span style="color:#94A3B8;margin-left:auto;font-size:12px">${h.changed_by_name}</span>
        </div>
    `).join('');

    const closeAvailable = !r.is_closed;
    const partsOpts = STATE.parts.map(p =>
        `<option value="${p.id}" data-stock="${p.quantity}" data-unit="${p.unit}">${p.name} (${p.sku}) — на складе ${p.quantity} ${p.unit}</option>`
    ).join('');

    openModal(`Заявка #${r.id} — ${r.title}`, `
        <div class="detail-block">
            <h4>Параметры</h4>
            <div class="detail-grid">
                <div>Оборудование<strong>${r.equipment_inv_number} · ${r.equipment_name}</strong></div>
                <div>Локация<strong>${r.location_name}</strong></div>
                <div>Приоритет<strong style="color:${r.priority_color}">${r.priority_name} (SLA ${r.priority_sla_hours} ч)</strong></div>
                <div>Статус<strong style="color:${r.status_color}">${r.status_name}</strong></div>
                <div>Плановая дата<strong>${r.planned_date || '—'}</strong></div>
                <div>Создал<strong>${r.creator_name}</strong></div>
            </div>
        </div>

        ${r.description ? `<div class="detail-block">
            <h4>Описание</h4>
            <p style="margin:0;color:#334155">${r.description}</p>
        </div>` : ''}

        ${closeAvailable ? `
            <div class="detail-block">
                <h4>Исполнитель</h4>
                <select id="modal-assign" style="padding:8px 10px;border:1px solid #CBD5E1;border-radius:8px;font-size:14px;width:100%;background:#fff">
                    ${assignOpts}
                </select>
            </div>
        ` : ''}

        <div class="detail-block">
            <h4>Запчасти, использованные при ремонте</h4>
            ${partsHtml}
        </div>

        <div class="detail-block">
            <h4>История статусов</h4>
            ${historyHtml}
        </div>

        ${closeAvailable ? `
            <div class="detail-block">
                <h4>Закрыть заявку</h4>
                <form id="complete-form" class="form">
                    <div id="parts-rows" style="display:flex;flex-direction:column;gap:8px"></div>
                    <button type="button" class="btn btn--ghost btn--small" id="add-part-row" style="align-self:flex-start">+ Добавить запчасть</button>
                    <label class="field">
                        <span>Комментарий мастера</span>
                        <textarea name="completion_note" rows="2" placeholder="Что было сделано"></textarea>
                    </label>
                    <button type="submit" class="btn btn--primary btn--block">Закрыть заявку (статус «Выполнена»)</button>
                </form>
            </div>
            <button class="btn btn--ghost btn--block" id="delete-btn" style="margin-top:6px">${r.status_code === 'received' ? 'Удалить заявку' : 'Удаление недоступно (заявка в работе)'}</button>
        ` : ''}
    `);

    // assign change
    const assignSel = document.getElementById('modal-assign');
    if (assignSel) assignSel.addEventListener('change', async () => {
        if (!assignSel.value) return;
        try {
            await apiPost(`/api/requests/${requestId}/assign`, { assigned_to: +assignSel.value });
            toast('Исполнитель назначен', 'success');
            closeModal();
            renderRequests(); renderBoard(); renderDashboard();
        } catch (e) { toast(e.message, 'error'); }
    });

    // parts rows
    const partsRows = document.getElementById('parts-rows');
    const partsAddBtn = document.getElementById('add-part-row');
    if (partsAddBtn) {
        const addRow = () => {
            const row = document.createElement('div');
            row.style.cssText = 'display:flex;gap:8px;align-items:center';
            row.innerHTML = `
                <select class="part-sel" style="flex:1;padding:8px 10px;border:1px solid #CBD5E1;border-radius:8px;font-size:13.5px;background:#fff">${partsOpts}</select>
                <input type="number" class="part-qty" min="1" value="1" style="width:80px;padding:8px 10px;border:1px solid #CBD5E1;border-radius:8px;font-size:13.5px">
                <button type="button" class="btn btn--ghost btn--small" data-remove>×</button>`;
            row.querySelector('[data-remove]').addEventListener('click', () => row.remove());
            partsRows.appendChild(row);
        };
        partsAddBtn.addEventListener('click', addRow);
    }

    const completeForm = document.getElementById('complete-form');
    if (completeForm) completeForm.addEventListener('submit', async e => {
        e.preventDefault();
        const parts_used = Array.from(partsRows.querySelectorAll('div')).map(row => {
            const sel = row.querySelector('.part-sel');
            const qty = row.querySelector('.part-qty');
            if (!sel || !qty) return null;
            return { part_id: +sel.value, quantity: +qty.value };
        }).filter(Boolean);
        const completion_note = completeForm.querySelector('[name="completion_note"]').value.trim() || null;

        try {
            await apiPost(`/api/requests/${requestId}/complete`, { parts_used, completion_note });
            toast('Заявка закрыта, запчасти списаны', 'success');
            closeModal();
            await preload();
            renderRequests(); renderBoard(); renderDashboard();
        } catch (err) { toast(err.message, 'error'); }
    });

    const delBtn = document.getElementById('delete-btn');
    if (delBtn && r.status_code === 'received') {
        delBtn.addEventListener('click', async () => {
            if (!confirm('Удалить заявку без следов?')) return;
            try {
                await apiDelete(`/api/requests/${requestId}`);
                toast('Заявка удалена', 'warn');
                closeModal();
                renderRequests(); renderBoard(); renderDashboard();
            } catch (e) { toast(e.message, 'error'); }
        });
    }
}

/* ---------- Modals ---------- */

function openNewRequestModal() {
    const eqOpts = STATE.equipment.map(e => `<option value="${e.id}">${e.inventory_number} — ${e.name}</option>`).join('');
    const prioOpts = STATE.priorities.map(p => `<option value="${p.id}">${p.name} (SLA ${p.sla_hours} ч)</option>`).join('');
    const techOpts = ['<option value="">— не назначать —</option>',
        ...STATE.staff.filter(s => s.role_code !== 'dispatcher' && s.role_code !== 'admin')
            .map(t => `<option value="${t.id}">${t.full_name}</option>`)
    ].join('');

    openModal('Регистрация новой заявки на ТО', `
        <form id="new-req-form" class="form">
            <label class="field"><span>Краткое описание (заголовок) *</span><input name="title" required minlength="5" placeholder="Например: Скрип подшипника привода"></label>
            <label class="field"><span>Оборудование *</span><select name="equipment_id" required>${eqOpts}</select></label>
            <label class="field"><span>Приоритет *</span><select name="priority_id" required>${prioOpts}</select></label>
            <label class="field"><span>Плановая дата</span><input name="planned_date" type="date" value="${STATE.today}"></label>
            <label class="field"><span>Назначить исполнителя</span><select name="assigned_to">${techOpts}</select></label>
            <label class="field"><span>Подробное описание</span><textarea name="description" rows="3" placeholder="Симптомы, обстоятельства возникновения"></textarea></label>
            <button type="submit" class="btn btn--primary btn--block">Зарегистрировать заявку</button>
        </form>
    `);
    document.getElementById('new-req-form').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = Object.fromEntries(new FormData(e.target));
        const body = {
            equipment_id: +fd.equipment_id,
            priority_id:  +fd.priority_id,
            title:        fd.title,
            description:  fd.description || null,
            planned_date: fd.planned_date || null,
            assigned_to:  fd.assigned_to ? +fd.assigned_to : null,
            created_by:   STATE.currentUserId,
        };
        try {
            await apiPost('/api/requests', body);
            toast('Заявка зарегистрирована', 'success');
            closeModal();
            renderRequests(); renderBoard(); renderDashboard();
        } catch (err) { toast(err.message, 'error'); }
    });
}

function openNewPartModal() {
    openModal('Новая запчасть', `
        <form id="new-part-form" class="form">
            <label class="field"><span>Артикул (SKU) *</span><input name="sku" required></label>
            <label class="field"><span>Наименование *</span><input name="name" required></label>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <label class="field"><span>Ед. изм.</span><input name="unit" value="шт"></label>
                <label class="field"><span>Цена (сом)</span><input type="number" name="unit_price" min="0" step="1" value="100"></label>
                <label class="field"><span>Остаток</span><input type="number" name="quantity" min="0" value="0"></label>
                <label class="field"><span>Мин. остаток</span><input type="number" name="min_quantity" min="0" value="0"></label>
            </div>
            <button type="submit" class="btn btn--primary btn--block">Добавить деталь</button>
        </form>
    `);
    document.getElementById('new-part-form').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = Object.fromEntries(new FormData(e.target));
        try {
            await apiPost('/api/parts', {
                sku: fd.sku, name: fd.name, unit: fd.unit || 'шт',
                unit_price: +fd.unit_price, quantity: +fd.quantity, min_quantity: +fd.min_quantity,
            });
            toast('Деталь добавлена', 'success');
            closeModal();
            renderParts();
        } catch (err) { toast(err.message, 'error'); }
    });
}

function openAdjustModal(partId, name) {
    openModal(`Корректировка остатка: ${name}`, `
        <form id="adjust-form" class="form">
            <label class="field"><span>Сумма изменения (+ приход / − расход) *</span>
                <input type="number" name="delta" required value="10">
            </label>
            <label class="field"><span>Комментарий</span><input name="note" placeholder="Например: поставка №42"></label>
            <button type="submit" class="btn btn--primary btn--block">Применить</button>
        </form>
    `);
    document.getElementById('adjust-form').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
            await apiPost(`/api/parts/${partId}/adjust`, { delta: +fd.get('delta'), note: fd.get('note') || null });
            toast('Остаток обновлён', 'success');
            closeModal();
            await preload();
            renderParts();
            renderDashboard();
        } catch (err) { toast(err.message, 'error'); }
    });
}

/* ---------- Modal/toast utils ---------- */

function openModal(title, html) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = html;
    document.getElementById('modal-overlay').hidden = false;
}
function closeModal() { document.getElementById('modal-overlay').hidden = true; }

function toast(message, kind = 'success') {
    const el = document.createElement('div');
    el.className = 'toast' + (kind !== 'success' ? ' toast--' + kind : '');
    el.textContent = message;
    document.getElementById('toast-stack').appendChild(el);
    setTimeout(() => el.remove(), 4500);
}
