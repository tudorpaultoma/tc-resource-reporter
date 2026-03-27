"""
HTML Report Template — self-contained static dashboard.
All CSS and JS are inline. No external dependencies.
Uses Python string.Template for safe placeholder substitution.
"""

import html
from string import Template

# ---------------------------------------------------------------------------
# CSS + JS + HTML skeleton
# ---------------------------------------------------------------------------
_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title}</title>
<style>
:root {
  --bg: #0f172a; --surface: #1e293b; --border: #334155;
  --text: #e2e8f0; --text-muted: #94a3b8; --accent: #38bdf8;
  --green: #4ade80; --yellow: #facc15; --red: #f87171; --orange: #fb923c;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; padding: 0; }
a { color: var(--accent); text-decoration: none; }

/* Header */
.header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.5rem 2rem; }
.header h1 { font-size: 1.5rem; font-weight: 700; }
.header .meta { color: var(--text-muted); font-size: 0.85rem; margin-top: .25rem; }

/* Layout */
.container { max-width: 1400px; margin: 0 auto; padding: 1.5rem 2rem; }

/* Cards */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.25rem; }
.card .label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.card .value { font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }
.card .value.green { color: var(--green); }
.card .value.yellow { color: var(--yellow); }
.card .value.red { color: var(--red); }
.card .value.accent { color: var(--accent); }

/* Sections */
.section { margin-bottom: 2rem; }
.section h2 { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }
.section h3 { font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem; color: var(--accent); }

/* Tables */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th { background: var(--surface); position: sticky; top: 0; padding: 0.6rem 0.75rem; text-align: left;
           border-bottom: 2px solid var(--border); color: var(--text-muted); font-weight: 600; cursor: pointer;
           user-select: none; white-space: nowrap; }
thead th:hover { color: var(--accent); }
thead th .sort-arrow { margin-left: 4px; font-size: 0.7rem; }
tbody td { padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); white-space: nowrap; }
tbody tr:hover { background: rgba(56, 189, 248, 0.05); }

/* Badges */
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: rgba(74,222,128,0.15); color: var(--green); }
.badge-yellow { background: rgba(250,204,21,0.15); color: var(--yellow); }
.badge-red { background: rgba(248,113,113,0.15); color: var(--red); }
.badge-blue { background: rgba(56,189,248,0.15); color: var(--accent); }
.badge-orange { background: rgba(251,146,60,0.15); color: var(--orange); }

/* Distribution grid */
.dist-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
.dist-card { background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; }
.dist-card h3 { margin-top: 0; }
.bar-row { display: flex; align-items: center; margin-bottom: 0.35rem; font-size: 0.8rem; }
.bar-label { width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-muted); }
.bar-track { flex: 1; height: 8px; background: var(--border); border-radius: 4px; margin: 0 0.5rem; }
.bar-fill { height: 100%; border-radius: 4px; background: var(--accent); min-width: 2px; }
.bar-count { width: 40px; text-align: right; font-weight: 600; }

/* Filter/Search */
.toolbar { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; align-items: center; }
.search-input { background: var(--surface); border: 1px solid var(--border); border-radius: 0.5rem;
                padding: 0.5rem 0.75rem; color: var(--text); font-size: 0.85rem; width: 260px; }
.search-input::placeholder { color: var(--text-muted); }
.search-input:focus { outline: none; border-color: var(--accent); }
select.search-input { appearance: auto; cursor: pointer; }

/* Tabs */
.tabs { display: flex; gap: 0; margin-bottom: 1rem; border-bottom: 2px solid var(--border); }
.tab { padding: 0.6rem 1.25rem; cursor: pointer; color: var(--text-muted); font-size: 0.9rem; font-weight: 500;
       border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color 0.15s, border-color 0.15s; }
.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* Footer */
.footer { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 2rem; }
</style>
</head>
<body>

