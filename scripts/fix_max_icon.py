#!/usr/bin/env python3
"""Заменяет инлайн-SVG иконки Max в кнопках шапки на содержимое
docs/static/svg/contacts/max.svg (чистый речевой пузырь) на всех страницах.
Ищет <svg>...</svg> внутри ссылки с классом kn-msg-btn--max."""
import re
import pathlib

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"

new_svg = (DOCS / "static/svg/contacts/max.svg").read_text(encoding="utf-8")
new_svg = "".join(line.strip() for line in new_svg.splitlines())

pat = re.compile(r'(kn-msg-btn--max"[^>]*>)<svg[^>]*?>.*?</svg>')

count = 0
for p in sorted(DOCS.rglob("*.html")):
    t = p.read_text(encoding="utf-8")
    nt, n = pat.subn(lambda m: m.group(1) + new_svg, t)
    if n:
        p.write_text(nt, encoding="utf-8")
        count += 1

print(f"Обновлено файлов: {count}")
