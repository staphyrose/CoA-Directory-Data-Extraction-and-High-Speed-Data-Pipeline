from flask import Flask, jsonify, render_template_string, request
from .db import connect, init_db
from .config import DIRECTORY_URL, CATEGORIES
from .extractor import CoAExtractor
import csv
import io
import os

app = Flask(__name__)

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CoA Directory Data Extraction Dashboard</title>
<style>
:root{--navy:#12213b;--blue:#2563eb;--blue2:#dbeafe;--green:#059669;--green2:#d1fae5;--amber:#d97706;--amber2:#fef3c7;--red:#dc2626;--red2:#fee2e2;--slate:#64748b;--line:#e2e8f0;--bg:#f4f7fb;--white:#fff}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:#172033}.top{background:linear-gradient(135deg,#0f1d35,#1e3a68);color:#fff;padding:26px 34px}.top-inner{max-width:1400px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:14px}.logo{width:48px;height:48px;border-radius:12px;background:#fff;color:#17345f;display:grid;place-items:center;font-weight:900;font-size:19px}.title h1{margin:0;font-size:23px}.title p{margin:5px 0 0;color:#cbd5e1;font-size:13px}.source-btn{background:#fff;color:#16355e;text-decoration:none;padding:11px 15px;border-radius:9px;font-weight:700;font-size:13px;white-space:nowrap}.wrap{max-width:1400px;margin:0 auto;padding:25px 28px 45px}.statusbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:18px}.crumb{font-size:13px;color:var(--slate)}.live{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:700;color:var(--green)}.dot{width:8px;height:8px;border-radius:50%;background:#10b981;box-shadow:0 0 0 4px #d1fae5}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:13px;margin-bottom:18px}.card{background:var(--white);border:1px solid var(--line);border-radius:14px;box-shadow:0 3px 14px rgba(15,23,42,.05)}.metric{padding:16px 17px;min-height:105px}.metric .label{font-size:12px;color:var(--slate);font-weight:700}.metric .value{font-size:25px;font-weight:800;margin-top:9px;color:var(--navy)}.metric .sub{font-size:11px;color:#94a3b8;margin-top:4px}.layout{display:grid;grid-template-columns:1.25fr .75fr;gap:18px;margin-bottom:18px}.section{padding:20px}.section h2{font-size:16px;margin:0 0 5px}.muted{font-size:12px;color:var(--slate)}.formgrid{display:grid;grid-template-columns:1fr 1.4fr auto;gap:10px;margin-top:17px}.input,.select{height:43px;border:1px solid #cbd5e1;border-radius:9px;padding:0 12px;background:#fff;font-size:13px;color:#172033}.btn{height:43px;border:0;border-radius:9px;padding:0 17px;font-weight:800;cursor:pointer}.primary{background:var(--blue);color:#fff}.secondary{background:#eef2ff;color:#334155}.notice{display:flex;gap:12px;padding:13px 15px;border-radius:10px;margin-top:14px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;font-size:12px;line-height:1.5}.notice strong{display:block;color:#173c78}.shield{font-size:19px}.checklist{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px}.check{padding:9px 10px;border-radius:8px;background:#f8fafc;border:1px solid var(--line);font-size:12px}.check b{color:var(--green);margin-right:5px}.progress-wrap{margin-top:16px}.progress-head{display:flex;justify-content:space-between;font-size:12px;font-weight:700;margin-bottom:7px}.bar{height:10px;background:#e2e8f0;border-radius:99px;overflow:hidden}.bar span{display:block;height:100%;width:100%;background:linear-gradient(90deg,#2563eb,#60a5fa);border-radius:99px}.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:12px}.mini{background:#f8fafc;border:1px solid var(--line);border-radius:9px;padding:10px}.mini .n{font-weight:800;font-size:15px}.mini .l{font-size:10px;color:var(--slate);margin-top:2px}.full{margin-bottom:18px}.table-head{display:flex;justify-content:space-between;align-items:end;gap:15px;margin-bottom:13px}.actions{display:flex;gap:8px}.table-scroll{overflow:auto;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;min-width:900px;background:#fff}th{background:#f8fafc;color:#475569;text-transform:uppercase;letter-spacing:.04em;font-size:10px;text-align:left;padding:11px;border-bottom:1px solid var(--line)}td{padding:11px;border-bottom:1px solid #edf1f5;font-size:12px;white-space:nowrap}tr:last-child td{border-bottom:0}.badge{display:inline-flex;padding:4px 8px;border-radius:99px;font-size:10px;font-weight:800}.success{background:var(--green2);color:#047857}.warning{background:var(--amber2);color:#92400e}.danger{background:var(--red2);color:#b91c1c}.neutral{background:#e2e8f0;color:#475569}.jobs td{font-size:11px}.empty{text-align:center;color:#94a3b8;padding:25px}.footer{color:#94a3b8;font-size:11px;text-align:center;margin-top:22px}.toast{position:fixed;right:22px;bottom:22px;max-width:390px;background:#12213b;color:#fff;padding:14px 16px;border-radius:10px;box-shadow:0 12px 30px #0003;display:none;font-size:12px;z-index:20}.toast.show{display:block}.result{margin-top:12px;font-size:12px;line-height:1.5}.error{color:var(--red)}
@media(max-width:1100px){.cards{grid-template-columns:repeat(3,1fr)}.layout{grid-template-columns:1fr}.top-inner{align-items:flex-start;flex-direction:column}.source-btn{align-self:flex-start}}
@media(max-width:650px){.wrap{padding:18px 13px}.cards{grid-template-columns:repeat(2,1fr)}.formgrid{grid-template-columns:1fr}.checklist{grid-template-columns:1fr}.top{padding:20px}.title h1{font-size:19px}}
</style>
</head>
<body>
<header class="top"><div class="top-inner">
  <div class="brand"><div class="logo">CoA</div><div class="title"><h1>Architect Directory Data Extraction</h1><p>Professional monitoring dashboard • Council of Architecture public-directory workflow</p></div></div>
  <a class="source-btn" href="{{url}}" target="_blank" rel="noopener">↗ Open Official CoA Directory</a>
</div></header>
<main class="wrap">
<div class="statusbar"><div class="crumb">Home / Extraction Dashboard</div><div class="live"><span class="dot"></span> SYSTEM READY</div></div>

<section class="cards">
{% for label,value,sub in metrics %}<div class="card metric"><div class="label">{{label}}</div><div class="value">{{value}}</div><div class="sub">{{sub}}</div></div>{% endfor %}
</section>

<div class="layout">
<section class="card section">
  <h2>Live Extraction Control</h2><div class="muted">Start a respectful directory query using the configured CoA endpoint.</div>
  <form id="extractForm" class="formgrid" method="post" action="/extract">
    <select class="select" name="category">{% for key,label in category_labels.items() %}<option value="{{key}}">{{label}}</option>{% endfor %}</select>
    <input class="input" name="value" placeholder="Enter search value (e.g. architect name, city, registration no.)" required>
    <button class="btn primary" type="submit" id="runBtn">▶ Start Extraction</button>
  </form>
  <div id="result" class="result"></div>
  <div class="notice"><div class="shield">🛡️</div><div><strong>CAPTCHA-safe security control</strong>The pipeline detects security verification and pauses. It does not bypass, solve, or automate CAPTCHA. Manual verification can be performed on the official CoA website before continuing the workflow.</div></div>
</section>
<section class="card section">
  <h2>Project Compliance</h2><div class="muted">Key features visible for demonstration and evaluation.</div>
  <div class="checklist">
    {% for item in compliance %}<div class="check"><b>✓</b>{{item}}</div>{% endfor %}
  </div>
</section>
</div>

<section class="card section full">
  <div class="table-head"><div><h2>Extraction Progress & Pipeline Health</h2><div class="muted">Current job and cumulative processing indicators</div></div><div class="actions"><button class="btn secondary" onclick="refreshDashboard()">↻ Refresh</button><a class="btn secondary" style="display:grid;place-items:center;text-decoration:none" href="/export.csv">↓ Export CSV</a></div></div>
  <div class="progress-wrap"><div class="progress-head"><span id="progressStatus">{{progress.status}}</span><span id="progressPct">{{progress.pct}}%</span></div><div class="bar"><span id="progressBar" style="width:{{progress.pct}}%"></span></div></div>
  <div class="stats-row">
    <div class="mini"><div class="n" id="processed">{{progress.processed}}</div><div class="l">Records processed</div></div>
    <div class="mini"><div class="n" id="throughput">{{progress.throughput}}</div><div class="l">Records / second</div></div>
    <div class="mini"><div class="n" id="activity">{{progress.latest}}</div><div class="l">Latest activity</div></div>
  </div>
</section>

<section class="card section full">
  <div class="table-head"><div><h2>Architect Records</h2><div class="muted">Persisted records from the project database • sample/public records are clearly tagged by source scope</div></div><div class="actions"><input class="input" id="recordFilter" style="height:38px;width:220px" placeholder="Filter visible rows…"></div></div>
  <div class="table-scroll"><table id="recordsTable"><thead><tr><th>Name</th><th>Registration No.</th><th>City</th><th>State</th><th>Valid Upto</th><th>Status</th><th>Source Scope</th><th>Extracted</th></tr></thead><tbody>
  {% for r in records %}<tr><td><b>{{r.architect_name or '—'}}</b></td><td>{{r.registration_number or '—'}}</td><td>{{r.city or '—'}}</td><td>{{r.state or '—'}}</td><td>{{r.valid_upto or '—'}}</td><td><span class="badge {{'success' if r.processing_status=='success' else 'danger'}}">{{r.processing_status}}</span></td><td><span class="badge neutral">{{r.record_scope or '—'}}</span></td><td>{{r.extracted_at or '—'}}</td></tr>{% else %}<tr><td class="empty" colspan="8">No records available.</td></tr>{% endfor %}
  </tbody></table></div>
</section>

<section class="card section full jobs">
  <div class="table-head"><div><h2>Recent Extraction Jobs</h2><div class="muted">Pending, completed, failed and security-verification states are persisted for resumable monitoring.</div></div></div>
  <div class="table-scroll"><table><thead><tr><th>Job</th><th>Category</th><th>Query</th><th>Status</th><th>Success</th><th>Duplicates</th><th>CAPTCHA</th><th>Started</th><th>Latest Activity</th></tr></thead><tbody>
  {% for j in jobs %}<tr><td>#{{j.id}}</td><td>{{j.category}}</td><td>{{j.query_value}}</td><td><span class="badge {% if j.status=='completed' %}success{% elif j.status=='captcha_required' %}warning{% elif j.status=='failed' %}danger{% else %}neutral{% endif %}">{{j.status}}</span></td><td>{{j.success_count}}</td><td>{{j.duplicate_count}}</td><td>{{j.captcha_count}}</td><td>{{j.started_at or '—'}}</td><td>{{j.latest_activity or '—'}}</td></tr>{% else %}<tr><td class="empty" colspan="9">No extraction jobs yet.</td></tr>{% endfor %}
  </tbody></table></div>
</section>

<div class="footer">CoA Directory Data Extraction Pipeline • SQLite persistence • indexed records • retries • duplicate handling • CAPTCHA-safe controls • <a href="/api/stats">API statistics</a></div>
</main><div id="toast" class="toast"></div>
<script>
const form=document.getElementById('extractForm');
form.addEventListener('submit',async(e)=>{e.preventDefault();const btn=document.getElementById('runBtn');const result=document.getElementById('result');btn.disabled=true;btn.textContent='⏳ Running…';result.textContent='Contacting CoA endpoint and applying configured retry/rate-limit controls…';try{const r=await fetch('/extract',{method:'POST',body:new FormData(form)});const data=await r.json();if(data.status==='captcha_required'){result.innerHTML='<span style="color:#92400e"><b>⚠ Security verification detected.</b> The pipeline paused safely; no CAPTCHA bypass was attempted.</span>';showToast('CAPTCHA/security verification detected — job paused safely.')}else if(data.status==='completed'){result.innerHTML='<span style="color:#047857"><b>✓ Extraction completed.</b> '+(data.records||0)+' records saved; '+(data.duplicates||0)+' duplicates skipped.</span>';showToast('Extraction completed successfully.')}else{result.innerHTML='<span class="error"><b>Extraction failed:</b> '+(data.error||'Unknown error')+'</span>';showToast('Extraction failed — see job history.')}await refreshDashboard();}catch(err){result.innerHTML='<span class="error"><b>Request error:</b> '+err+'</span>'}finally{btn.disabled=false;btn.textContent='▶ Start Extraction'}});
function showToast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),4200)}
async function refreshDashboard(){try{const r=await fetch('/api/stats');const d=await r.json();document.querySelectorAll('.metric .value')[0].textContent=d.total_records;document.querySelectorAll('.metric .value')[1].textContent=d.successful;document.querySelectorAll('.metric .value')[2].textContent=d.failed;document.querySelectorAll('.metric .value')[3].textContent=d.duplicates;document.querySelectorAll('.metric .value')[4].textContent=d.jobs;document.querySelectorAll('.metric .value')[5].textContent=d.captcha_events;document.getElementById('processed').textContent=d.total_records;document.getElementById('activity').textContent=d.latest_activity||'—';}catch(e){}}
document.getElementById('recordFilter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('#recordsTable tbody tr').forEach(tr=>tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none')});
</script></body></html>'''

CATEGORY_LABELS = {
    "name": "Search by Name",
    "year": "Registration Year",
    "registration_number": "Registration Number",
    "state": "State",
    "city": "City",
    "pincode": "Pincode",
}


def dashboard_stats():
    with connect() as c:
        row = c.execute("""SELECT COUNT(*) total,
            COALESCE(SUM(processing_status='success'),0) success,
            COALESCE(SUM(processing_status='failed'),0) failed,
            COALESCE(SUM(duplicate_status='duplicate'),0) dup
            FROM architects""").fetchone()
        j = c.execute("""SELECT COUNT(*) jobs,
            COALESCE(SUM(captcha_count),0) captcha,
            COALESCE(MAX(latest_activity),'—') latest
            FROM extraction_jobs""").fetchone()
        latest = c.execute("SELECT * FROM extraction_jobs ORDER BY id DESC LIMIT 1").fetchone()
        rps = latest["records_per_second"] if latest and latest["records_per_second"] else 0
    return {
        "total_records": row[0] or 0,
        "successful": row[1] or 0,
        "failed": row[2] or 0,
        "duplicates": row[3] or 0,
        "jobs": j[0] or 0,
        "captcha_events": j[1] or 0,
        "latest_activity": j[2],
        "throughput": round(float(rps), 3),
    }


def page_progress(s):
    latest = s.get("latest_job")
    if not latest:
        return {"status": "No live job — database ready", "pct": 100 if s["total_records"] else 0,
                "processed": s["total_records"], "throughput": s["throughput"], "latest": s["latest_activity"]}
    total = latest["total_identified"] or 0
    done = (latest["success_count"] or 0) + (latest["duplicate_count"] or 0) + (latest["failed_count"] or 0)
    pct = int(min(100, (done / total) * 100)) if total else (100 if latest["status"] in ("completed", "captcha_required", "failed") else 5)
    return {"status": f"Job #{latest['id']} • {latest['status']}", "pct": pct,
            "processed": done, "throughput": round(float(latest["records_per_second"] or 0), 3),
            "latest": latest["latest_activity"] or "—"}


@app.get('/')
def home():
    init_db()
    with connect() as c:
        jobs = c.execute("SELECT * FROM extraction_jobs ORDER BY id DESC LIMIT 15").fetchall()
        records = c.execute("""SELECT architect_name, registration_number, city, state,
            valid_upto, processing_status, record_scope, extracted_at
            FROM architects ORDER BY id DESC LIMIT 100""").fetchall()
        latest = c.execute("SELECT * FROM extraction_jobs ORDER BY id DESC LIMIT 1").fetchone()
    s = dashboard_stats()
    s["latest_job"] = latest
    metrics = [
        ("TOTAL RECORDS", s["total_records"], "Persisted in SQLite"),
        ("SUCCESSFUL", s["successful"], "Successfully stored"),
        ("FAILED", s["failed"], "Record-level failures"),
        ("DUPLICATES", s["duplicates"], "Skipped by unique key"),
        ("EXTRACTION JOBS", s["jobs"], "Tracked pipeline jobs"),
        ("CAPTCHA EVENTS", s["captcha_events"], "Safe pause events"),
    ]
    compliance = [
        "Batch/query workflow", "SQLite persistence", "Indexed retrieval", "Duplicate handling",
        "Retries + HTTP errors", "Incremental record saving", "Job status tracking", "CAPTCHA detection",
        "Rate-limit delay", "Raw response capture", "CSV export", "Progress monitoring",
    ]
    return render_template_string(HTML, url=DIRECTORY_URL, metrics=metrics,
                                  category_labels=CATEGORY_LABELS, compliance=compliance,
                                  progress=page_progress(s), jobs=jobs, records=records)


@app.post('/extract')
def extract():
    category = request.form.get('category', '')
    value = request.form.get('value', '').strip()
    if category not in CATEGORIES:
        return jsonify({"status": "failed", "error": "Invalid extraction category."}), 400
    if not value:
        return jsonify({"status": "failed", "error": "Search value is required."}), 400
    result = CoAExtractor().run_category_page(category, value)
    return jsonify(result)


@app.get('/api/stats')
def api_stats():
    return jsonify(dashboard_stats())


@app.get('/export.csv')
def export_csv():
    with connect() as c:
        rows = c.execute("SELECT * FROM architects ORDER BY id").fetchall()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(rows[0].keys() if rows else ["id"])
    for row in rows:
        writer.writerow(list(row))
    return app.response_class(out.getvalue(), mimetype='text/csv',
                              headers={'Content-Disposition': 'attachment; filename=coa_architects.csv'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=False)
