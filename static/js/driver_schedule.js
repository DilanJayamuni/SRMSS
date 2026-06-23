let currentYear, currentMonth, currentDriverId;
let scheduleData = null;

(async function init() {
    const sel = document.getElementById('driver-select');
    if (!sel) return;

    const drivers = await apiGet('/api/drivers') || [];
    const userRole = document.getElementById('user-role-display').innerText;

    sel.innerHTML = '<option value="">-- Select Driver --</option>' +
        drivers.map(d => `<option value="${d.id}">${d.name}</option>`).join('');

    const now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth() + 1;

    document.getElementById('month-label').innerText = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    sel.addEventListener('change', onDriverChange);

    if (userRole === 'Operational Staff') {
        const myTrips = await apiGet('/api/dashboard/staff');
        if (myTrips && myTrips.my_trips && myTrips.my_trips.length > 0) {
            const staffDriverId = myTrips.my_trips[0].driver_id;
            if (staffDriverId) {
                sel.value = staffDriverId;
                loadSchedule(staffDriverId, currentYear, currentMonth);
                return;
            }
        }
    }

    initProposalForm();
})();

function onDriverChange() {
    currentDriverId = parseInt(document.getElementById('driver-select').value);
    if (currentDriverId) {
        loadSchedule(currentDriverId, currentYear, currentMonth);
    } else {
        document.getElementById('calendar-panel').style.display = 'none';
        document.getElementById('no-driver-panel').style.display = 'block';
    }
}

function prevMonth() {
    currentMonth--;
    if (currentMonth < 1) { currentMonth = 12; currentYear--; }
    updateMonthLabel();
    if (currentDriverId) loadSchedule(currentDriverId, currentYear, currentMonth);
}

function nextMonth() {
    currentMonth++;
    if (currentMonth > 12) { currentMonth = 1; currentYear++; }
    updateMonthLabel();
    if (currentDriverId) loadSchedule(currentDriverId, currentYear, currentMonth);
}

function todayMonth() {
    const now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth() + 1;
    updateMonthLabel();
    if (currentDriverId) loadSchedule(currentDriverId, currentYear, currentMonth);
}

function updateMonthLabel() {
    const d = new Date(currentYear, currentMonth - 1, 1);
    document.getElementById('month-label').innerText = d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

async function loadSchedule(driverId, year, month) {
    const data = await apiGet(`/api/driver-schedule?driver_id=${driverId}&month=${month}&year=${year}`);
    if (!data) return;

    scheduleData = data;
    renderCalendar(data);
    document.getElementById('calendar-panel').style.display = 'block';
    document.getElementById('no-driver-panel').style.display = 'none';
}

function renderCalendar(data) {
    const grid = document.getElementById('calendar-grid');
    const detail = document.getElementById('day-detail');
    detail.style.display = 'none';

    const daysInMonth = data.days_in_month;
    const firstDay = new Date(data.year, data.month - 1, 1).getDay();

    grid.innerHTML = '';

    for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day empty';
        grid.appendChild(empty);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${data.year.toString().padStart(4, '0')}-${data.month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        const dayDiv = document.createElement('div');
        dayDiv.className = 'calendar-day';
        dayDiv.dataset.date = dateStr;

        const numSpan = document.createElement('span');
        numSpan.className = 'day-number';
        numSpan.innerText = day;
        dayDiv.appendChild(numSpan);

        const trips = data.schedules[dateStr];
        if (trips && trips.length > 0) {
            dayDiv.classList.add('has-trips');
            const dot = document.createElement('span');
            dot.className = 'trip-dot';
            dot.innerText = trips.length;
            dayDiv.appendChild(dot);

            const first = trips[0];
            const label = document.createElement('span');
            label.className = 'trip-label';
            label.innerText = first.departure_time.substring(11, 16) + ' ' + first.route_name;
            dayDiv.appendChild(label);
        }

        dayDiv.addEventListener('click', () => showDayDetail(dateStr));
        grid.appendChild(dayDiv);
    }
}

function showDayDetail(dateStr) {
    const detail = document.getElementById('day-detail');
    const dateTitle = document.getElementById('detail-date');
    const tripsDiv = document.getElementById('detail-trips');

    dateTitle.innerText = new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const trips = scheduleData && scheduleData.schedules[dateStr];
    if (!trips || trips.length === 0) {
        tripsDiv.innerHTML = '<p style="opacity:0.7;">No trips scheduled for this day.</p>';
    } else {
        tripsDiv.innerHTML = trips.map(t => {
            const badgeClass = t.status === 'Scheduled' ? 'badge-blue' : t.status === 'Completed' ? 'badge-green' : 'badge-red';
            return `<div class="trip-list-item">
                <div>
                    <div class="route">${t.route_name}</div>
                    <div class="info">${t.vehicle_reg} &bull; ${t.departure_time.substring(11, 16)} - ${t.arrival_time ? t.arrival_time.substring(11, 16) : '--'}</div>
                </div>
                <span class="badge ${badgeClass}">${t.status}</span>
            </div>`;
        }).join('');
    }
    detail.style.display = 'block';
}

async function initProposalForm() {
    const [drivers, vehicles, routes] = await Promise.all([
        apiGet('/api/drivers'),
        apiGet('/api/vehicles'),
        apiGet('/api/routes')
    ]);

    const dSel = document.getElementById('prop-driver');
    if (dSel && drivers) {
        dSel.innerHTML = '<option value="">Driver</option>' +
            drivers.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    }

    const vSel = document.getElementById('prop-vehicle');
    if (vSel && vehicles) {
        vSel.innerHTML = '<option value="">Vehicle</option>' +
            vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('');
    }

    const rSel = document.getElementById('prop-route');
    if (rSel && routes) {
        rSel.innerHTML = '<option value="">Route</option>' +
            routes.map(r => `<option value="${r.id}">${r.route_name}</option>`).join('');
    }

    const panel = document.getElementById('proposal-panel');
    if (panel) panel.style.display = 'block';
}

async function submitProposal() {
    const driverId = document.getElementById('prop-driver').value;
    const vehicleId = document.getElementById('prop-vehicle').value;
    const routeId = document.getElementById('prop-route').value;
    const date = document.getElementById('prop-date').value;
    const departure = document.getElementById('prop-departure').value;
    const arrival = document.getElementById('prop-arrival').value;
    const recurrence = document.getElementById('prop-recurrence').value;
    const notes = document.getElementById('prop-notes').value;

    if (!driverId || !vehicleId || !routeId || !departure) {
        showToast('Please fill in driver, vehicle, route, and departure time.', 'error');
        return;
    }

    const payload = {
        driver_id: parseInt(driverId),
        vehicle_id: parseInt(vehicleId),
        route_id: parseInt(routeId),
        proposed_date: date,
        departure_time: date ? `${date}T${departure}` : departure,
        arrival_time: date && arrival ? `${date}T${arrival}` : arrival,
        recurrence: recurrence,
        notes: notes
    };

    const resp = await apiPost('/api/schedule-proposals', payload);
    if (!resp.ok) {
        const err = await resp.json();
        showToast(err.error || 'Failed to create proposal.', 'error');
        return;
    }

    showToast('Proposal submitted successfully!', 'success');
    document.getElementById('prop-driver').value = '';
    document.getElementById('prop-vehicle').value = '';
    document.getElementById('prop-route').value = '';
    document.getElementById('prop-date').value = '';
    document.getElementById('prop-departure').value = '';
    document.getElementById('prop-arrival').value = '';
    document.getElementById('prop-notes').value = '';
}
