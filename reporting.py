from datetime import datetime
from html import escape
from pathlib import Path
from time import monotonic

import pytest

from config.config import BASE_URL, IS_DEMO_SITE, LIVE_MODE


_test_results = {}
_started_at = None
_started_clock = None


def pytest_addoption(parser):
    parser.addoption(
        "--html-report",
        action="store",
        default="reports/test-report.html",
        help="Path for the self-contained HTML test report.",
    )


def pytest_sessionstart(session):
    global _started_at, _started_clock
    _test_results.clear()
    _started_at = datetime.now().astimezone()
    _started_clock = monotonic()


@pytest.fixture
def report_step(request):
    result = _test_results.setdefault(
        request.node.nodeid,
        {"phases": {}, "details": "", "duration": 0.0, "steps": []},
    )
    marker = request.node.get_closest_marker("case_id")
    if marker and marker.args:
        result["case_id"] = str(marker.args[0])

    def record_step(name, expected, actual, status="PASS"):
        result["steps"].append(
            {
                "name": str(name),
                "expected": str(expected),
                "actual": str(actual),
                "status": str(status).upper(),
            }
        )

    return record_step


def pytest_runtest_logreport(report):
    result = _test_results.setdefault(
        report.nodeid,
        {"phases": {}, "details": "", "duration": 0.0, "steps": []},
    )
    result["phases"][report.when] = report.outcome
    result["duration"] += report.duration
    if report.failed or report.skipped:
        result["details"] = report.longreprtext


def pytest_sessionfinish(session, exitstatus):
    config = session.config
    report_path = Path(config.getoption("--html-report"))
    if not report_path.is_absolute():
        report_path = Path(config.rootpath) / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)

    tests = []
    for nodeid, result in _test_results.items():
        phases = result["phases"]
        if "failed" in phases.values():
            status = "failed"
        elif "skipped" in phases.values():
            status = "skipped"
        elif phases.get("call") == "passed":
            status = "passed"
        else:
            status = "error"
        tests.append(
            {
                "name": nodeid,
                "case_id": result.get("case_id", ""),
                "status": status,
                "duration": result["duration"],
                "details": result["details"],
                "steps": result["steps"],
            }
        )

    elapsed = monotonic() - _started_clock if _started_clock is not None else 0
    counts = {
        status: sum(test["status"] == status for test in tests)
        for status in ("passed", "failed", "skipped", "error")
    }
    html = _render_report(
        tests=tests,
        counts=counts,
        elapsed=elapsed,
        generated_at=_started_at,
        exitstatus=exitstatus,
    )
    report_path.write_text(html, encoding="utf-8")

    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(f"HTML test report: {report_path.resolve()}")


def _render_report(tests, counts, elapsed, generated_at, exitstatus=0):
    total = sum(counts.values())
    if total:
        colors = {
            "passed": "#22c55e",
            "failed": "#ef4444",
            "skipped": "#f59e0b",
            "error": "#a855f7",
        }
        stops = []
        cursor = 0.0
        for status, amount in counts.items():
            if not amount:
                continue
            end = cursor + amount / total * 100
            stops.append(f"{colors[status]} {cursor:.2f}% {end:.2f}%")
            cursor = end
        chart = f"conic-gradient({', '.join(stops)})"
    else:
        chart = "conic-gradient(#dbe4f0 0 100%)"

    cards = "".join(
        f'<article class="metric {status}"><span>{status.title()}</span>'
        f'<strong>{counts[status]}</strong></article>'
        for status in ("passed", "failed", "skipped", "error")
    )
    legend = "".join(
        f'<div class="legend-item"><i class="{status}"></i>'
        f'<span>{status.title()}</span><strong>{counts[status]}</strong></div>'
        for status in ("passed", "failed", "skipped", "error")
    )
    rows = []
    for test in tests:
        status = test["status"]
        details = escape(test["details"])
        step_rows = "".join(
            f"<li><strong>{escape(step['name'])}</strong> "
            f'<span class="badge '
            f'{"passed" if step["status"] == "PASS" else "failed" if step["status"] == "FAIL" else "skipped"}">'
            f"{escape(step['status'])}</span>"
            f"<br><strong>Expected:</strong> {escape(step['expected'])}"
            f"<br><strong>Actual:</strong> {escape(step['actual'])}</li>"
            for step in test["steps"]
        )
        detail_content = ""
        if step_rows:
            detail_content += f"<ol>{step_rows}</ol>"
        if details:
            detail_content += f"<pre>{details}</pre>"
        detail_cell = (
            f"<details><summary>Steps and details</summary>{detail_content}</details>"
            if detail_content
            else '<span class="muted">No issues reported</span>'
        )
        test_name = (
            f"<code>{escape(test['case_id'])}</code><br>"
            f'<span class="muted">{escape(test["name"])}</span>'
            if test["case_id"]
            else f"<code>{escape(test['name'])}</code>"
        )
        rows.append(
            f"<tr><td>{test_name}</td>"
            f'<td><span class="badge {status}">{status.upper()}</span></td>'
            f"<td>{test['duration']:.2f}s</td><td>{detail_cell}</td></tr>"
        )

    mode = "Live-safe (checkout disabled)" if LIVE_MODE else (
        "Demo checkout" if IS_DEMO_SITE else "External target (checkout disabled)"
    )
    generated = generated_at.strftime("%Y-%m-%d %H:%M:%S %Z") if generated_at else "Unknown"
    if exitstatus not in (0, 5) or counts["failed"] or counts["error"]:
        result_message = "Failures detected"
    elif not total:
        result_message = "No tests collected"
    else:
        result_message = "No test failures"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toolshop QA | Test Report</title>
