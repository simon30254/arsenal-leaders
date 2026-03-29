import requests, csv, io, os
from datetime import datetime

PITCH_TYPES = [
    ("FF", "四縫線快速球", "🔴"),
    ("SI", "伸卡球",       "🟠"),
    ("FC", "切球",         "🟡"),
    ("SL", "滑球",         "🟢"),
    ("SW", "橫掃球",         "🔵"),
    ("CU", "曲球",         "🟣"),
    ("CH", "變速球",       "⚪"),
    ("FS", "指叉球",       "🟤"),
]

YEAR = datetime.now().year
if datetime.now().month < 3:
    YEAR -= 1

def fetch_arsenal_data(pitch_type, year):
    url = (
        f"https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats"
        f"?type=pitcher&pitchType={pitch_type}&year={year}&team=&min=q&csv=true"
    )
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))

def get_name(r):
    return (
        r.get("last_name, first_name") or
        r.get("player_name") or
        r.get("name_display_first_last") or
        "—"
    )

def fmt(val, decimals=1, suffix=""):
    try:
        return f"{float(val):.{decimals}f}{suffix}"
    except:
        return "—"

def fmt_rv(val):
    try:
        v = float(val)
        color = "#22c55e" if v < 0 else "#ef4444" if v > 0 else "#94a3b8"
        return f'<span style="color:{color};font-weight:700">{v:+.1f}</span>'
    except:
        return "—"

def fmt_pct(val):
    try:
        v = float(val)
        v = v * 100 if v <= 1 else v
        return f"{v:.1f}%"
    except:
        return "—"

def build_table(rows, top_n=50):
    def sort_key(r):
        try:
            return float(r.get("run_value_per_100") or r.get("run_value") or 0)
        except:
            return 0

    rows_sorted = sorted(rows, key=sort_key)[:top_n]

    if not rows_sorted:
        return '<tr><td colspan="10" style="text-align:center;padding:2rem;color:#64748b">本球種本季無符合資格投手</td></tr>'

    html = ""
    for rank, r in enumerate(rows_sorted, 1):
        medal     = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else str(rank)
        hand      = r.get("p_throws", "")
        team      = r.get("team_name_alt") or r.get("team") or r.get("team_abbrev") or "—"
        pitch     = r.get("pitch_name") or r.get("pitch_type_name") or "—"
        run_val   = fmt_rv(r.get("run_value_per_100") or r.get("run_value"))
        whiff     = fmt_pct(r.get("whiff_percent"))
        k_pct     = fmt_pct(r.get("k_percent"))
        slg       = fmt(r.get("slg"), 3)
        ba        = fmt(r.get("ba"), 3)
        avg_speed = fmt(r.get("avg_speed") or r.get("velocity"), suffix=" mph")
        spin      = fmt(r.get("avg_spin") or r.get("spin_rate"), 0, " rpm")

        html += f"""<tr>
          <td class="rank">{medal}</td>
          <td class="player">{get_name(r)} <span class="hand">{hand}</span></td>
          <td class="team">{team}</td>
          <td class="pitch-tag">{pitch}</td>
          <td class="stat">{run_val}</td>
          <td class="stat">{whiff}</td>
          <td class="stat">{k_pct}</td>
          <td class="stat">{slg}</td>
          <td class="stat">{ba}</td>
          <td class="stat">{avg_speed}</td>
          <td class="stat">{spin}</td>
        </tr>"""
    return html

