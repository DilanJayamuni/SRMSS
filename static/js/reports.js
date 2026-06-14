let currentTab = 'summary';
let chartInstances = {};
let filterState = {};

(async function initReports() {
  if (window.USER_ROLE !== 'Administrator') {
    document.querySelectorAll('.tab-admin').forEach(t => t.classList.add('hidden-tab'));
  }
  setupTabs();
  setupFilters();
  setupExport();
  await switchTab('summary');
})();

function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', async () => {
      const name = tab.dataset.tab;
      if (name === currentTab) return;
      await switchTab(name);
    });
  });
}

async function switchTab(name) {
  Object.values(chartInstances).forEach(c => { if (c) { c.destroy(); } });
  chartInstances = {};
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
  document.querySelector(`.tab[data-tab="${name}"]`).classList.add('active');
  document.getElementById(`tab-${name}`).classList.add('active');
  currentTab = name;
  buildFilterBar(name);
  await loadTab(name);
}

function setupFilters() {
  document.getElementById('filterApply').addEventListener('click', async () => {
    filterState = getFilterParams();
    await loadTab(currentTab);
  });
  document.getElementById('filterReset').addEventListener('click', async () => {
    filterState = {};
    document.querySelectorAll('.filter-input').forEach(el => el.value = '');
    await loadTab(currentTab);
  });
}

function buildFilterBar(tab) {
  const c = document.getElementById('filterControls');
  let html = '<div class="filter-group"><label>From</label><input type="date" id="f-date_from" class="filter-input"></div>';
  html += '<div class="filter-group"><label>To</label><input type="date" id="f-date_to" class="filter-input"></div>';
  const vehicleTabs = ['fuel', 'maintenance', 'trips'];
  if (vehicleTabs.includes(tab)) {
    html += '<div class="filter-group"><label>Vehicle</label><select id="f-vehicle_id" class="filter-input"><option value="">All Vehicles</option></select></div>';
  }
  if (tab === 'trips') {
    html += '<div class="filter-group"><label>Driver</label><select id="f-driver_id" class="filter-input"><option value="">All Drivers</option></select></div>';
    html += '<div class="filter-group"><label>Route</label><select id="f-route_id" class="filter-input"><option value="">All Routes</option></select></div>';
  }
  if (tab === 'fleet') {
    html += '<div class="filter-group"><label>Type</label><select id="f-vehicle_type" class="filter-input"><option value="">All Types</option></select></div>';
  }
  if (tab === 'drivers') {
    html += '<div class="filter-group"><label>Driver</label><select id="f-driver_id" class="filter-input"><option value="">All Drivers</option></select></div>';
  }
  if (tab === 'maintenance') {
    html += '<div class="filter-group"><label>Status</label><select id="f-status" class="filter-input"><option value="">All Status</option><option value="Pending">Pending</option><option value="Approved">Approved</option><option value="Rejected">Rejected</option></select></div>';
  }
  c.innerHTML = html;
  populateDropdowns(tab);
}

async function populateDropdowns(tab) {
  const vehEl = document.getElementById('f-vehicle_id');
  const drvEl = document.getElementById('f-driver_id');
  const rteEl = document.getElementById('f-route_id');
  const typeEl = document.getElementById('f-vehicle_type');
  const [vehicles, drivers, routes] = await Promise.all([
    vehEl || typeEl ? apiGet('/api/vehicles') : null,
    drvEl ? apiGet('/api/drivers') : null,
    rteEl ? apiGet('/api/routes') : null
  ]);
  if (vehEl && vehicles) vehicles.forEach(v => { vehEl.innerHTML += `<option value="${v.id}">${v.registration_no}</option>`; });
  if (drvEl && drivers) drivers.forEach(d => { drvEl.innerHTML += `<option value="${d.id}">${d.name}</option>`; });
  if (rteEl && routes) routes.forEach(r => { rteEl.innerHTML += `<option value="${r.id}">${r.route_name}</option>`; });
  if (typeEl && vehicles) {
    const types = [...new Set(vehicles.map(v => v.type).filter(Boolean))];
    types.forEach(t => { typeEl.innerHTML += `<option value="${t}">${t}</option>`; });
  }
}

