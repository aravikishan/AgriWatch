/* AgriWatch -- Dashboard JavaScript
   Time-series charts, gauge widgets, field grid visualization
*/

// ========== Utility ==========

function apiGet(url) {
    return fetch(url).then(function(r) { return r.json(); });
}

function apiPost(url, body) {
    return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : '{}',
    }).then(function(r) { return r.json(); });
}

function formatTime(isoStr) {
    if (!isoStr) return '--';
    var d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(isoStr) {
    if (!isoStr) return '--';
    return new Date(isoStr).toLocaleDateString();
}

// ========== Dashboard Summary ==========

function loadDashboardSummary() {
    apiGet('/api/dashboard/summary').then(function(data) {
        var el = document.getElementById('alert-count');
        if (el) el.textContent = data.alert_count || 0;
        var healthEl = document.getElementById('avg-health');
        if (healthEl && data.fields && data.fields.length > 0) {
            var sum = 0;
            data.fields.forEach(function(f) { sum += f.health_score || 0; });
            healthEl.textContent = Math.round(sum / data.fields.length) + '%';
        }
    });
}

// ========== Alerts ==========

function loadAlerts() {
    var container = document.getElementById('alerts-container');
    if (!container) return;
    apiGet('/api/alerts?limit=10').then(function(alerts) {
        if (!alerts.length) {
            container.innerHTML = '<p class="loading">No active alerts.</p>';
            return;
        }
        var html = '';
        alerts.forEach(function(a) {
            html += '<div class="alert-item">'
                + '<span class="alert-icon">&#9888;</span>'
                + '<span class="alert-message">' + (a.alert_message || 'Alert') + '</span>'
                + '<span class="alert-time">' + formatTime(a.recorded_at) + '</span>'
                + '</div>';
        });
        container.innerHTML = html;
    });
}

// ========== Simulate & Predict ==========

function simulateReadings(fieldId) {
    apiPost('/api/readings/simulate/' + fieldId).then(function(data) {
        loadLatestReadings();
        loadAlerts();
        loadDashboardSummary();
    });
}

function generatePrediction(fieldId) {
    apiPost('/api/predictions/' + fieldId + '/generate').then(function() {
        location.reload();
    });
}

// ========== Sensor Gauges ==========

function loadLatestReadings() {
    apiGet('/api/readings?limit=200').then(function(readings) {
        /* Group by sensor_id, keep the latest */
        var latest = {};
        readings.forEach(function(r) {
            if (!latest[r.sensor_id] || r.recorded_at > latest[r.sensor_id].recorded_at) {
                latest[r.sensor_id] = r;
            }
        });
        Object.keys(latest).forEach(function(sid) {
            updateGauge(sid, latest[sid]);
        });
    });
}

function updateGauge(sensorId, reading) {
    var el = document.getElementById('reading-' + sensorId);
    if (el) {
        var val = reading.value;
        if (reading.unit === 'lux' && val > 1000) {
            el.textContent = (val / 1000).toFixed(1) + 'k';
        } else {
            el.textContent = val.toFixed(1);
        }
    }
    /* Update arc */
    var arc = document.getElementById('arc-' + sensorId);
    if (arc) {
        var pct = getGaugePercent(reading.sensor_type, reading.value);
        var circumference = 157; /* approximate arc length */
        arc.setAttribute('stroke-dasharray', (pct * circumference / 100) + ' ' + circumference);
        /* Color based on health */
        if (reading.is_alert) {
            arc.setAttribute('stroke', '#e74c3c');
        } else if (pct > 80 || pct < 20) {
            arc.setAttribute('stroke', '#daa520');
        } else {
            arc.setAttribute('stroke', '#4a7c59');
        }
    }
}

function getGaugePercent(sensorType, value) {
    var ranges = {
        'temperature': { min: -10, max: 50 },
        'humidity': { min: 0, max: 100 },
        'soil_moisture': { min: 0, max: 100 },
        'ph': { min: 3, max: 10 },
        'light': { min: 0, max: 100000 },
    };
    var range = ranges[sensorType] || { min: 0, max: 100 };
    var pct = ((value - range.min) / (range.max - range.min)) * 100;
    return Math.max(0, Math.min(100, pct));
}

// ========== Time-Series Chart (Canvas) ==========

var chartInstance = null;

function loadSensorChart() {
    var sensorSel = document.getElementById('chart-sensor');
    var hoursSel = document.getElementById('chart-hours');
    if (!sensorSel || !sensorSel.value) return;
    var sensorId = sensorSel.value;
    var hours = hoursSel ? hoursSel.value : 24;
    apiGet('/api/readings/history/' + sensorId + '?hours=' + hours).then(function(data) {
        drawTimeSeriesChart(data);
    });
}

function drawTimeSeriesChart(readings) {
    var canvas = document.getElementById('sensor-chart') || document.getElementById('dashboard-chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width;
    var H = canvas.height;
    var pad = { top: 30, right: 30, bottom: 50, left: 60 };

    ctx.clearRect(0, 0, W, H);

    if (!readings || readings.length === 0) {
        ctx.fillStyle = '#5a5a5a';
        ctx.font = '14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No data available. Select a sensor and time range.', W / 2, H / 2);
        return;
    }

    var values = readings.map(function(r) { return r.value; });
    var times = readings.map(function(r) { return new Date(r.recorded_at); });
    var minVal = Math.min.apply(null, values);
    var maxVal = Math.max.apply(null, values);
    var valRange = maxVal - minVal || 1;
    var minTime = times[0].getTime();
    var maxTime = times[times.length - 1].getTime();
    var timeRange = maxTime - minTime || 1;

    var plotW = W - pad.left - pad.right;
    var plotH = H - pad.top - pad.bottom;

    function xPos(t) { return pad.left + ((t.getTime() - minTime) / timeRange) * plotW; }
    function yPos(v) { return pad.top + plotH - ((v - minVal) / valRange) * plotH; }

    /* Grid lines */
    ctx.strokeStyle = '#e0d5c1';
    ctx.lineWidth = 1;
    var gridLines = 5;
    for (var i = 0; i <= gridLines; i++) {
        var gy = pad.top + (plotH / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, gy);
        ctx.lineTo(W - pad.right, gy);
        ctx.stroke();
        /* Label */
        var gval = maxVal - (valRange / gridLines) * i;
        ctx.fillStyle = '#5a5a5a';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(gval.toFixed(1), pad.left - 8, gy + 4);
    }

    /* Time labels */
    var labelCount = Math.min(readings.length, 8);
    var step = Math.max(1, Math.floor(readings.length / labelCount));
    ctx.textAlign = 'center';
    for (var j = 0; j < readings.length; j += step) {
        var tx = xPos(times[j]);
        ctx.fillStyle = '#5a5a5a';
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText(formatTime(readings[j].recorded_at), tx, H - pad.bottom + 18);
        /* Tick */
        ctx.beginPath();
        ctx.moveTo(tx, H - pad.bottom);
        ctx.lineTo(tx, H - pad.bottom + 5);
        ctx.strokeStyle = '#c4a882';
        ctx.stroke();
    }

    /* Area fill */
    ctx.beginPath();
    ctx.moveTo(xPos(times[0]), yPos(values[0]));
    for (var k = 1; k < values.length; k++) {
        ctx.lineTo(xPos(times[k]), yPos(values[k]));
    }
    ctx.lineTo(xPos(times[values.length - 1]), pad.top + plotH);
    ctx.lineTo(xPos(times[0]), pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = 'rgba(74, 124, 89, 0.15)';
    ctx.fill();

    /* Line */
    ctx.beginPath();
    ctx.moveTo(xPos(times[0]), yPos(values[0]));
    for (var m = 1; m < values.length; m++) {
        ctx.lineTo(xPos(times[m]), yPos(values[m]));
    }
    ctx.strokeStyle = '#4a7c59';
    ctx.lineWidth = 2;
    ctx.stroke();

    /* Data points */
    for (var n = 0; n < values.length; n++) {
        ctx.beginPath();
        ctx.arc(xPos(times[n]), yPos(values[n]), 3, 0, Math.PI * 2);
        var isAlert = readings[n].is_alert;
        ctx.fillStyle = isAlert ? '#e74c3c' : '#4a7c59';
        ctx.fill();
    }

    /* Unit label */
    if (readings[0] && readings[0].unit) {
        ctx.fillStyle = '#5a5a5a';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Unit: ' + readings[0].unit, pad.left, pad.top - 10);
    }

    /* Sensor type title */
    if (readings[0] && readings[0].sensor_type) {
        ctx.fillStyle = '#2d5a27';
        ctx.font = 'bold 13px Inter, sans-serif';
        ctx.textAlign = 'right';
        var title = readings[0].sensor_type.replace('_', ' ');
        title = title.charAt(0).toUpperCase() + title.slice(1);
        ctx.fillText(title + ' Over Time', W - pad.right, pad.top - 10);
    }
}

// ========== Dashboard chart on load ==========

function loadDashboardChart() {
    /* Load first available sensor data for the dashboard overview chart */
    apiGet('/api/sensors').then(function(sensors) {
        if (sensors.length > 0) {
            var tempSensor = sensors.find(function(s) { return s.sensor_type === 'temperature'; });
            var sensorId = tempSensor ? tempSensor.id : sensors[0].id;
            apiGet('/api/readings/history/' + sensorId + '?hours=24').then(function(data) {
                drawTimeSeriesChart(data);
            });
        }
    });
}

// ========== Init ==========

document.addEventListener('DOMContentLoaded', function() {
    /* Load gauge readings if on sensors or dashboard page */
    if (document.getElementById('gauge-container') || document.querySelector('.field-cards')) {
        loadLatestReadings();
    }
    /* Load dashboard chart */
    var dashChart = document.getElementById('dashboard-chart');
    if (dashChart) {
        loadDashboardChart();
    }
});
