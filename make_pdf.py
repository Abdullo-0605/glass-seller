"""Convert FLOWCHART.md to PDF."""
import markdown
from pathlib import Path

md_text = Path("FLOWCHART.md").read_text(encoding="utf-8")
html_body = markdown.markdown(md_text, extensions=["fenced_code"])

html = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    "<style>"
    "body { font-family: Consolas, monospace; font-size: 11px; margin: 30px; }"
    "h1 { font-size: 20px; } h2 { font-size: 15px; margin-top: 24px; }"
    "pre { background: #f4f4f4; padding: 14px; border-radius: 6px; "
    "font-size: 9.5px; line-height: 1.35; white-space: pre; page-break-inside: avoid; }"
    "code { font-family: Consolas, monospace; }"
    "</style></head><body>"
    + html_body
    + "</body></html>"
)

Path("FLOWCHART.html").write_text(html, encoding="utf-8")
print("FLOWCHART.html created — opening in browser so you can Print > Save as PDF")

import webbrowser, os
webbrowser.open("file:///" + os.path.abspath("FLOWCHART.html").replace("\\", "/"))