<div class="header">
  <h1>${title}</h1>
  <div class="meta">Last updated: ${report_time} &nbsp;|&nbsp; Scanned ${regions_scanned} regions in ${elapsed}s &nbsp;|&nbsp; Reporter v${version}</div>
</div>

<div class="container">

  <!-- Summary Cards -->
  <div class="cards">
    <div class="card"><div class="label">Total Resources</div><div class="value accent">${total}</div></div>
    <div class="card"><div class="label">Owners</div><div class="value accent">${owner_count}</div></div>
    <div class="card"><div class="label">Expiring Soon</div><div class="value yellow">${expiring_soon_count}</div></div>
    <div class="card"><div class="label">Already Expired</div><div class="value red">${expired_count}</div></div>
    <div class="card"><div class="label">Incomplete Tags</div><div class="value orange">${incomplete_count}</div></div>
    <div class="card"><div class="label">Auto-Managed CVMs</div><div class="value green">${auto_managed_count}</div></div>
    <div class="card"><div class="label">No-Delete Missing Project</div><div class="value red">${no_delete_no_project_count}</div></div>
  </div>

  <!-- Tabs -->
  <div class="tabs" id="mainTabs">
    <div class="tab active" data-tab="all">All Resources</div>
    <div class="tab" data-tab="owners">By Owner</div>
    <div class="tab" data-tab="byproject">By Project</div>
    <div class="tab" data-tab="expiring">Expiring Soon</div>
    <div class="tab" data-tab="expired">Already Expired</div>
    <div class="tab" data-tab="incomplete">Incomplete Tags</div>
    <div class="tab" data-tab="nodelete">No-Delete Missing Project</div>
    <div class="tab" data-tab="distribution">Distribution</div>
  </div>

  <!-- All Resources -->
  <div class="tab-panel active" id="panel-all">
    <div class="toolbar">
      <input class="search-input" id="searchAll" placeholder="Search by ID, name, owner, region..." />
      <select class="search-input" id="filterRegion" style="width:200px">
        <option value="">All Regions</option>
        ${region_options}
      </select>
      <select class="search-input" id="filterOwner" style="width:200px">
        <option value="">All Owners</option>
        ${owner_options}
      </select>
    </div>
    <div class="table-wrap">
      <table id="tableAll">
        <thead><tr>
          <th data-col="0">Service <span class="sort-arrow"></span></th>
          <th data-col="1">Resource ID <span class="sort-arrow"></span></th>
          <th data-col="2">Name <span class="sort-arrow"></span></th>
          <th data-col="3">Region <span class="sort-arrow"></span></th>
          <th data-col="4">State <span class="sort-arrow"></span></th>
          <th data-col="5">Owner <span class="sort-arrow"></span></th>
          <th data-col="6">Created <span class="sort-arrow"></span></th>
          <th data-col="7">TTL <span class="sort-arrow"></span></th>
          <th data-col="8">Days Left <span class="sort-arrow"></span></th>
          <th data-col="9">Can Delete <span class="sort-arrow"></span></th>
          <th data-col="10">Project <span class="sort-arrow"></span></th>
        </tr></thead>
        <tbody>${all_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- By Owner -->
  <div class="tab-panel" id="panel-owners">
    ${owners_section}
  </div>

  <!-- By Project -->
  <div class="tab-panel" id="panel-byproject">
    ${by_project_section}
  </div>

  <!-- Expiring Soon -->
  <div class="tab-panel" id="panel-expiring">
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Service</th><th>Resource ID</th><th>Name</th><th>Region</th>
          <th>Owner</th><th>Days Left</th><th>Expires At</th><th>Can Delete</th>
        </tr></thead>
        <tbody>${expiring_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Already Expired -->
  <div class="tab-panel" id="panel-expired">
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Service</th><th>Resource ID</th><th>Name</th><th>Region</th>
          <th>Owner</th><th>Days Overdue</th><th>Can Delete</th><th>Project</th>
        </tr></thead>
        <tbody>${expired_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Incomplete Tags -->
  <div class="tab-panel" id="panel-incomplete">
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Service</th><th>Resource ID</th><th>Name</th><th>Region</th>
          <th>Owner</th><th>Created</th><th>Missing</th>
        </tr></thead>
        <tbody>${incomplete_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- No-Delete Missing Project -->
  <div class="tab-panel" id="panel-nodelete">
    <p style="color:var(--text-muted);margin-bottom:1rem;">Resources with <code>TaggerCanDelete=NO</code> but no <code>TaggerProject</code> — these will be deleted by the cleaner because project justification is missing.</p>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Service</th><th>Resource ID</th><th>Name</th><th>Region</th>
          <th>Owner</th><th>Created</th><th>TTL</th><th>Days Left</th><th>Project</th>
        </tr></thead>
        <tbody>${no_delete_no_project_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Distribution -->
  <div class="tab-panel" id="panel-distribution">
    <div class="dist-grid">
      ${distribution_cards}
    </div>
  </div>

</div>

<div class="footer">
  TC Resource Reporter v${version} &mdash; generated ${report_time}
</div>

<script>
/* Tabs */
document.querySelectorAll('#mainTabs .tab').forEach(function(tab){
  tab.addEventListener('click',function(){
    document.querySelectorAll('#mainTabs .tab').forEach(function(t){t.classList.remove('active')});
    document.querySelectorAll('.tab-panel').forEach(function(p){p.classList.remove('active')});
    tab.classList.add('active');
    document.getElementById('panel-'+tab.dataset.tab).classList.add('active');
  });
});

/* Combined filter: search + region + owner */
var si=document.getElementById('searchAll');
var fr=document.getElementById('filterRegion');
var fo=document.getElementById('filterOwner');
function applyFilters(){
  var q=(si?si.value:'').toLowerCase();
  var rv=(fr?fr.value:'').toLowerCase();
  var ov=(fo?fo.value:'').toLowerCase();
  var rows=document.querySelectorAll('#tableAll tbody tr');
  rows.forEach(function(r){
    var cells=r.children;
    var regionVal=cells[3]?cells[3].textContent.trim().toLowerCase():'';
    var ownerVal=cells[5]?cells[5].textContent.trim().toLowerCase():'';
    var text=r.textContent.toLowerCase();
    var show=true;
    if(q && text.indexOf(q)<0) show=false;
    if(rv && regionVal!==rv) show=false;
    if(ov && ownerVal!==ov) show=false;
    r.style.display=show?'':'none';
  });
}
if(si) si.addEventListener('input',applyFilters);
if(fr) fr.addEventListener('change',applyFilters);
if(fo) fo.addEventListener('change',applyFilters);

/* Sort */
document.querySelectorAll('#tableAll thead th[data-col]').forEach(function(th){
  th.addEventListener('click',function(){
    var ci=parseInt(th.dataset.col),tb=document.querySelector('#tableAll tbody');
    var rows=Array.from(tb.querySelectorAll('tr'));
    var asc=th.dataset.asc!=='1'; th.dataset.asc=asc?'1':'0';
    rows.sort(function(a,b){
      var va=a.children[ci].textContent.trim(),vb=b.children[ci].textContent.trim();
      var na=parseFloat(va),nb=parseFloat(vb);
      if(!isNaN(na)&&!isNaN(nb))return asc?na-nb:nb-na;
      return asc?va.localeCompare(vb):vb.localeCompare(va);
    });
    rows.forEach(function(r){tb.appendChild(r);});
  });
});
</script>
</body>
</html>""")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _esc(val):
    """HTML-escape a value."""
    return html.escape(str(val)) if val else ""


def _badge(text, color="blue"):
    """Render a small badge."""
    if not text:
        return '<span class="badge badge-blue">—</span>'
    return f'<span class="badge badge-{color}">{_esc(text)}</span>'


def _normalize_state(state):
    """Normalize raw API state strings to unified display names and colors.

    Returns (display_label, badge_color).
    """
    s = str(state).upper().strip()

    # Green — healthy / operational
    if s in ("RUNNING", "ACTIVE", "BIND", "BINDBOUND", "NORMAL"):
        return "Active", "green"
    if s == "ATTACHED":
        return "Attached", "green"

    # Yellow — idle but not problematic
    if s in ("AVAILABLE", "UNATTACHED"):
        return "Unattached", "yellow"

    # Red — stopped / down / error
    if s in ("STOPPED", "SHUTDOWN", "STOPPING"):
        return "Stopped", "red"
    if s in ("UNBIND", "DETACHED"):
        return "Detached", "red"
    if s in ("TERMINATED", "DELETED", "ERROR", "FAILED"):
        return s.capitalize(), "red"
    if s == "CREATING":
        return "Creating", "blue"

    # Fallback
    return state, "blue"


def _state_badge(state):
    """Color-code resource state with normalized labels."""
    if not state:
        return _badge("—", "blue")
    label, color = _normalize_state(state)
    return _badge(label, color)


def _days_left_badge(r):
    """Render days-left with color."""
    dl = r.get("_days_left")
    if dl is None:
        return "—"
    if dl < 0:
        return f'<span class="badge badge-red">{dl}d (overdue)</span>'
    if dl <= 3:
        return f'<span class="badge badge-yellow">{dl}d</span>'
    return f'<span class="badge badge-green">{dl}d</span>'


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------
def _all_row(r):
    return (
        f"<tr>"
        f"<td>{_badge(r.get('service',''))}</td>"
        f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
        f"<td>{_esc(r.get('resource_name',''))}</td>"
        f"<td>{_esc(r.get('region',''))}</td>"
        f"<td>{_state_badge(r.get('state',''))}</td>"
        f"<td>{_esc(r.get('TaggerOwner',''))}</td>"
        f"<td>{_esc(r.get('TaggerCreated',''))}</td>"
        f"<td>{_esc(r.get('TaggerTTL',''))}</td>"
        f"<td>{_days_left_badge(r)}</td>"
        f"<td>{_esc(r.get('TaggerCanDelete',''))}</td>"
        f"<td>{_esc(r.get('TaggerProject',''))}</td>"
        f"</tr>"
    )


def _expiring_row(r):
    return (
        f"<tr>"
        f"<td>{_badge(r.get('service',''))}</td>"
        f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
        f"<td>{_esc(r.get('resource_name',''))}</td>"
        f"<td>{_esc(r.get('region',''))}</td>"
        f"<td>{_esc(r.get('TaggerOwner',''))}</td>"
        f"<td>{_days_left_badge(r)}</td>"
        f"<td>{_esc(r.get('_expires_at',''))}</td>"
        f"<td>{_esc(r.get('TaggerCanDelete',''))}</td>"
        f"</tr>"
    )


def _expired_row(r):
    overdue = abs(r.get("_days_left", 0))
    return (
        f"<tr>"
        f"<td>{_badge(r.get('service',''))}</td>"
        f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
        f"<td>{_esc(r.get('resource_name',''))}</td>"
        f"<td>{_esc(r.get('region',''))}</td>"
        f"<td>{_esc(r.get('TaggerOwner',''))}</td>"
        f"<td><span class='badge badge-red'>{overdue}d overdue</span></td>"
        f"<td>{_esc(r.get('TaggerCanDelete',''))}</td>"
        f"<td>{_esc(r.get('TaggerProject',''))}</td>"
        f"</tr>"
    )


def _incomplete_row(r):
    missing = []
    if not r.get("TaggerOwner"):
        missing.append("Owner")
    if not r.get("TaggerCreated"):
        missing.append("Created")
    if not r.get("TaggerTTL"):
        missing.append("TTL")
    return (
        f"<tr>"
        f"<td>{_badge(r.get('service',''))}</td>"
        f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
        f"<td>{_esc(r.get('resource_name',''))}</td>"
        f"<td>{_esc(r.get('region',''))}</td>"
        f"<td>{_esc(r.get('TaggerOwner','') or '—')}</td>"
        f"<td>{_esc(r.get('TaggerCreated','') or '—')}</td>"
        f"<td><span class='badge badge-orange'>{', '.join(missing)}</span></td>"
        f"</tr>"
    )


def _no_delete_no_project_row(r):
    project = r.get("TaggerProject", "")
    project_display = (
        f'<span class="badge badge-red">MISSING</span>'
        if not project or project.lower() == "n/a"
        else _esc(project)
    )
    return (
        f"<tr>"
        f"<td>{_badge(r.get('service',''))}</td>"
        f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
        f"<td>{_esc(r.get('resource_name',''))}</td>"
        f"<td>{_esc(r.get('region',''))}</td>"
        f"<td>{_esc(r.get('TaggerOwner',''))}</td>"
        f"<td>{_esc(r.get('TaggerCreated',''))}</td>"
        f"<td>{_esc(r.get('TaggerTTL',''))}</td>"
        f"<td>{_days_left_badge(r)}</td>"
        f"<td>{project_display}</td>"
        f"</tr>"
    )


# ---------------------------------------------------------------------------
# Distribution card builder
# ---------------------------------------------------------------------------
def _dist_card(title, data_dict, max_items=15):
    """Render a bar-chart card for a dict of {label: count}."""
    if not data_dict:
        return ""
    sorted_items = sorted(data_dict.items(), key=lambda x: -x[1])[:max_items]
    max_val = max(v for _, v in sorted_items) if sorted_items else 1
    rows = ""
    for label, count in sorted_items:
        pct = round(count / max_val * 100)
        rows += (
            f'<div class="bar-row">'
            f'<span class="bar-label" title="{_esc(label)}">{_esc(label)}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{pct}%"></span></span>'
            f'<span class="bar-count">{count}</span>'
            f'</div>'
        )
    return (
        f'<div class="dist-card">'
        f'<h3>{_esc(title)}</h3>'
        f'{rows}'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Owners section builder
# ---------------------------------------------------------------------------
def _owners_section(by_owner):
    """Build the 'By Owner' tab content."""
    if not by_owner:
        return "<p>No owner data.</p>"

    parts = []
    for owner in sorted(by_owner.keys()):
        res_list = by_owner[owner]
        parts.append(f'<h3>{_esc(owner)} ({len(res_list)} resources)</h3>')
        parts.append('<div class="table-wrap"><table>')
        parts.append(
            "<thead><tr><th>Service</th><th>Resource ID</th><th>Name</th>"
            "<th>Region</th><th>State</th><th>TTL</th><th>Days Left</th>"
            "<th>Can Delete</th><th>Project</th></tr></thead><tbody>"
        )
        for r in res_list:
            parts.append(
                f"<tr>"
                f"<td>{_badge(r.get('service',''))}</td>"
                f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
                f"<td>{_esc(r.get('resource_name',''))}</td>"
                f"<td>{_esc(r.get('region',''))}</td>"
                f"<td>{_state_badge(r.get('state',''))}</td>"
                f"<td>{_esc(r.get('TaggerTTL',''))}</td>"
                f"<td>{_days_left_badge(r)}</td>"
                f"<td>{_esc(r.get('TaggerCanDelete',''))}</td>"
                f"<td>{_esc(r.get('TaggerProject',''))}</td>"
                f"</tr>"
            )
        parts.append("</tbody></table></div>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# By-project section builder
# ---------------------------------------------------------------------------
def _by_project_section(resources):
    """Build the 'By Project' tab — only resources with a real project tag."""
    by_proj = {}
    for r in resources:
        proj = r.get("TaggerProject", "")
        if proj and proj.lower() != "n/a":
            by_proj.setdefault(proj, []).append(r)

    if not by_proj:
        return "<p>No resources with a project tag.</p>"

    parts = []
    for proj in sorted(by_proj.keys()):
        res_list = by_proj[proj]
        parts.append(f'<h3>{_esc(proj)} ({len(res_list)} resources)</h3>')
        parts.append('<div class="table-wrap"><table>')
        parts.append(
            "<thead><tr><th>Service</th><th>Resource ID</th><th>Name</th>"
            "<th>Region</th><th>State</th><th>Owner</th><th>TTL</th>"
            "<th>Days Left</th><th>Can Delete</th></tr></thead><tbody>"
        )
        for r in res_list:
            parts.append(
                f"<tr>"
                f"<td>{_badge(r.get('service',''))}</td>"
                f"<td><code>{_esc(r.get('resource_id',''))}</code></td>"
                f"<td>{_esc(r.get('resource_name',''))}</td>"
                f"<td>{_esc(r.get('region',''))}</td>"
                f"<td>{_state_badge(r.get('state',''))}</td>"
                f"<td>{_esc(r.get('TaggerOwner',''))}</td>"
                f"<td>{_esc(r.get('TaggerTTL',''))}</td>"
                f"<td>{_days_left_badge(r)}</td>"
                f"<td>{_esc(r.get('TaggerCanDelete',''))}</td>"
                f"</tr>"
            )
        parts.append("</tbody></table></div>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_report(*, title, resources, stats, report_time, elapsed, regions_scanned, version):
    """Render the full HTML report and return it as a string."""
    all_rows = "\n".join(_all_row(r) for r in resources)
    expiring_rows = "\n".join(_expiring_row(r) for r in stats["expiring_soon"])
    expired_rows = "\n".join(_expired_row(r) for r in stats["already_expired"])
    incomplete_rows = "\n".join(_incomplete_row(r) for r in stats["incomplete_tags"])
    no_delete_no_project_rows = "\n".join(
        _no_delete_no_project_row(r) for r in stats["no_delete_no_project"]
    )
    owners_section = _owners_section(stats["by_owner"])
    by_project_section = _by_project_section(resources)

    # Build region dropdown options
    region_options = "\n".join(
        f'<option value="{_esc(reg)}">{_esc(reg)}</option>'
        for reg in sorted(stats["by_region"].keys())
    )

    # Build owner dropdown options
    owner_options = "\n".join(
        f'<option value="{_esc(owner)}">{_esc(owner)}</option>'
        for owner in sorted(stats["by_owner"].keys())
    )

    distribution_cards = "\n".join([
        _dist_card("By Service Type", stats["by_service"]),
        _dist_card("By Region", stats["by_region"]),
        _dist_card("By Project", stats["by_project"]),
        _dist_card("By Owner", {k: len(v) for k, v in stats["by_owner"].items()}),
    ])

    return _TEMPLATE.safe_substitute(
        title=_esc(title),
        report_time=_esc(report_time),
        regions_scanned=regions_scanned,
        elapsed=elapsed,
        version=_esc(version),
        total=stats["total"],
        owner_count=len(stats["by_owner"]),
        expiring_soon_count=len(stats["expiring_soon"]),
        expired_count=len(stats["already_expired"]),
        incomplete_count=len(stats["incomplete_tags"]),
        auto_managed_count=len(stats["auto_managed"]),
        no_delete_no_project_count=len(stats["no_delete_no_project"]),
        all_rows=all_rows,
        owners_section=owners_section,
        by_project_section=by_project_section,
        expiring_rows=expiring_rows,
        expired_rows=expired_rows,
        incomplete_rows=incomplete_rows,
        no_delete_no_project_rows=no_delete_no_project_rows,
        region_options=region_options,
        owner_options=owner_options,
        distribution_cards=distribution_cards,
    )
