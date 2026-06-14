(function startClock() {
    setInterval(() => {
        const now = new Date();
        const tEl = document.getElementById('dash-time');
        const dEl = document.getElementById('dash-date');
        if (tEl) tEl.innerText = now.toLocaleTimeString();
        if (dEl) dEl.innerText = now.toLocaleDateString('en-US', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
    }, 1000);
})();

(async function loadStats() {
    const stats = await apiGet('/api/stats');
    if (!stats) return;
    const vehEl = document.getElementById('stat-vehicles');
    const drvEl = document.getElementById('stat-drivers');
    const tripEl = document.getElementById('stat-trips');
    if (vehEl) vehEl.innerText = stats.vehicles;
    if (drvEl) drvEl.innerText = stats.drivers;
    if (tripEl) tripEl.innerText = stats.trips;
})();

(function initDashboard() {
    const role = window.USER_ROLE || '';
    if (!role) return;
    const endpoint = role === 'Administrator' ? '/api/dashboard/admin'
        : role === 'Supervisor' ? '/api/dashboard/supervisor'
        : '/api/dashboard/staff';
    (async () => {
        const data = await apiGet(endpoint);
        if (!data) return;
        if (role === 'Administrator') buildAdminCharts(data);
        else if (role === 'Supervisor') buildSupervisorCharts(data);
        else buildStaffCharts(data);
    })();
})();

function buildAdminCharts(data) {
    const charts = {};
    const colors = { 'Scheduled': '#eab308', 'In Transit': '#2563eb', 'Completed': '#16a34a', 'Cancelled': '#ef4444' };

    if (data.trip_status && data.trip_status.length) {
        const ctx = document.getElementById('admin-chart-trip-status');
        if (ctx) {
            charts.tripStatus = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.trip_status.map(r => r.status),
                    datasets: [{ data: data.trip_status.map(r => r.count), backgroundColor: data.trip_status.map(r => colors[r.status] || '#64748b') }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }

    if (data.monthly_cost && data.monthly_cost.length) {
        const ctx = document.getElementById('admin-chart-monthly-costs');
        if (ctx) {
            charts.monthlyCosts = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.monthly_cost.map(r => r.month),
                    datasets: [
                        { label: 'Fuel', data: data.monthly_cost.map(r => r.fuel_cost), backgroundColor: '#2563eb' },
                        { label: 'Maintenance', data: data.monthly_cost.map(r => r.maint_cost), backgroundColor: '#7c3aed' }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }

    if (data.fleet_composition && data.fleet_composition.length) {
        const ctx = document.getElementById('admin-chart-fleet-composition');
        if (ctx) {
            const pieColors = ['#2563eb', '#16a34a', '#eab308', '#ef4444', '#7c3aed', '#f97316', '#06b6d4'];
            charts.fleetComposition = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.fleet_composition.map(r => r.type),
                    datasets: [{ data: data.fleet_composition.map(r => r.count), backgroundColor: data.fleet_composition.map((_, i) => pieColors[i % pieColors.length]) }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }

    if (data.license_expiries && data.license_expiries.length) {
        const ctx = document.getElementById('admin-chart-license-expiry');
        if (ctx) {
            charts.licenseExpiry = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.license_expiries.map(r => r.driver_name),
                    datasets: [{ label: 'Days Until Expiry', data: data.license_expiries.map(r => r.days_until_expiry), backgroundColor: data.license_expiries.map(r => r.days_until_expiry <= 30 ? '#ef4444' : '#eab308') }]
                },
                options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } }
            });
        }
    }

    if (data.vehicle_utilization && data.vehicle_utilization.length) {
        const ctx = document.getElementById('admin-chart-vehicle-utilization');
        if (ctx) {
            charts.vehicleUtilization = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.vehicle_utilization.map(r => r.registration_no),
                    datasets: [{ label: 'Trip Count', data: data.vehicle_utilization.map(r => r.trip_count), backgroundColor: '#2563eb' }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }
    }

    if (data.route_completion && data.route_completion.length) {
        const ctx = document.getElementById('admin-chart-route-completion');
        if (ctx) {
            charts.routeCompletion = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.route_completion.map(r => r.route_name),
                    datasets: [{ label: 'Completion Rate (%)', data: data.route_completion.map(r => r.completion_rate), backgroundColor: data.route_completion.map(r => r.completion_rate >= 80 ? '#16a34a' : r.completion_rate >= 50 ? '#eab308' : '#ef4444') }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } }, plugins: { legend: { display: false } } }
            });
        }
    }

    const opsContainer = document.getElementById('admin-today-operations');
    if (opsContainer) {
        if (!data.today_operations || data.today_operations.length === 0) {
            opsContainer.innerHTML = '<p style="padding:10px; opacity:0.7;">No trips scheduled for today.</p>';
        } else {
            opsContainer.innerHTML = data.today_operations.map(op => {
                const badgeClass = op.status === 'Delayed' || op.status === 'Cancelled' ? 'badge-red'
                    : op.status === 'Completed' ? 'badge-purple'
                    : op.status === 'In Transit' ? 'badge-blue' : 'badge-green';
                return `<div class="trip-list-item">
                    <div><div class="route">${op.route_name}</div><div class="info">${op.registration_no} &bull; ${op.driver_name}</div></div>
                    <div style="text-align:right"><div style="font-weight:600;">${op.departure_time ? op.departure_time.substring(11, 16) : '--:--'}</div><span class="badge ${badgeClass}">${op.status}</span></div>
                </div>`;
            }).join('');
        }
    }
}

