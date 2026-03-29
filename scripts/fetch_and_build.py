import requests, csv, io, os
from datetime import datetime

YEAR = datetime.now().year
if datetime.now().month < 3:
    YEAR -= 1

PITCH_COLORS = {
    "FF": "#ef4444", "SI": "#f97316", "FC": "#eab308",
    "SL": "#22c55e", "SW": "#3b82f6", "CU": "#a855f7",
    "CH": "#94a3b8", "FS": "#78716c", "ST": "#06b6d4",
    "KC": "#8b5cf6", "KN": "#64748b", "CS": "#ec4899",
}

def fetch_all_data(year):
    url = (
        f"https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats"
        f"?type=pitcher&pitchType=&year={year}&team=&min=10&csv=true"
    )
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows

def get_name(r):
    return (
        r.get("last_name, first_name") or
        r.get("player_name") or "—"
    )

def fmt(val, decimals=3, suffix=""):
    try:
        return f"{float(val):.{decimals}f}{suffix}"
    except:
        return "—"

def fmt1(val, suffix=""):
    try:
        return f"{float(val):.1f}{suffix}"
    except:
        return "—"

def fmt_rv(val):
    try:
        v = float(val)
        intensity = min(abs(v) / 30, 1.0)
        if v < 0:
            r_val = int(34 + (239-34) * intensity)
            g_val = int(197 + (68-197) * intensity)
            b_val = int(94 + (68-94) * intensity)
        else:
            r_val = int(239 * intensity + 30 * (1-intensity))
            g_val = int(68 * intensity + 30 * (1-intensity))
            b_val = int(68 * intensity + 30 * (1-intensity))
        bg = f"rgb({r_val},{g_val},{b_val})"
        text_color = "#fff" if intensity > 0.3 else "#e2e8f0"
        return f'<span class="rv-badge" style="background:{bg};color:{text_color}">{v:+.0f}</span>'
    except:
        return "—"

def pitch_tag(pitch_type, pitch_name):
    color = PITCH_COLORS.get(pitch_type, "#64748b")
    short = pitch_type or "?"
    name = pitch_name or pitch_type or "—"
    return f'<span class="pt-dot" style="background:{color}" title="{name}">{short}</span> {name}'