function getFilterParams() {
  const p = {};
  document.querySelectorAll('.filter-input').forEach(el => {
    if (el.value) p[el.id.replace('f-', '')] = el.value;
  });
  return p;
}

function qs(params) {
  const s = new URLSearchParams(params).toString();
  return s ? '?' + s : '';
}

function setupExport() {
  const btn = document.getElementById('exportCsvBtn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const reportMap = { summary: 'summary', trips: 'trips', fleet: 'fleet', drivers: 'drivers', fuel: 'fuel', maintenance: 'maintenance' };
    const name = reportMap[currentTab];
    if (!name) return;
    const params = { ...filterState };
    const q = new URLSearchParams(params).toString();
    window.location.href = '/api/reports/export/' + name + (q ? '?' + q : '');
  });
}

async function loadTab(name) {
  const el = document.getElementById(`report-${name}`);
  if (!el) return;
  el.innerHTML = '<div style="text-align:center;padding:40px;opacity:0.5;">Loading...</div>';
  try {
    const fns = { summary: loadSummary, trips: loadTrips, fleet: loadFleet, drivers: loadDrivers, fuel: loadFuel, maintenance: loadMaintenance };
    await fns[name](el);
  } catch (e) {
    el.innerHTML = '<div class="panel"><p style="color:var(--danger);">Error loading report.</p></div>';
  }
}

async function loadSummary(el) {
  const data = await apiGet('/api/reports/summary' + qs(filterState));
  const tripsData = await apiGet('/api/reports/trips' + qs(filterState));
  if (!data) { el.innerHTML = '<div class="panel"><p style="color:var(--danger);">Error loading summary.</p></div>'; return; }
  const tc = data.total_fuel_cost + data.total_maint_cost;
  el.innerHTML = `
    <div class="grid-3">
      <div class="panel"><h3>Total Fuel Cost</h3><div style="font-size:28px;font-weight:700;">Rs. ${data.total_fuel_cost.toLocaleString()}</div></div>
      <div class="panel"><h3>Total Maintenance</h3><div style="font-size:28px;font-weight:700;">Rs. ${data.total_maint_cost.toLocaleString()}</div></div>
      <div class="panel"><h3>Trip Completion</h3><div style="font-size:28px;font-weight:700;">${data.completion_rate}%</div></div>
    </div>
    <div class="grid-2">
      <div class="panel"><h3>Cost Overview</h3><div class="chart-container"><canvas id="chart-summary-cost"></canvas></div></div>
      <div class="panel"><h3>Trip Status Distribution</h3><div class="chart-container"><canvas id="chart-summary-status"></canvas></div></div>
    </div>
    <div class="panel">
      <h3>Performance Summary</h3>
      <table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>
        <tr><td>Total Scheduled Trips</td><td>${data.total_trips}</td></tr>
        <tr><td>Completed Trips</td><td>${data.completed_trips}</td></tr>
        <tr><td>Fuel Consumed (L)</td><td>${data.total_liters}</td></tr>
        <tr><td>Total Cost (Fuel + Maintenance)</td><td>Rs. ${tc.toLocaleString()}</td></tr>
      </tbody></table>
    </div>`;
  chartInstances.summaryCost = new Chart(document.getElementById('chart-summary-cost'), {
    type: 'bar', data: {
      labels: ['Fuel', 'Maintenance'],
      datasets: [{ label: 'Cost (Rs.)', data: [data.total_fuel_cost, data.total_maint_cost], backgroundColor: ['#2563eb', '#7c3aed'] }]
    }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });
  if (tripsData && tripsData.by_status && tripsData.by_status.length) {
    const labels = tripsData.by_status.map(r => r.status);
    const values = tripsData.by_status.map(r => r.count);
    const colors = { 'Scheduled': '#eab308', 'Completed': '#16a34a', 'Cancelled': '#ef4444', 'In Transit': '#2563eb' };
    chartInstances.summaryStatus = new Chart(document.getElementById('chart-summary-status'), {
      type: 'doughnut', data: {
        labels, datasets: [{ data: values, backgroundColor: labels.map(l => colors[l] || '#64748b') }]
      }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
    });
  }
}

