#!/usr/bin/env python3
"""Приводит иконку Max в кнопках шапки к готовому растровому логотипу
docs/static/image/max-logo.png (белый логотип на прозрачном фоне, выводится
на синем фоне кнопки .kn-msg-btn--max) на всех страницах.
Заменяет содержимое ссылки .kn-msg-btn--max (инлайн-<svg> или <img>) на <img>.

Путь до картинки релятивизируется по глубине страницы — так же, как это
делает scripts/build-header.py, чтобы сайт работал не только из корня домена."""
import re
import pathlib

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"

pat = re.compile(r'(kn-msg-btn--max"[^>]*>)(?:<svg[^>]*?>.*?</svg>|<img[^>]*?>)')

count = 0
for p in sorted(DOCS.rglob("*.html")):
    if "html-snippets" in p.parts:
        continue
    depth = len(p.relative_to(DOCS).parts) - 1
    prefix = "../" * depth
    img = f'<img src="{prefix}static/image/max-logo.png" alt="" width="17" height="17">'
    t = p.read_text(encoding="utf-8")
    nt, n = pat.subn(lambda m: m.group(1) + img, t)
    if n and nt != t:
        p.write_text(nt, encoding="utf-8")
        count += 1

print(f"Обновлено файлов: {count}")
