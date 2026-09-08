// NirmanDrishti — dashboard client
// MoSPI MPLADS Integrity Platform (SIH26102)

let mapInstance = null;
let markersLayer = null;

let allWorks = [];
let allAnomalies = [];
let allMps = [];
let benchmarks = {};          // category -> { avg, ceiling, unit }
let findingFilter = 'confirmed';

const VIEW_META = {
    dashboard: ['Audit Overview',      'Automated integrity screening of MPLADS sanctioned works'],
    findings:  ['Findings',            'Every alert raised, with the measurement behind it'],
    map:       ['Geospatial Map',      'Asset locations and contractor bidding network'],
    works:     ['Projects Register',   'Sanctioned works currently under audit'],
    mps:       ['MP Directory',        'Official allocation dataset for all constituencies'],
    method:    ['Methodology',         'How each detection engine reaches its conclusion']
};

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadAll();
});

/* ------------------------------------------------------------------ utils */

const $ = id => document.getElementById(id);

function fmt(n, dp = 2) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-IN', { minimumFractionDigits: dp, maximumFractionDigits: dp });
}

function fmtInt(n) {
    if (n === null || n === undefined || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-IN');
}

function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

const isConfirmed = a => a.severity === 'CRITICAL' || a.severity === 'HIGH';

function sevClass(sev) {
    if (sev === 'CRITICAL') return 'critical';
    if (sev === 'HIGH') return 'high';
    return 'advisory';
}

function sevLabel(sev) {
    return sev === 'MEDIUM' || sev === 'LOW' ? 'Advisory' : sev.charAt(0) + sev.slice(1).toLowerCase();
}

// Case reference, in the shape officers expect on a file.
function caseId(a) {
    const place = (a.constituency_name || 'GEN').replace(/[^A-Za-z]/g, '').slice(0, 3).toUpperCase() || 'GEN';
    const year = (a.detected_at || '').slice(0, 4) || '2026';
    return `MPLADS/${place}/${year}/${String(a.anomaly_id).padStart(4, '0')}`;
}

/* ------------------------------------------------- headline figure per type
   Each finding has one number that carries it. Pull that out of the stored
   evidence string and lead the card with it. */

function headline(a) {
    const ev = a.mathematical_evidence || '';
    let m;

    if (a.anomaly_type === 'SPATIAL_DUPLICATE') {
        m = ev.match(/Distance:\s*([\d.]+)\s*m/i);
        return {
            figure: m ? `${Number(m[1]).toFixed(1)} m` : '—',
            caption: 'between two works of the same category, in the same ward',
            rows: [['Method', 'Haversine great-circle distance'], ['Threshold', '≤ 100 m'], ['Measured', m ? `${m[1]} m` : '—']]
        };
    }

    if (a.anomaly_type === 'PRICE_INFLATION') {
        m = ev.match(/Price Ratio\s*=\s*([\d.]+)x/i);
        if (m) {
            const pct = (parseFloat(m[1]) - 1) * 100;
            const c = ev.match(/Max PWD Ceiling = Rs ([\d.]+)L/i);
            const s = ev.match(/Sanctioned = Rs ([\d.]+)L/i);
            return {
                figure: `+${pct.toFixed(1)}%`,
                caption: 'above the PWD Schedule of Rates ceiling',
                rows: [
                    ['Sanctioned', s ? `₹${s[1]} L` : '—'],
                    ['PWD ceiling', c ? `₹${c[1]} L` : '—'],
                    ['Ratio', `${m[1]}× (threshold 1.5×)`]
                ]
            };
        }
        const z = ev.match(/=\s*([\d.]+)\s*>\s*[\d.]+$/);
        return {
            figure: z ? `Z ${Number(z[1]).toFixed(2)}` : '—',
            caption: 'standard deviations above the mean sanctioned cost',
            rows: [['Method', 'Standard-score outlier test'], ['Threshold', 'Z > 2.5']]
        };
    }

    if (a.anomaly_type === 'CARTEL_BID_RIGGING') {
        m = ev.match(/=\s*(\d+)\s*tenders/i);
        return {
            figure: m ? `${m[1]} tenders` : '—',
            caption: 'bid on jointly by the same pair of contractors',
            rows: [['Method', 'Bipartite co-bidding graph'], ['Threshold', '≥ 2 shared tenders'], ['Co-bids', m ? m[1] : '—']]
        };
    }

    if (a.anomaly_type === 'FUND_STAGNATION') {
        m = ev.match(/Elapsed Days\s*=\s*(\d+)/i);
        const p = ev.match(/Progress\s*=\s*(\d+)%/i);
        return {
            figure: m ? `${fmtInt(m[1])} days` : '—',
            caption: `since sanction, at ${p ? p[1] : '—'}% physical progress`,
            rows: [['Method', 'Elapsed time vs. reported progress'], ['Threshold', '≥ 180 days below 20%'], ['Progress', p ? `${p[1]}%` : '—']]
        };
    }

    m = ev.match(/Unspent Ratio:\s*([\d.]+)%/i);
    return {
        figure: m ? `${m[1]}%` : '—',
        caption: 'of the constituency allocation remains unspent',
        rows: [['Method', 'Constituency balance check'], ['Threshold', '≥ ₹2.00 Cr unspent']]
    };
}

/* ------------------------------------------------------------------- load */

async function loadAll() {
    try {
        const [stats, works, anomalies, bm] = await Promise.all([
            fetch('/api/stats').then(r => r.json()),
            fetch('/api/works').then(r => r.json()),
            fetch('/api/anomalies').then(r => r.json()),
            fetch('/api/benchmarks').then(r => r.json()).catch(() => [])
        ]);

        allWorks = works;
        allAnomalies = anomalies;
        benchmarks = {};
        bm.forEach(b => benchmarks[b.category] = { ceiling: b.max_acceptable_rate_inr, avg: b.avg_rate_inr, unit: b.unit });

        renderScope(stats);
        renderKpis(stats);
        renderLadder();
        renderCostChart();
        renderTypeChart();
        renderFindings();
        renderMapMarkers(works);
        renderWorksTable(works);

        fetch('/api/mps').then(r => r.json()).then(mps => {
            allMps = mps;
            renderMpsTable(mps);
            $('nav-count-mps').textContent = mps.length;
            $('mps-foot').textContent = `${mps.length} members listed`;
        });

        initCartelGraph();
    } catch (err) {
        console.error('Dashboard load failed:', err);
    }
}

/* ------------------------------------------------------------ scope + kpis */

function renderScope(stats) {
    $('scope-mps').textContent = fmtInt(stats.total_mps_registered);
    $('scope-works').textContent = fmtInt(stats.total_works);
    $('scope-alloc').textContent = fmtInt(Math.round(stats.total_national_budget_cr));
    $('scope-time').textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
    $('nav-count-works').textContent = stats.total_works;
}

function renderKpis(stats) {
    const confirmed = allAnomalies.filter(isConfirmed);

    $('kpi-confirmed').textContent = confirmed.length;
    $('kpi-risk').textContent = fmt(stats.funds_at_risk_lakhs);

    // Largest rupee overcharge above the PWD ceiling, across all audited works.
    let worst = null;
    allWorks.forEach(w => {
        const b = benchmarks[w.work_category];
        if (!b) return;
        const excess = w.sanctioned_amount_lakhs - b.ceiling;
        if (excess > 0 && (!worst || excess > worst.excess)) worst = { excess, work: w, ceiling: b.ceiling };
    });

    $('kpi-overcharge').textContent = worst ? fmt(worst.excess) : '0.00';
    $('kpi-overcharge-foot').textContent = worst
        ? `${worst.work.constituency_name} · ceiling ₹${fmt(worst.ceiling)} L`
        : 'No work exceeds its ceiling';

    const engines = new Set(confirmed.map(a => a.anomaly_type));
    $('kpi-engines').textContent = engines.size;
    $('nav-count-findings').textContent = confirmed.length;
}

function renderLadder() {
    const c = allAnomalies.filter(a => a.severity === 'CRITICAL').length;
    const h = allAnomalies.filter(a => a.severity === 'HIGH').length;
    $('lad-critical').textContent = c;
    $('lad-high').textContent = h;
    $('lad-advisory').textContent = fmtInt(allAnomalies.length - c - h);
}

/* ----------------------------------------------------------------- charts */

function renderCostChart() {
    const rows = allWorks
        .map(w => {
            const b = benchmarks[w.work_category];
            if (!b) return null;
            return { w, ceiling: b.ceiling, ratio: w.sanctioned_amount_lakhs / b.ceiling };
        })
        .filter(r => r && r.ratio > 1)
        .sort((a, b) => b.ratio - a.ratio)
        .slice(0, 5);

    const el = $('chart-cost');

    if (!rows.length) {
        el.innerHTML = '<div class="empty-row">No work exceeds its PWD ceiling.</div>';
        return;
    }

    const scale = Math.max(...rows.map(r => Math.max(r.w.sanctioned_amount_lakhs, r.ceiling))) * 1.12;

    el.innerHTML = rows.map(r => {
        const pctBar = (r.w.sanctioned_amount_lakhs / scale) * 100;
        const pctCeil = (r.ceiling / scale) * 100;
        const over = r.ratio >= 1.5;
        return `
            <div class="bar-row">
                <div class="bar-head">
                    <span class="name">${esc(r.w.work_category)} <span class="secondary">· ${esc(r.w.constituency_name)}</span></span>
                    <span class="val">₹${fmt(r.w.sanctioned_amount_lakhs)} L · ${r.ratio.toFixed(2)}×</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill ${over ? 'over' : 'under'}" style="width:${pctBar.toFixed(1)}%"></div>
                    <div class="bar-ceiling${pctCeil > 62 ? ' flip' : ''}" style="left:${pctCeil.toFixed(1)}%" data-label="PWD ceiling ₹${fmt(r.ceiling)} L"></div>
                </div>
            </div>`;
    }).join('');
}

function renderTypeChart() {
    const labels = {
        SPATIAL_DUPLICATE: 'Duplicate assets',
        PRICE_INFLATION: 'Cost above ceiling',
        CARTEL_BID_RIGGING: 'Collusive bidding',
        FUND_STAGNATION: 'Stalled works',
        IDLE_FUNDS: 'Unspent balances'
    };

    const counts = {};
    allAnomalies.forEach(a => counts[a.anomaly_type] = (counts[a.anomaly_type] || 0) + 1);

    // The advisory tier outnumbers confirmed findings by two orders of magnitude.
    // Scaling them on one axis would flatten every real finding to a sliver, so
    // confirmed types get their own scale and the advisory count is stated apart.
    const confirmedRows = Object.entries(counts)
        .filter(([t]) => t !== 'IDLE_FUNDS')
        .sort((a, b) => b[1] - a[1]);

    const max = Math.max(1, ...confirmedRows.map(r => r[1]));

    const bars = confirmedRows.map(([type, n]) => {
        const cls = (type === 'SPATIAL_DUPLICATE' || type === 'PRICE_INFLATION') ? 'crit' : 'high';
        return `
            <div class="bar-row">
                <div class="bar-head">
                    <span class="name">${labels[type] || type}</span>
                    <span class="val">${fmtInt(n)}</span>
                </div>
                <div class="bar-simple-track">
                    <div class="bar-simple-fill ${cls}" style="width:${((n / max) * 100).toFixed(1)}%"></div>
                </div>
            </div>`;
    }).join('');

    const advisory = counts.IDLE_FUNDS || 0;
    const aside = advisory ? `
        <div class="chart-aside">
            <div class="bar-head" style="margin-bottom:2px">
                <span class="name">${labels.IDLE_FUNDS} <span class="secondary">· advisory</span></span>
                <span class="val">${fmtInt(advisory)}</span>
            </div>
            <div class="section-note">Excluded from the scale above — constituency-level notices, reported separately from confirmed findings.</div>
        </div>` : '';

    $('chart-types').innerHTML = bars + aside;
}

/* --------------------------------------------------------------- findings */

function findingCard(a, idx) {
    const h = headline(a);
    const sc = sevClass(a.severity);

    return `
        <article class="finding sev-${sc}">
            <div class="finding-top">
                <span class="case-id">${caseId(a)}</span>
                <span class="chip chip-${sc}">${sevLabel(a.severity)}</span>
            </div>

            <div class="headline-figure">${esc(h.figure)}</div>
            <div class="headline-caption">${esc(h.caption)}</div>

            <div class="finding-name">${esc(a.title)}</div>
            <p class="finding-desc">${esc(a.description)}</p>

            <dl class="evidence-grid">
                ${h.rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}
            </dl>

            <div class="finding-actions">
                <button class="link-btn" onclick="viewEvidence(${idx})">Full evidence →</button>
            </div>
        </article>`;
}

function renderFindings() {
    const confirmed = allAnomalies.filter(isConfirmed);

    $('priority-findings').innerHTML = confirmed.length
        ? confirmed.slice(0, 4).map(a => findingCard(a, allAnomalies.indexOf(a))).join('')
        : '<div class="empty-row">No confirmed findings.</div>';

    const list = findingFilter === 'confirmed' ? confirmed : allAnomalies;
    const shown = list.slice(0, 60);

    $('all-findings').innerHTML = shown.length
        ? shown.map(a => findingCard(a, allAnomalies.indexOf(a))).join('')
        : '<div class="empty-row">No findings in this view.</div>';

    $('findings-note').textContent = findingFilter === 'confirmed'
        ? `${confirmed.length} confirmed findings (critical and high severity).`
        : `Showing ${shown.length} of ${fmtInt(allAnomalies.length)} alerts, including the advisory tier.`;

    $('filt-confirmed').className = 'btn' + (findingFilter === 'confirmed' ? ' btn-primary' : '');
    $('filt-all').className = 'btn' + (findingFilter === 'all' ? ' btn-primary' : '');
}

function setFindingFilter(f) {
    findingFilter = f;
    renderFindings();
}

/* -------------------------------------------------------------------- map */

function initMap() {
    mapInstance = L.map('gis-map', { scrollWheelZoom: false }).setView([22.9, 79.5], 5);

    // Standard OSM tiles — keyless and reliable. They are desaturated in CSS
    // (.leaflet-tile-pane) so the basemap reads as muted cartography and the
    // risk pins remain the only saturated thing on the map.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(mapInstance);

    markersLayer = L.layerGroup().addTo(mapInstance);
}

function renderMapMarkers(works) {
    markersLayer.clearLayers();

    works.forEach(w => {
        let cls = 'pin-normal', glyph = '✓';
        if (w.risk_level === 'Critical' || w.anomaly_count >= 2) { cls = 'pin-critical'; glyph = '!'; }
        else if (w.risk_level === 'High' || w.anomaly_count === 1) { cls = 'pin-high'; glyph = '!'; }

        const marker = L.marker([w.latitude, w.longitude], {
            icon: L.divIcon({
                className: '',
                html: `<div class="custom-pin ${cls}">${glyph}</div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        });

        marker.bindPopup(`
            <div class="popup-title">${esc(w.work_name)}</div>
            <dl class="popup-grid">
                <dt>Category</dt><dd>${esc(w.work_category)}</dd>
                <dt>Location</dt><dd>${esc(w.location_name)}</dd>
                <dt>Constituency</dt><dd>${esc(w.constituency_name)}</dd>
                <dt>Sanctioned</dt><dd>₹${fmt(w.sanctioned_amount_lakhs)} L</dd>
                <dt>Progress</dt><dd>${w.completion_percent}%</dd>
                <dt>Coordinates</dt><dd class="mono">${w.latitude.toFixed(4)}, ${w.longitude.toFixed(4)}</dd>
                <dt>Alerts</dt><dd>${w.anomaly_count}</dd>
            </dl>`);

        markersLayer.addLayer(marker);
    });
}

/* ----------------------------------------------------------------- tables */

function renderWorksTable(works) {
    const tbody = $('works-table-body');

    if (!works.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-row">No works match this query.</td></tr>';
        return;
    }

    tbody.innerHTML = works.map(w => {
        const risk = w.risk_level === 'Critical' ? 'critical' : (w.risk_level === 'High' ? 'high' : 'ok');
        const stalled = w.completion_percent < 20;
        return `
            <tr>
                <td class="mono">${esc(w.work_id)}</td>
                <td><span class="primary">${esc(w.work_name)}</span><br><span class="secondary">${esc(w.location_name)}</span></td>
                <td>${esc(w.work_category)}</td>
                <td>${esc(w.constituency_name)}<br><span class="secondary">${esc(w.mp_name)}</span></td>
                <td class="num">${fmt(w.sanctioned_amount_lakhs)}</td>
                <td>
                    <div class="progress">
                        <div class="progress-track"><div class="progress-fill ${stalled ? 'stalled' : ''}" style="width:${w.completion_percent}%"></div></div>
                        <span class="progress-val">${w.completion_percent}%</span>
                    </div>
                </td>
                <td><span class="secondary">${esc(w.status)}</span></td>
                <td><span class="chip chip-${risk}">${esc(w.risk_level)}</span></td>
            </tr>`;
    }).join('');

    $('works-foot').textContent = `${works.length} works listed`;
}

function filterTable() {
    const q = $('table-search').value.toLowerCase();
    renderWorksTable(allWorks.filter(w =>
        [w.work_name, w.work_id, w.location_name, w.constituency_name, w.mp_name, w.work_category]
            .some(f => String(f).toLowerCase().includes(q))));
}

function renderMpsTable(mps) {
    const tbody = $('mps-table-body');

    if (!mps.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No records found.</td></tr>';
        return;
    }

    tbody.innerHTML = mps.map((m, i) => `
        <tr>
            <td class="mono">${i + 1}</td>
            <td><span class="primary">${esc(m.mp_name)}</span></td>
            <td>${esc(m.constituency_name)}</td>
            <td><span class="secondary">${esc(m.state)}</span></td>
            <td class="num">${fmt(m.total_allocated_cr)}</td>
            <td class="num mono">${fmtInt(Math.round(m.total_allocated_cr * 1e7))}</td>
            <td><span class="secondary">${esc(m.house)}</span></td>
        </tr>`).join('');
}

function filterMpsTable() {
    const q = $('mps-search').value.toLowerCase();
    renderMpsTable(allMps.filter(m =>
        [m.mp_name, m.constituency_name, m.state].some(f => String(f).toLowerCase().includes(q))));
}

/* ------------------------------------------------------------ cartel graph */

async function initCartelGraph() {
    try {
        const data = await fetch('/api/cartel-network').then(r => r.json());
        const container = $('cartel-network');
        if (!container) return;

        const nodes = new vis.DataSet(data.nodes.map(n => {
            if (n.type === 'contractor') {
                const flagged = n.risk > 0.5;
                return {
                    id: n.id,
                    label: n.label.length > 20 ? n.label.slice(0, 18) + '…' : n.label,
                    title: `${n.label}\nRisk score ${n.risk}\nDistrict ${n.district}`,
                    shape: 'dot',
                    size: flagged ? 15 : 10,
                    color: { background: flagged ? '#B3261E' : '#1B7F4B', border: '#FFFFFF' },
                    borderWidth: 2,
                    font: { color: '#10151F', size: 11, face: 'Inter' }
                };
            }
            return {
                id: n.id,
                label: n.label,
                title: `Tender ${n.id}\nEstimate ₹${n.cost} L`,
                shape: 'box',
                color: { background: '#EEF3FA', border: '#24508F' },
                borderWidth: 1,
                font: { color: '#16325A', size: 10, face: 'IBM Plex Mono' },
                margin: 7
            };
        }));

        const edges = new vis.DataSet(data.links.map(l => ({
            from: l.source,
            to: l.target,
            color: { color: l.is_winner ? '#24508F' : '#C2CAD6' },
            width: l.is_winner ? 2 : 1,
            dashes: !l.is_winner,
            title: `₹${l.amount} L — ${l.is_winner ? 'winning bid' : 'losing bid'}`
        })));

        new vis.Network(container, { nodes, edges }, {
            physics: { barnesHut: { gravitationalConstant: -3200, springLength: 105 }, stabilization: { iterations: 120 } },
            interaction: { hover: true, tooltipDelay: 120 }
        });

        const flagged = data.nodes.filter(n => n.type === 'contractor' && n.risk > 0.5).length;
        $('cartel-note').textContent = `${flagged} contractors above risk threshold`;
    } catch (err) {
        console.error('Cartel graph failed:', err);
    }
}

/* ------------------------------------------------------------------ modal */

function viewEvidence(index) {
    const a = allAnomalies[index];
    if (!a) return;

    const h = headline(a);
    $('modal-title').textContent = a.title;

    $('modal-content').innerHTML = `
        <div class="finding-top" style="margin-bottom:14px">
            <span class="case-id">${caseId(a)}</span>
            <span class="chip chip-${sevClass(a.severity)}">${sevLabel(a.severity)}</span>
        </div>

        <div class="field">
            <div class="field-label">Key measurement</div>
            <div class="headline-figure">${esc(h.figure)}</div>
            <div class="headline-caption" style="margin-bottom:0">${esc(h.caption)}</div>
        </div>

        <div class="field">
            <div class="field-label">Narrative</div>
            <p class="finding-desc">${esc(a.description)}</p>
        </div>

        <div class="field">
            <div class="field-label">Recorded evidence</div>
            <pre class="proof">${esc(a.mathematical_evidence)}</pre>
        </div>

        <div class="field">
            <div class="field-label">Case record</div>
            <dl class="evidence-grid" style="margin-top:0;padding-top:0;border-top:0">
                <dt>Work ID</dt><dd>${esc(a.work_id || 'Constituency level')}</dd>
                <dt>Detector</dt><dd>${esc(a.anomaly_type)}</dd>
                <dt>Status</dt><dd>${esc(a.status)}</dd>
                <dt>Detected</dt><dd>${esc(a.detected_at)}</dd>
            </dl>
        </div>`;

    $('evidence-modal').hidden = false;
}

function closeModal() { $('evidence-modal').hidden = true; }

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* ------------------------------------------------------------------ views */

function switchView(view) {
    Object.keys(VIEW_META).forEach(v => {
        const el = $('view-' + v);
        if (el) el.hidden = v !== view;
    });

    document.querySelectorAll('.nav-item').forEach(b =>
        b.classList.toggle('active', b.dataset.view === view));

    const [title, sub] = VIEW_META[view];
    $('page-title').textContent = title;
    $('page-sub').textContent = sub;
    $('crumb').textContent = title;

    window.scrollTo({ top: 0 });
    if (view === 'map' && mapInstance) setTimeout(() => mapInstance.invalidateSize(), 120);
}

/* ----------------------------------------------------------------- actions */

function toast(title, body, ms = 5200) {
    $('toast-title').textContent = title;
    $('toast-body').innerHTML = body;
    $('toast').hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => $('toast').hidden = true, ms);
}

async function runLiveAudit() {
    const btn = $('btn-trigger-audit');
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Auditing…';
    btn.disabled = true;

    try {
        const out = await fetch('/api/trigger-audit', { method: 'POST' }).then(r => r.json());
        await loadAll();
        const r = out.results;
        toast('Audit complete', [
            `Duplicate assets      ${r.spatial_duplicates}`,
            `Collusive pairs       ${r.cartel_rings}`,
            `Cost above ceiling    ${r.price_inflations}`,
            `Stalled works         ${r.stagnant_works}`
        ].join('<br>'));
    } catch (err) {
        toast('Audit failed', esc(String(err)));
    } finally {
        btn.innerHTML = original;
        btn.disabled = false;
    }
}

async function resetData() {
    if (!confirm('Re-ingest the official portal dataset and re-run all detectors?')) return;
    try {
        await fetch('/api/reset-data', { method: 'POST' });
        await loadAll();
        toast('Dataset re-synced', 'Portal records reloaded and detectors re-run.');
    } catch (err) {
        toast('Re-sync failed', esc(String(err)));
    }
}
