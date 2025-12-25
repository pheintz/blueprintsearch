#!/usr/bin/env python3
import csv
import html
import sys
from datetime import datetime, timezone
from pathlib import Path
import shutil

def main(csv_path: str, out_path: str) -> None:
    csv_file = Path(csv_path)
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Copy style.css next to generated HTML so the <link href="style.css"> works
    style_src = Path(__file__).parent / "style.css"
    style_dest = out_file.parent / "style.css"
    if style_src.exists():
        shutil.copy2(style_src, style_dest)
        print(f"Copied {style_src} -> {style_dest}")
    else:
        print(f"Warning: {style_src} not found; generated HTML will reference 'style.css' but file won't be copied.", file=sys.stderr)

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
  <link rel="stylesheet" href="style.css">
  <title>Sheet Table</title>
</head>
<body>
  <div class="container" role="main">
    <h1>Merchant Blueprint Data</h1>
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