def build_html(rows):
    # 依 run_value 降冪排序（Run Value 越大代表這球越強，對投手有利）
    def sort_key(r):
        try:
            return float(r.get("run_value") or 0)
        except:
            return 0

    rows_sorted = sorted(rows, key=sort_key, reverse=True)[:50]

    rows_html = ""
    for rank, r in enumerate(rows_sorted, 1):
        medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else str(rank)
        name = get_name(r)
        team = r.get("team_name_alt", "—")
        pt   = r.get("pitch_type", "")
        pn   = r.get("pitch_name", "")
        hand = r.get("p_throws", "")

        rv100   = fmt1(r.get("run_value_per_100"))
        rv      = fmt_rv(r.get("run_value"))
        pitches = r.get("pitches", "—")
        usage   = fmt1(r.get("pitch_usage"), "%")
        pa      = r.get("pa", "—")
        ba      = fmt(r.get("ba"))
        slg     = fmt(r.get("slg"))
        woba    = fmt(r.get("woba"))
        whiff   = fmt1(r.get("whiff_percent"), "%")
        kpct    = fmt1(r.get("k_percent"), "%")
        putaway = fmt1(r.get("put_away"), "%")
        xba     = fmt(r.get("est_ba"))
        xslg    = fmt(r.get("est_slg"))
        xwoba   = fmt(r.get("est_woba"))
        hardhit = fmt1(r.get("hard_hit_percent"), "%")

        rows_html += f"""<tr>
          <td class="rank">{medal}</td>
          <td class="player">{name} <span class="hand">{hand}</span></td>
          <td class="team">{team}</td>
          <td class="pitch-cell">{pitch_tag(pt, pn)}</td>
          <td class="stat">{rv100}</td>
          <td class="stat rv-cell">{rv}</td>
          <td class="stat">{pitches}</td>
          <td class="stat">{usage}</td>
          <td class="stat">{pa}</td>
          <td class="stat">{ba}</td>
          <td class="stat">{slg}</td>
          <td class="stat">{woba}</td>
          <td class="stat hi">{whiff}</td>
          <td class="stat hi">{kpct}</td>
          <td class="stat">{putaway}</td>
          <td class="stat">{xba}</td>
          <td class="stat">{xslg}</td>
          <td class="stat">{xwoba}</td>
          <td class="stat">{hardhit}</td>
        </tr>"""

    updated = datetime.now().strftime("%Y-%m-%d")
    total = len(rows_sorted)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MLB 武器球排行榜 {YEAR}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a; color: #e2e8f0; padding: 1rem;
    font-size: 13px;
  }}
  h1 {{ font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: .2rem; }}
  .subtitle {{ font-size: .75rem; color: #475569; margin-bottom: .75rem; }}

  .filters {{
    display: flex; flex-wrap: wrap; gap: .5rem;
    margin-bottom: .75rem; align-items: center;
  }}
  .filter-label {{ font-size: .75rem; color: #64748b; }}
  select {{
    background: #1e293b; border: 1px solid #334155; color: #cbd5e1;
    padding: .3rem .5rem; border-radius: 5px; font-size: .75rem; cursor: pointer;
  }}
  input[type=text] {{
    background: #1e293b; border: 1px solid #334155; color: #cbd5e1;
    padding: .3rem .6rem; border-radius: 5px; font-size: .75rem; width: 140px;
  }}
  input::placeholder {{ color: #475569; }}

  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; min-width: 900px; }}

  .group-header th {{
    background: #0f172a; color: #475569; font-size: .65rem;
    text-align: center; padding: .2rem; border-bottom: none;
    text-transform: uppercase; letter-spacing: .05em;
  }}
  thead tr:last-child th {{
    background: #1e293b; color: #64748b; font-size: .68rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
    padding: .5rem .5rem; border-bottom: 2px solid #334155;
    white-space: nowrap; cursor: pointer; user-select: none;
  }}
  thead tr:last-child th:hover {{ color: #cbd5e1; background: #253347; }}
  thead tr:last-child th.sorted {{ color: #60a5fa; }}

  td {{ padding: .4rem .5rem; border-bottom: 1px solid #1a2535; white-space: nowrap; }}
  tr:hover td {{ background: #1e293b88; }}

  .rank {{ width: 2rem; font-weight: 700; font-size: .85rem; text-align: center; }}
  .player {{ font-weight: 600; color: #f1f5f9; min-width: 130px; }}
  .hand {{ font-size: .65rem; color: #475569; }}
  .team {{ color: #94a3b8; font-size: .78rem; }}
  .pitch-cell {{ min-width: 130px; }}
  .pt-dot {{
    display: inline-block; padding: .1rem .35rem;
    border-radius: 4px; font-size: .65rem; font-weight: 700;
    color: #fff; margin-right: .3rem; vertical-align: middle;
  }}
  .stat {{ font-family: 'SF Mono', 'Fira Code', monospace; font-size: .78rem; text-align: right; }}
  .hi {{ color: #7dd3fc; }}
  .rv-cell {{ text-align: center; }}
  .rv-badge {{
    display: inline-block; padding: .15rem .5rem;
    border-radius: 5px; font-weight: 700; font-size: .8rem;
    min-width: 2.5rem; text-align: center;
  }}

  .legend {{
    font-size: .7rem; color: #475569; margin-top: .75rem;
    display: flex; flex-wrap: wrap; gap: .3rem 1rem;
  }}
  .footer {{ margin-top: .75rem; font-size: .68rem; color: #334155; text-align: right; }}
  .footer a {{ color: #3b82f6; text-decoration: none; }}
  .count {{ font-size: .75rem; color: #64748b; margin-bottom: .5rem; }}
</style>
</head>
<body>
<h1>⚾ MLB 武器球排行榜 {YEAR}</h1>
<p class="subtitle">所有球種混合排行｜依 Run Value 排序｜資料：Baseball Savant Statcast</p>

<div class="filters">
  <span class="filter-label">搜尋：</span>
  <input type="text" id="search" placeholder="投手名稱...">
  <span class="filter-label">球種：</span>
  <select id="pitchFilter" onchange="applyFilters()">
    <option value="">全部</option>
    <option value="FF">四縫線 FF</option>
    <option value="SI">伸卡球 SI</option>
    <option value="FC">切球 FC</option>
    <option value="SL">滑球 SL</option>
    <option value="SW">掃球 SW</option>
    <option value="ST">掃球 ST</option>
    <option value="CU">曲球 CU</option>
    <option value="CH">變速球 CH</option>
    <option value="FS">指叉球 FS</option>
  </select>
  <span class="filter-label">手性：</span>
  <select id="handFilter" onchange="applyFilters()">
    <option value="">全部</option>
    <option value="R">右投 R</option>
    <option value="L">左投 L</option>
  </select>
</div>

<p class="count" id="count">共 {total} 筆</p>

<div class="table-wrap">
<table id="mainTable">
  <thead>
    <tr class="group-header">
      <th colspan="4"></th>
      <th colspan="2">Usage</th>
      <th colspan="3">Standard</th>
      <th colspan="3">Standard</th>
      <th colspan="3">Outcome</th>
      <th colspan="4">Statcast</th>
    </tr>
    <tr>
      <th onclick="sortTable(0)">#</th>
      <th onclick="sortTable(1)">Player</th>
      <th onclick="sortTable(2)">Team</th>
      <th onclick="sortTable(3)">Pitch</th>
      <th onclick="sortTable(4)">RV/100</th>
      <th onclick="sortTable(5)" class="sorted">Run Value ↓</th>
      <th onclick="sortTable(6)">Pitches</th>
      <th onclick="sortTable(7)">%</th>
      <th onclick="sortTable(8)">PA</th>
      <th onclick="sortTable(9)">BA</th>
      <th onclick="sortTable(10)">SLG</th>
      <th onclick="sortTable(11)">wOBA</th>
      <th onclick="sortTable(12)">Whiff%</th>
      <th onclick="sortTable(13)">K%</th>
      <th onclick="sortTable(14)">Put Away%</th>
      <th onclick="sortTable(15)">xBA</th>
      <th onclick="sortTable(16)">xSLG</th>
      <th onclick="sortTable(17)">xwOBA</th>
      <th onclick="sortTable(18)">Hard Hit%</th>
    </tr>
  </thead>
  <tbody id="tableBody">
{rows_html}
  </tbody>
</table>
</div>

<div class="legend">
  <span>Run Value：<strong style="color:#22c55e">負數 = 投手有利</strong>　<strong style="color:#ef4444">正數 = 投手不利</strong></span>
  <span>Whiff% = 揮空率　K% = 三振率　Put Away% = 致勝球率</span>
</div>
<p class="footer">最後更新：{updated}｜<a href="https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats" target="_blank">原始資料 Baseball Savant</a></p>

<script>
let sortCol = 5;
let sortAsc = false;
const tbody = document.getElementById('tableBody');
const allRows = Array.from(tbody.querySelectorAll('tr'));

document.getElementById('search').addEventListener('input', applyFilters);

function applyFilters() {{
  const search = document.getElementById('search').value.toLowerCase();
  const pitch  = document.getElementById('pitchFilter').value;
  const hand   = document.getElementById('handFilter').value;
  let count = 0;
  allRows.forEach(row => {{
    const text = row.textContent.toLowerCase();
    const pitchCell = row.cells[3] ? row.cells[3].textContent : '';
    const handText  = row.cells[1] ? row.cells[1].textContent : '';
    const matchSearch = !search || text.includes(search);
    const matchPitch  = !pitch  || pitchCell.includes(pitch);
    const matchHand   = !hand   || handText.includes(hand);
    const show = matchSearch && matchPitch && matchHand;
    row.style.display = show ? '' : 'none';
    if (show) count++;
  }});
  document.getElementById('count').textContent = '共 ' + count + ' 筆';
}}

function sortTable(col) {{
  const ths = document.querySelectorAll('thead tr:last-child th');
  ths.forEach(th => th.classList.remove('sorted'));
  ths[col].classList.add('sorted');
  if (sortCol === col) {{ sortAsc = !sortAsc; }}
  else {{ sortCol = col; sortAsc = false; }}
  const sorted = allRows.slice().sort((a, b) => {{
    const av = a.cells[col] ? a.cells[col].textContent.replace(/[^0-9.\-+]/g, '') : '';
    const bv = b.cells[col] ? b.cells[col].textContent.replace(/[^0-9.\-+]/g, '') : '';
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return sortAsc ? an - bn : bn - an;
    return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  sorted.forEach(row => tbody.appendChild(row));
}}
</script>
</body>
</html>"""

def main():
    print(f"抓取 {YEAR} 年所有球種資料...")
    try:
        rows = fetch_all_data(YEAR)
        print(f"  → {len(rows)} 筆")
    except Exception as e:
        print(f"  → 失敗: {e}")
        rows = []

    html = build_html(rows)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ 已生成 docs/index.html")

if __name__ == "__main__":
    main()