def build_html(all_data):
    tabs_html = ""
    panels_html = ""

    for i, (code, name, emoji) in enumerate(PITCH_TYPES):
        active = "active" if i == 0 else ""
        tabs_html += f'<button class="tab-btn {active}" onclick="showTab(\'{code}\')" id="btn-{code}">{emoji} {name} <span class="code">{code}</span></button>\n'

        rows_html = build_table(all_data.get(code, []))

        panels_html += f"""<div class="tab-panel {'active' if i == 0 else ''}" id="panel-{code}">
          <div class="table-wrap">
          <table>
            <thead><tr>
              <th>#</th>
              <th>投手</th>
              <th>球隊</th>
              <th>球種</th>
              <th title="Run Value：負數代表對投手越有利">RV/100</th>
              <th title="揮棒落空率">揮空率</th>
              <th title="三振率">K%</th>
              <th title="被長打率">SLG</th>
              <th title="被打擊率">被打擊率</th>
              <th title="平均球速">均速</th>
              <th title="平均旋轉數">旋轉數</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
          </div>
        </div>"""

    updated = datetime.now().strftime("%Y-%m-%d")

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
  }}
  h1 {{ font-size: 1.25rem; font-weight: 800; color: #f8fafc; margin-bottom: .2rem; }}
  .subtitle {{ font-size: .78rem; color: #475569; margin-bottom: .75rem; }}
  .legend {{
    font-size: .72rem; color: #64748b; margin-bottom: 1rem;
    background: #1e293b; border-radius: 6px; padding: .5rem .75rem;
    display: flex; flex-wrap: wrap; gap: .4rem 1.5rem;
  }}
  .good {{ color: #22c55e; }} .bad {{ color: #ef4444; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-bottom: 1rem; }}
  .tab-btn {{
    background: #1e293b; border: 1px solid #334155; color: #64748b;
    padding: .4rem .75rem; border-radius: 6px; cursor: pointer;
    font-size: .8rem; transition: all .15s;
  }}
  .tab-btn:hover {{ background: #334155; color: #cbd5e1; }}
  .tab-btn.active {{ background: #2563eb; border-color: #2563eb; color: #fff; font-weight: 700; }}
  .code {{ opacity: .45; font-size: .68rem; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .82rem; min-width: 700px; }}
  thead {{ background: #1e293b; }}
  th {{
    padding: .55rem .7rem; text-align: left; color: #475569;
    font-size: .7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .04em; border-bottom: 2px solid #334155;
    white-space: nowrap;
  }}
  th[title] {{ cursor: help; text-decoration: underline dotted #334155; }}
  td {{ padding: .5rem .7rem; border-bottom: 1px solid #1a2535; }}
  tr:hover td {{ background: #1e293b; }}
  .rank {{ font-weight: 700; width: 2.2rem; font-size: .9rem; }}
  .player {{ font-weight: 600; color: #f1f5f9; white-space: nowrap; }}
  .hand {{ font-size: .68rem; color: #475569; margin-left: .25rem; }}
  .team {{ font-size: .78rem; color: #94a3b8; white-space: nowrap; }}
  .pitch-tag {{
    font-size: .7rem; background: #0f172a; color: #7dd3fc;
    padding: .15rem .4rem; border-radius: 4px; white-space: nowrap;
  }}
  .stat {{ font-family: 'SF Mono', 'Fira Code', monospace; font-size: .82rem; }}
  .footer {{ margin-top: 1rem; font-size: .7rem; color: #334155; text-align: right; }}
  .footer a {{ color: #3b82f6; text-decoration: none; }}
</style>
</head>
<body>
<h1>⚾ MLB 武器球排行榜 {YEAR}</h1>
<p class="subtitle">各球種 Top 50｜依 Run Value 排序｜資料：Baseball Savant Statcast</p>
<div class="legend">
  <span>RV/100：<span class="good">負數 = 投手有利 ✓</span>　<span class="bad">正數 = 投手不利</span></span>
  <span>揮空率 = 揮棒落空率　K% = 三振率　SLG = 被長打率　被打擊率 = BA against</span>
</div>
<div class="tabs">{tabs_html}</div>
{panels_html}
<p class="footer">最後更新：{updated}｜<a href="https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats" target="_blank">原始資料 Baseball Savant</a></p>
<script>
function showTab(code) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + code).classList.add('active');
  document.getElementById('btn-' + code).classList.add('active');
}}
</script>
</body>
</html>"""

def main():
    all_data = {}
    for code, name, emoji in PITCH_TYPES:
        print(f"抓取 {emoji} {name} ({code})...")
        try:
            rows = fetch_arsenal_data(code, YEAR)
            all_data[code] = rows
            print(f"  → {{len(rows)}} 筆")
        except Exception as e:
            print(f"  → 失敗: {{e}}")
            all_data[code] = []

    html = build_html(all_data)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ 已生成 docs/index.html")

if __name__ == "__main__":
    main()