function buildSupervisorCharts(data) {
    const charts = {};
    const colors = { 'Scheduled': '#eab308', 'In Transit': '#2563eb', 'Completed': '#16a34a', 'Cancelled': '#ef4444' };

    if (data.today_trip_status && data.today_trip_status.length) {
        const ctx = document.getElementById('super-chart-trip-status');
        if (ctx) {
            charts.tripStatus = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.today_trip_status.map(r => r.status),
                    datasets: [{ data: data.today_trip_status.map(r => r.count), backgroundColor: data.today_trip_status.map(r => colors[r.status] || '#64748b') }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }

    if (data.route_completion && data.route_completion.length) {
        const ctx = document.getElementById('super-chart-route-completion');
        if (ctx) {
            charts.routeCompletion = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.route_completion.map(r => r.route_name),
                    datasets: [{ label: 'Completion Rate (%)', data: data.route_completion.map(r => r.completion_rate), backgroundColor: data.route_completion.map(r => r.completion_rate >= 80 ? '#16a34a' : r.completion_rate >= 50 ? '#eab308' : '#ef4444') }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } }, plugins: { legend: { display: false } } }
            });
        }
    }

    if (data.vehicle_utilization && data.vehicle_utilization.length) {
        const ctx = document.getElementById('super-chart-vehicle-utilization');
        if (ctx) {
            charts.vehicleUtilization = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.vehicle_utilization.map(r => r.registration_no),
                    datasets: [{ label: 'Trips This Month', data: data.vehicle_utilization.map(r => r.trip_count), backgroundColor: '#2563eb' }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }
    }

    if (data.fuel_cost_monthly && data.fuel_cost_monthly.length) {
        const ctx = document.getElementById('super-chart-fuel-cost');
        if (ctx) {
            charts.fuelCost = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.fuel_cost_monthly.map(r => r.month),
                    datasets: [{ label: 'Fuel Cost (Rs.)', data: data.fuel_cost_monthly.map(r => r.total_cost), backgroundColor: '#eab308' }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }
    }

    const opsContainer = document.getElementById('super-today-operations');
    if (opsContainer) {
        if (!data.today_operations || data.today_operations.length === 0) {
            opsContainer.innerHTML = '<p style="padding:10px; opacity:0.7;">No trips scheduled for today.</p>';
        } else {
            opsContainer.innerHTML = data.today_operations.slice(0, 5).map(op => {
                const badgeClass = op.status === 'Delayed' || op.status === 'Cancelled' ? 'badge-red'
                    : op.status === 'Completed' ? 'badge-purple'
                    : op.status === 'In Transit' ? 'badge-blue' : 'badge-green';
                return `<div class="trip-list-item">
                    <div><div class="route">${op.route_name}</div><div class="info">${op.registration_no} &bull; ${op.driver_name}</div></div>
                    <div style="text-align:right"><div style="font-weight:600;">${op.departure_time ? op.departure_time.substring(11, 16) : '--:--'}</div><span class="badge ${badgeClass}">${op.status}</span></div>
                </div>`;
            }).join('');
        }
    }
}

function buildStaffCharts(data) {
    const charts = {};

    if (data.fleet_composition && data.fleet_composition.length) {
        const ctx = document.getElementById('staff-chart-fleet-composition');
        if (ctx) {
            const pieColors = ['#2563eb', '#16a34a', '#eab308', '#ef4444', '#7c3aed', '#f97316', '#06b6d4'];
            charts.fleetComposition = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.fleet_composition.map(r => r.type),
                    datasets: [{ data: data.fleet_composition.map(r => r.count), backgroundColor: data.fleet_composition.map((_, i) => pieColors[i % pieColors.length]) }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }

    const scheduleContainer = document.getElementById('staff-today-schedule');
    if (scheduleContainer) {
        if (!data.my_trips || data.my_trips.length === 0) {
            scheduleContainer.innerHTML = '<p style="padding:10px; opacity:0.7;">No trips scheduled for you today.</p>';
        } else {
            scheduleContainer.innerHTML = data.my_trips.map(op => {
                const badgeClass = op.status === 'Delayed' || op.status === 'Cancelled' ? 'badge-red'
                    : op.status === 'Completed' ? 'badge-purple'
                    : op.status === 'In Transit' ? 'badge-blue' : 'badge-green';
                return `<div class="trip-list-item">
                    <div><div class="route">${op.route_name}</div><div class="info">${op.registration_no}</div></div>
                    <div style="text-align:right"><div style="font-weight:600;">${op.departure_time ? op.departure_time.substring(11, 16) : '--:--'}</div><span class="badge ${badgeClass}">${op.status}</span></div>
                </div>`;
            }).join('');
        }
    }
}

(async function loadMonitoring() {
    const tbody = document.getElementById('monitoring-table-body');
    if (!tbody) return;
    const data = await apiGet('/api/monitoring/vehicles');
    if (!data) return;
    tbody.innerHTML = data.map(v => {
        const statusBadge = v.trip_count == 0
            ? '<span class="badge badge-red">Unassigned</span>'
            : '<span class="badge badge-green">Active</span>';
        return `<tr><td>${v.registration_no}</td><td>${v.type}</td><td>${v.capacity}</td><td>${v.mileage || 0} km</td><td>${v.trip_count}</td><td>${statusBadge}</td></tr>`;
    }).join('');
})();

let viewerRouteLayer = null;
let viewerMap = null;

function viewerColorIcon(color) {
    return L.divIcon({
        className: '',
        html: `<div style="background:${color};border-radius:50%;width:22px;height:22px;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.3);"></div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
    });
}
const vGreenIcon = viewerColorIcon('#22c55e');
const vRedIcon = viewerColorIcon('#ef4444');
const vBlueIcon = viewerColorIcon('#3b82f6');

(async function initViewer() {
    const sel = document.getElementById('v_route_select');
    if (!sel) return;
    const routes = await apiGet('/api/routes');
    if (routes) {
        sel.innerHTML = '<option value="">-- Select --</option>' + routes.map(r => `<option value="${r.id}">${r.route_name}</option>`).join('');
    }
    if (document.getElementById('map')) {
        viewerMap = L.map('map').setView([6.9271, 79.8612], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(viewerMap);
    }
})();

async function loadRouteViewer() {
    const routeId = document.getElementById('v_route_select').value;
    if (!routeId) return;
    const route = await apiGet(`/api/routes/${routeId}`);
    if (!route) return;

    if (viewerRouteLayer && viewerMap) viewerMap.removeLayer(viewerRouteLayer);
    viewerRouteLayer = L.layerGroup().addTo(viewerMap);

    if (route.path_geometry) {
        const coords = JSON.parse(route.path_geometry);
        L.polyline(coords, { color: '#2563eb', weight: 5 }).addTo(viewerRouteLayer);
        if (coords.length > 0) {
            L.marker(coords[0], { icon: vGreenIcon }).addTo(viewerRouteLayer).bindPopup("Start");
            L.marker(coords[coords.length - 1], { icon: vRedIcon }).addTo(viewerRouteLayer).bindPopup("End");
        }
        viewerMap.fitBounds(coords);
    }
    const stops = JSON.parse(route.stops || '[]');
    const startSelect = document.getElementById('v_start_stop');
    const endSelect = document.getElementById('v_end_stop');
    startSelect.innerHTML = '';
    endSelect.innerHTML = '';
    stops.forEach((s, idx) => {
        L.marker([s.lat, s.lon], { icon: vBlueIcon }).addTo(viewerRouteLayer).bindPopup(s.name);
        startSelect.innerHTML += `<option value="${idx}">${s.name}</option>`;
        endSelect.innerHTML += `<option value="${idx}">${s.name}</option>`;
    });
    document.getElementById('fare-panel').style.display = 'block';
}

function calculateViewerFare() {
    const startIdx = parseInt(document.getElementById('v_start_stop').value);
    const endIdx = parseInt(document.getElementById('v_end_stop').value);
    const routeId = document.getElementById('v_route_select').value;
    fetch(`/api/routes/${routeId}`).then(r => r.json()).then(route => {
        const stops = JSON.parse(route.stops || '[]');
        let totalDist = 0;
        const min = Math.min(startIdx, endIdx);
        const max = Math.max(startIdx, endIdx);
        for (let i = min; i < max; i++) {
            if (stops[i] && stops[i + 1]) totalDist += haversine(stops[i].lat, stops[i].lon, stops[i + 1].lat, stops[i + 1].lon);
        }
        const fare = 20 + (totalDist * 5);
        document.getElementById('fare-result').innerHTML = `Rs. ${fare.toFixed(2)} (approx ${totalDist.toFixed(1)} km)`;
    });
}

function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
