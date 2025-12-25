#!/usr/bin/env python3
import csv
import html
import sys
from datetime import datetime, timezone
from pathlib import Path

def main(csv_path: str, out_path: str) -> None:
    csv_file = Path(csv_path)
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Read CSV
    with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        raise SystemExit("CSV is empty")

    headers = rows[0]
    data_rows = rows[1:]

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    def td(cell: str) -> str:
        return f"<td>{html.escape(cell)}</td>"

    thead = "<tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers) + "</tr>"
    tbody = "\n".join("<tr>" + "".join(td(c) for c in r) + "</tr>" for r in data_rows)

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
  <title>Sheet Table</title>
  <style>
    body {{
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: "IBM Plex Sans", sans-serif;
        font-optical-sizing: auto;
        font-weight: 400;
        font-style: normal;
        font-variation-settings: "wdth" 100;
        font-size: large;
        margin: 0;
        padding: 20px;
        height: 50vh;
        display: flex;
        flex-direction: column;
    }}
    .meta {{ margin: 0 0 12px; color: #555; font-size: 14px; }}
    input {{ width: min(900px, 100%); padding: 10px; font-size: 16px; margin: 8px 0 14px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ position: sticky; top: 0; background: #f6f6f6; text-align: left; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
  </style>
</head>
<body>
  <h1>Google Sheet (Searchable)</h1>
  <p class="meta">Last updated (UTC): {updated}</p>

  <input id="q" type="search" placeholder="Type to search…" autocomplete="off" />

  <table id="tbl">
    <thead>{thead}</thead>
    <tbody>{tbody}</tbody>
  </table>

<script>
  const q = document.getElementById('q');
  const tbody = document.querySelector('#tbl tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));

  q.addEventListener('input', () => {{
    const needle = q.value.trim().toLowerCase();
    for (const tr of rows) {{
      const hay = tr.innerText.toLowerCase();
      tr.style.display = hay.includes(needle) ? '' : 'none';
    }}
  }});
</script>
</body>
</html>
"""
    out_file.write_text(page, encoding="utf-8")
    print(f"Wrote {out_file} ({len(data_rows)} rows)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: generate_site.py input.csv output.html")
    main(sys.argv[1], sys.argv[2])
