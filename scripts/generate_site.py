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

    # Determine which columns to keep: skip columns whose header (row 1) is empty or whitespace
    keep_indices = [i for i, h in enumerate(headers) if h and h.strip() != ""]
    if not keep_indices:
        raise SystemExit("No non-empty header columns found in CSV")

    filtered_headers = [headers[i] for i in keep_indices]

    # Normalize rows to the kept columns, filling missing cells with empty string
    def row_for_indices(row):
        return [row[i] if i < len(row) else "" for i in keep_indices]

    filtered_data_rows = [row_for_indices(r) for r in data_rows]

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    def td(cell: str) -> str:
        return f"<td>{html.escape(cell)}</td>"

    thead = "<tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in filtered_headers) + "</tr>"
    tbody = "\n".join("<tr>" + "".join(td(c) for c in r) + "</tr>" for r in filtered_data_rows)

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="theme-color" content="#121212" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
  <title>Sheet Table</title>
  <style>
    :root {{
      /* Material-inspired dark theme (accessible contrast) */
      --background-color: #121212; /* Material dark background */
      --surface: #1E1E1E; /* elevated surface */
      --muted: #90A4AE; /* secondary text / muted */
      --text-color: #ECEFF1; /* primary text */
      --primary: #1E88E5; /* Material Blue 600 */
      --primary-foreground: #FFFFFF;
      --border: rgba(255,255,255,0.08);
      --focus-ring: rgba(30,136,229,0.22);
      --radius: 8px;
      --max-width: 1200px;
    }}

    html, body {{
      height: 100%;
      background-color: var(--background-color);
      color: var(--text-color);
      font-family: "Roboto", system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial;
      margin: 0;
      padding: 20px;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    .container {{
      max-width: var(--max-width);
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    h1 {{
      font-size: 1.6rem;
      margin: 0;
      font-weight: 500;
      color: var(--text-color);
    }}

    .meta {{
      margin: 0;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .controls {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    input[type="search"] {{
      width: min(900px, 100%);
      padding: 10px 12px;
      font-size: 1rem;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      color: var(--text-color);
      outline: none;
      transition: box-shadow 120ms ease, border-color 120ms ease;
      box-shadow: none;
    }}

    input[type="search"]::placeholder {{
      color: rgba(236,239,241,0.6);
    }}

    input[type="search"]:focus {{
      box-shadow: 0 0 0 6px var(--focus-ring);
      border-color: var(--primary);
    }}

    table {{
      border-collapse: collapse;
      width: 100%;
      background: transparent;
      margin-top: 8px;
      overflow: auto;
      border-radius: 6px;
    }}

    th, td {{
      border: 1px solid var(--border);
      padding: 10px 12px;
      vertical-align: top;
      text-align: left;
      font-size: 0.95rem;
    }}

    thead th {{
      position: sticky;
      top: 0;
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
      backdrop-filter: blur(4px);
      z-index: 2;
      font-weight: 500;
    }}

    tbody tr:nth-child(even) td {{
      background: rgba(255,255,255,0.02);
    }}

    tbody tr:hover td {{
      background: rgba(30,136,229,0.04);
    }}

    /* Make table cells wrap, preserving readability */
    td {{
      white-space: pre-wrap;
      word-break: break-word;
    }}

    /* Accessible focus for rows (keyboard navigation) */
    tr[tabindex="0"]:focus {{
      outline: none;
      box-shadow: 0 0 0 6px var(--focus-ring);
    }}

    .sr-only {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0,0,0,0);
      white-space: nowrap;
      border: 0;
    }}

    @media (prefers-reduced-motion: reduce) {{
      * {{
        transition: none !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="container" role="main">
    <h1>Google Sheet (Searchable)</h1>
    <p class="meta">Last updated (UTC): {updated}</p>

    <div class="controls">
      <label for="q" class="sr-only">Search table</label>
      <input id="q" aria-label="Search table" type="search" placeholder="Type to search…" autocomplete="off" />
    </div>

    <div style="overflow:auto;">
      <table id="tbl" role="table" aria-label="Sheet data">
        <thead>{thead}</thead>
        <tbody>{tbody}</tbody>
      </table>
    </div>
  </div>

<script>
  (function() {{
    const q = document.getElementById('q');
    const tbody = document.querySelector('#tbl tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Allow keyboard focusing of rows for accessibility
    rows.forEach(r => r.setAttribute('tabindex', '0'));

    q.addEventListener('input', () => {{
      const needle = q.value.trim().toLowerCase();
      for (const tr of rows) {{
        const hay = tr.innerText.toLowerCase();
        tr.style.display = hay.includes(needle) ? '' : 'none';
        tr.setAttribute('aria-hidden', hay.includes(needle) ? 'false' : 'true');
      }}
    }});
  }})();
</script>
</body>
</html>
"""
    out_file.write_text(page, encoding="utf-8")
    print(f"Wrote {out_file} ({len(filtered_data_rows)} rows, {len(filtered_headers)} columns)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: generate_site.py input.csv output.html")
    main(sys.argv[1], sys.argv[2])