<style>
:root{{--ink:#172033;--muted:#65738b;--line:#e4eaf2;--surface:#fff;--bg:#f3f6fb;--blue:#4169e1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",Arial,sans-serif}}
.shell{{max-width:1120px;margin:0 auto;padding:36px 22px 56px}}
.hero{{padding:30px 32px;border-radius:22px;background:linear-gradient(120deg,#172554,#1d4ed8 62%,#38bdf8);color:white;box-shadow:0 18px 40px #173a742b}}
.eyebrow{{font-size:12px;letter-spacing:.16em;text-transform:uppercase;opacity:.76}}h1{{margin:8px 0;font-size:clamp(28px,5vw,42px);line-height:1.12}}
.hero p{{margin:0;color:#dbeafe}}.state{{display:inline-flex;margin-top:18px;padding:7px 12px;border-radius:999px;background:#ffffff20;font-weight:700;font-size:12px;letter-spacing:.06em}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}}
.metric,.panel{{background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 24px #17203308}}
.metric{{padding:17px 19px;display:flex;align-items:center;justify-content:space-between;color:var(--muted)}}
.metric strong{{font-size:30px;color:var(--ink)}}.metric.passed strong{{color:#16a34a}}.metric.failed strong{{color:#dc2626}}.metric.skipped strong{{color:#d97706}}.metric.error strong{{color:#9333ea}}
.overview{{display:grid;grid-template-columns:300px 1fr;gap:18px;margin-bottom:20px}}
.panel{{padding:22px}}h2{{margin:0 0 18px;font-size:18px}}.chart-wrap{{display:grid;place-items:center;min-height:230px}}
.donut{{width:190px;height:190px;border-radius:50%;background:{chart};display:grid;place-items:center;position:relative}}
.donut:before{{content:"";position:absolute;inset:23px;border-radius:50%;background:white}}
.donut-center{{z-index:1;text-align:center}}.donut-center strong{{display:block;font-size:38px;line-height:1.1}}.donut-center span{{color:var(--muted);font-size:12px}}
.legend{{display:grid;gap:13px;align-content:center}}.legend-item{{display:grid;grid-template-columns:14px 1fr auto;gap:10px;align-items:center;color:var(--muted)}}
.legend-item i{{width:11px;height:11px;border-radius:4px;background:#dbe4f0}}.legend-item i.passed{{background:#22c55e}}.legend-item i.failed{{background:#ef4444}}.legend-item i.skipped{{background:#f59e0b}}.legend-item i.error{{background:#a855f7}}
.legend-item strong{{color:var(--ink)}}.meta{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
.meta div{{padding:13px 15px;background:#f8faff;border-radius:11px;min-width:0}}.meta span{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
.meta strong{{display:block;margin-top:3px;overflow-wrap:anywhere}}table{{width:100%;border-collapse:collapse}}th,td{{padding:13px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}code{{overflow-wrap:anywhere;color:#334155}}
.badge{{display:inline-block;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:800;letter-spacing:.04em}}
.badge.passed{{background:#dcfce7;color:#15803d}}.badge.failed{{background:#fee2e2;color:#b91c1c}}.badge.skipped{{background:#fef3c7;color:#b45309}}.badge.error{{background:#f3e8ff;color:#7e22ce}}
details summary{{cursor:pointer;color:var(--blue);font-weight:600}}pre{{max-width:520px;white-space:pre-wrap;overflow-wrap:anywhere;padding:12px;background:#f8fafc;border-radius:9px;color:#475569;font-size:12px}}
.muted{{color:var(--muted);font-size:13px}}footer{{padding:22px 4px;color:var(--muted);font-size:12px;text-align:center}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}.overview{{grid-template-columns:1fr}}.meta{{grid-template-columns:1fr}}.panel{{overflow-x:auto}}}}
</style>
</head>
<body><main class="shell">
<header class="hero"><div class="eyebrow">Quality assurance · browser automation</div>
<h1>Toolshop Test Report</h1><p>Clear results for the product, stock, cart and checkout journey.</p>
<span class="state">{escape(result_message.upper())}</span></header>
<section class="grid" aria-label="Test result counts">{cards}</section>
<section class="overview">
<article class="panel"><h2>Run summary</h2><div class="chart-wrap"><div class="donut" role="img" aria-label="{total} total tests">
<div class="donut-center"><strong>{total}</strong><span>total tests</span></div></div></div></article>
<article class="panel"><h2>Outcome distribution</h2><div class="legend">{legend}</div></article>
</section>
<section class="panel" style="margin-bottom:20px"><h2>Execution details</h2><div class="meta">
<div><span>Target</span><strong>{escape(BASE_URL)}</strong></div>
<div><span>Mode</span><strong>{escape(mode)}</strong></div>
<div><span>Generated</span><strong>{escape(generated)}</strong></div>
<div><span>Duration</span><strong>{elapsed:.2f}s</strong></div></div></section>
<section class="panel"><h2>Test cases</h2><table><thead><tr><th>Test</th><th>Result</th><th>Time</th><th>Details</th></tr></thead>
<tbody>{''.join(rows) if rows else '<tr><td colspan="4" class="muted">No tests were collected.</td></tr>'}</tbody></table></section>
<footer>Generated locally by the Toolshop QA pytest reporting plugin · No external assets or tracking.</footer>
</main></body></html>"""
