#!/usr/bin/env python3
"""Build a one-page resume HTML file from a structured JSON payload.

Ported from Karan's preferred Codex `tailor-resume-html` workflow.
Usage:
    python3 scripts/build_resume_html.py input.json output.html
"""

import html
import json
import sys
from pathlib import Path


def esc(value):
    return html.escape(str(value), quote=True)


def section(title, body):
    return f"<section>\n<h2>{esc(title)}</h2>\n{body}\n</section>"


def build(data):
    contact = "<br>\n".join(esc(item) for item in data.get("contact", []))
    skills = "\n".join(
        f'<div class="skill"><strong>{esc(s["label"])}:</strong> {esc(s["text"])}</div>'
        for s in data.get("skills", [])
    )
    roles = []
    for role in data.get("roles", []):
        bullets = "\n".join(f"<li>{esc(b)}</li>" for b in role.get("bullets", []))
        company = role.get("company", "")
        location = role.get("location")
        company_line = f"{company} | {location}" if location else company
        roles.append(
            f"""
<article class="role">
  <div class="role-head">
    <div class="company">{esc(company_line)}</div>
    <div class="date">{esc(role.get("dates", ""))}</div>
  </div>
  <div class="title">{esc(role.get("title", ""))}</div>
  <ul>{bullets}</ul>
</article>"""
        )
    education = data.get("education", {})
    education_body = f"""
<div class="education">
  <div>
    <div class="school">{esc(education.get("school", ""))} | {esc(education.get("location", ""))}</div>
    <div class="degree">{esc(education.get("degree", ""))}</div>
  </div>
  <div class="date">{esc(education.get("date", ""))}</div>
</div>"""
    interests = data.get("interests")
    interests_section = ""
    if interests:
        interests_section = section("Interests", f'<div class="interests">{esc(interests)}</div>')

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(data.get("name", "Tailored Resume"))}</title>
  <style>
    @page {{ size: Letter; margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f1eee8; color: #151515; font-family: Arial, Helvetica, sans-serif; letter-spacing: 0; }}
    .page {{ width: 8.5in; min-height: 11in; margin: 0 auto; background: #fff; padding: 0.35in 0.42in 0.3in; overflow: hidden; }}
    .accent {{ height: 0.055in; background: #b65a3a; margin-bottom: 0.14in; }}
    header {{ display: grid; grid-template-columns: 1fr auto; gap: 0.2in; align-items: start; padding-bottom: 0.105in; border-bottom: 1px solid #cec8bf; }}
    h1 {{ margin: 0; font-size: 36px; line-height: 0.95; font-weight: 800; text-transform: uppercase; }}
    .target {{ margin-top: 0.055in; font-size: 12.2px; line-height: 1.18; font-weight: 800; text-transform: uppercase; color: #3e3e3e; }}
    .contact {{ padding-top: 0.01in; text-align: right; font-size: 10.8px; line-height: 1.42; color: #333; white-space: nowrap; }}
    .summary {{ margin-top: 0.105in; font-size: 10.65px; line-height: 1.32; }}
    section {{ margin-top: 0.105in; }}
    h2 {{ margin: 0 0 0.052in; padding-bottom: 0.034in; border-bottom: 1px solid #d8d2ca; color: #a44b2f; font-size: 11.6px; line-height: 1; font-weight: 800; text-transform: uppercase; }}
    .skills {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.06in 0.19in; }}
    .skill {{ font-size: 9.7px; line-height: 1.25; }}
    .skill strong {{ font-weight: 800; }}
    .role {{ margin-top: 0.08in; }}
    .role-head {{ display: grid; grid-template-columns: 1fr auto; gap: 0.14in; align-items: baseline; margin-bottom: 0.015in; }}
    .company {{ font-size: 11.9px; font-weight: 800; line-height: 1.12; }}
    .date {{ font-size: 9.9px; font-weight: 800; line-height: 1.12; color: #4a4a4a; white-space: nowrap; }}
    .title {{ margin-bottom: 0.032in; font-size: 10.4px; line-height: 1.12; font-weight: 800; color: #333; }}
    ul {{ margin: 0; padding-left: 0.15in; }}
    li {{ margin: 0 0 0.033in; padding-left: 0.01in; font-size: 9.7px; line-height: 1.2; }}
    .education {{ display: grid; grid-template-columns: 1fr auto; gap: 0.15in; font-size: 10.2px; line-height: 1.25; }}
    .school {{ font-weight: 800; }}
    .degree, .interests {{ color: #333; }}
    .interests {{ font-size: 9.4px; line-height: 1.2; }}
    @media print {{ body {{ background: #fff; }} .page {{ margin: 0; }} }}
  </style>
</head>
<body>
  <main class="page">
    <div class="accent"></div>
    <header>
      <div>
        <h1>{esc(data.get("name", ""))}</h1>
        <div class="target">{esc(data.get("headline", ""))}</div>
      </div>
      <div class="contact">{contact}</div>
    </header>
    <div class="summary">{esc(data.get("summary", ""))}</div>
    {section("Technical Skills", f'<div class="skills">{skills}</div>')}
    {section("Professional Experience", "".join(roles))}
    {section("Education", education_body)}
    {interests_section}
  </main>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("Usage: build_resume_html.py input.json output.html", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(build(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