async function loadTrips(el) {
  const data = await apiGet('/api/reports/trips' + qs(filterState));
  const routesData = await apiGet('/api/reports/trips/routes' + qs(filterState));
  if (!data) { el.innerHTML = '<div class="panel"><p style="color:var(--danger);">Error loading trips.</p></div>'; return; }
  const total = data.by_status.reduce((s, r) => s + r.count, 0);
  const completed = (data.by_status.find(r => r.status === 'Completed') || {}).count || 0;
  const cancelled = (data.by_status.find(r => r.status === 'Cancelled') || {}).count || 0;
  const scheduled = (data.by_status.find(r => r.status === 'Scheduled') || {}).count || 0;
  const rate = total > 0 ? (completed / total * 100).toFixed(1) : 0;
  el.innerHTML = `
    <div class="grid-3">
      <div class="panel"><h3>Total Trips</h3><div style="font-size:28px;font-weight:700;">${total}</div></div>
      <div class="panel"><h3>Completed</h3><div style="font-size:28px;font-weight:700;color:var(--success);">${completed} (${rate}%)</div></div>
      <div class="panel"><h3>Cancelled</h3><div style="font-size:28px;font-weight:700;color:var(--danger);">${cancelled}</div></div>
    </div>
    <div class="grid-2">
      <div class="panel"><h3>Status Distribution</h3><div class="chart-container"><canvas id="chart-trips-status"></canvas></div></div>
      <div class="panel"><h3>Monthly Trend</h3><div class="chart-container"><canvas id="chart-trips-monthly"></canvas></div></div>
    </div>
    <div class="panel"><h3>Route Performance</h3>
      <table><thead><tr><th>Route</th><th>Total Trips</th><th>Completed</th><th>Rate</th></tr></thead><tbody>
        ${(routesData || []).map(r => `<tr><td>${r.route_name}</td><td>${r.total_trips}</td><td>${r.completed_trips}</td><td>${r.completion_rate}%</td></tr>`).join('')}
      </tbody></table>
    </div>`;
  const colors = { 'Scheduled': '#eab308', 'Completed': '#16a34a', 'Cancelled': '#ef4444', 'In Transit': '#2563eb' };
  chartInstances.tripsStatus = new Chart(document.getElementById('chart-trips-status'), {
    type: 'doughnut', data: {
      labels: data.by_status.map(r => r.status), datasets: [{ data: data.by_status.map(r => r.count), backgroundColor: data.by_status.map(r => colors[r.status] || '#64748b') }]
    }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
  if (data.by_month && data.by_month.length) {
    chartInstances.tripsMonthly = new Chart(document.getElementById('chart-trips-monthly'), {
      type: 'bar', data: {
        labels: data.by_month.map(r => r.month),
        datasets: [
          { label: 'Total', data: data.by_month.map(r => r.total), backgroundColor: '#2563eb' },
          { label: 'Completed', data: data.by_month.map(r => r.completed), backgroundColor: '#16a34a' }
        ]
      }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
    });
  }
}

async function loadFleet(el) {
  const data = await apiGet('/api/reports/fleet' + qs(filterState));
  if (!data || !data.length) { el.innerHTML = '<div class="panel"><p style="color:var(--danger);">No fleet data available.</p></div>'; return; }
  el.innerHTML = `
    <div class="panel"><h3>Vehicle Utilization</h3><div class="chart-container"><canvas id="chart-fleet"></canvas></div></div>
    <div class="panel"><h3>Fleet Details</h3>
      <table><thead><tr><th>Vehicle</th><th>Type</th><th>Trips</th><th>Distance (km)</th><th>Fuel (L)</th></tr></thead><tbody>
        ${data.map(r => `<tr><td>${r.registration_no}</td><td>${r.type || '-'}</td><td>${r.trips_completed}</td><td>${Math.round(r.total_distance_km)}</td><td>${Math.round(r.total_fuel_liters)}</td></tr>`).join('')}
      </tbody></table>
    </div>`;
  const labels = data.map(r => r.registration_no);
  chartInstances.fleet = new Chart(document.getElementById('chart-fleet'), {
    type: 'bar', data: {
      labels,
      datasets: [
        { label: 'Trips Completed', data: data.map(r => r.trips_completed), backgroundColor: '#2563eb' },
        { label: 'Distance (km)', data: data.map(r => Math.round(r.total_distance_km)), backgroundColor: '#16a34a' }
      ]
    }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

async function loadDrivers(el) {
  const [drvData, licData] = await Promise.all([
    apiGet('/api/reports/drivers' + qs(filterState)),
    apiGet('/api/reports/drivers/licenses' + qs(filterState))
  ]);
  let html = '';
  if (drvData && drvData.length) {
    html += `<div class="panel"><h3>Trips per Driver</h3><div class="chart-container"><canvas id="chart-drivers"></canvas></div></div>`;
    html += `<div class="panel"><h3>Driver Activity</h3>
      <table><thead><tr><th>Name</th><th>License</th><th>Trips Completed</th></tr></thead><tbody>
        ${drvData.map(r => `<tr><td>${r.name}</td><td>${r.license_no}</td><td>${r.trips_completed}</td></tr>`).join('')}
      </tbody></table></div>`;
    chartInstances.drivers = new Chart(document.getElementById('chart-drivers'), {
      type: 'bar', data: {
        labels: drvData.map(r => r.name),
        datasets: [{ label: 'Trips Completed', data: drvData.map(r => r.trips_completed), backgroundColor: '#7c3aed' }]
      }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
  }
  if (licData && licData.length) {
    html += `<div class="panel"><h3>License Expiry</h3>
      <table><thead><tr><th>Name</th><th>License No.</th><th>Expiry Date</th><th>Days Until Expiry</th></tr></thead><tbody>
        ${licData.map(r => {
          const expired = r.days_until_expiry < 0;
          return `<tr class="${expired ? 'expired-row' : ''}"><td>${r.name}</td><td>${r.license_no}</td><td>${r.license_expiry}</td><td>${expired ? 'Expired' : r.days_until_expiry + ' days'}</td></tr>`;
        }).join('')}
      </tbody></table></div>`;
  }
  if (!html) html = '<div class="panel"><p>No driver data available.</p></div>';
  el.innerHTML = html;
}

async function loadFuel(el) {
  const [costData, effData] = await Promise.all([
    apiGet('/api/reports/fuel' + qs(filterState)),
    apiGet('/api/reports/fuel/efficiency' + qs(filterState))
  ]);
  if (!costData || !costData.length) { el.innerHTML = '<div class="panel"><p>No fuel data available.</p></div>'; return; }
  const totalCost = costData.reduce((s, r) => s + r.total_cost, 0);
  const totalLiters = costData.reduce((s, r) => s + r.total_liters, 0);
  el.innerHTML = `
    <div class="grid-3">
      <div class="panel"><h3>Total Fuel Cost</h3><div style="font-size:28px;font-weight:700;">Rs. ${totalCost.toLocaleString()}</div></div>
      <div class="panel"><h3>Total Liters</h3><div style="font-size:28px;font-weight:700;">${Math.round(totalLiters)}</div></div>
      <div class="panel"><h3>Avg Cost/Liter</h3><div style="font-size:28px;font-weight:700;">Rs. ${totalLiters > 0 ? (totalCost/totalLiters).toFixed(2) : 0}</div></div>
    </div>
    <div class="grid-2">
      <div class="panel"><h3>Monthly Fuel Cost</h3><div class="chart-container"><canvas id="chart-fuel-monthly"></canvas></div></div>
      <div class="panel"><h3>Fuel Efficiency (L/100km)</h3><div class="chart-container"><canvas id="chart-fuel-eff"></canvas></div></div>
    </div>
    <div class="panel"><h3>Cost Breakdown by Vehicle</h3>
      <table><thead><tr><th>Vehicle</th><th>Total Cost</th><th>Liters</th><th>Avg Cost/L</th><th>Entries</th></tr></thead><tbody>
        ${costData.map(r => `<tr><td>${r.registration_no}</td><td>Rs. ${Math.round(r.total_cost)}</td><td>${Math.round(r.total_liters)}</td><td>Rs. ${r.avg_cost_per_liter || 0}</td><td>${r.entry_count}</td></tr>`).join('')}
      </tbody></table>
    </div>`;
  const months = [...new Set(costData.map(r => r.month))].sort();
  const monthlyCosts = months.map(m => costData.filter(r => r.month === m).reduce((s, r) => s + r.total_cost, 0));
  chartInstances.fuelMonthly = new Chart(document.getElementById('chart-fuel-monthly'), {
    type: 'bar', data: {
      labels: months,
      datasets: [{ label: 'Cost (Rs.)', data: monthlyCosts, backgroundColor: '#2563eb' }]
    }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });
  if (effData && effData.length) {
    const effVehicles = effData.filter(r => r.total_km > 0);
    chartInstances.fuelEff = new Chart(document.getElementById('chart-fuel-eff'), {
      type: 'bar', data: {
        labels: effVehicles.map(r => r.registration_no),
        datasets: [{ label: 'L/100km', data: effVehicles.map(r => r.efficiency), backgroundColor: '#eab308' }]
      }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
  }
}

async function loadMaintenance(el) {
  const [costData, pendData] = await Promise.all([
    apiGet('/api/reports/maintenance' + qs(filterState)),
    apiGet('/api/reports/maintenance/pending')
  ]);
  if (!costData || !costData.length) { el.innerHTML = '<div class="panel"><p>No maintenance data available.</p></div>'; return; }
  const totalCost = costData.reduce((s, r) => s + r.total_cost, 0);
  el.innerHTML = `
    <div class="grid-2">
      <div class="panel"><h3>Total Maintenance Cost</h3><div style="font-size:28px;font-weight:700;">Rs. ${totalCost.toLocaleString()}</div></div>
      <div class="panel"><h3>Total Records</h3><div style="font-size:28px;font-weight:700;">${costData.length}</div></div>
    </div>
    <div class="panel"><h3>Monthly Maintenance Cost</h3><div class="chart-container"><canvas id="chart-maint-monthly"></canvas></div></div>
    <div class="panel"><h3>Cost by Vehicle</h3>
      <table><thead><tr><th>Vehicle</th><th>Total Cost</th><th>Records</th><th>Last Maintenance</th></tr></thead><tbody>
        ${costData.map(r => `<tr><td>${r.registration_no}</td><td>Rs. ${Math.round(r.total_cost)}</td><td>${r.entry_count}</td><td>${r.last_date || '-'}</td></tr>`).join('')}
      </tbody></table>
    </div>`;
  const vehicles = [...new Set(costData.map(r => r.registration_no))];
  const vehCosts = vehicles.map(v => costData.filter(r => r.registration_no === v).reduce((s, r) => s + r.total_cost, 0));
  chartInstances.maintMonthly = new Chart(document.getElementById('chart-maint-monthly'), {
    type: 'bar', data: {
      labels: vehicles,
      datasets: [{ label: 'Cost (Rs.)', data: vehCosts, backgroundColor: '#7c3aed' }]
    }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });
  if (pendData && pendData.length) {
    el.innerHTML += `<div class="panel"><h3>Pending Maintenance Items</h3>
      <table><thead><tr><th>Vehicle</th><th>Date</th><th>Description</th><th>Cost</th><th>Mileage</th></tr></thead><tbody>
        ${pendData.map(r => `<tr><td>${r.registration_no}</td><td>${r.date}</td><td>${r.description}</td><td>Rs. ${r.cost}</td><td>${r.mileage || '-'}</td></tr>`).join('')}
      </tbody></table></div>`;
  }
}