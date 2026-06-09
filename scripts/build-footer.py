#!/usr/bin/env python3
"""
Единый источник подвала сайта.

Подвал описан ОДИН раз в `docs/static/html-snippets/footer.html`
с путями от корня (`/...`). Этот скрипт вставляет его во все
страницы `docs/**/*.html`:

  - подставляет относительные пути нужной глубины (../, ../../);
  - оборачивает в маркеры FOOTER:START/END, поэтому повторный запуск
    просто пересинхронизирует подвал (идемпотентно).

Запуск:
    python3 scripts/build-footer.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'docs'
SNIPPET_PATH = ROOT / 'static' / 'html-snippets' / 'footer.html'

START = '<!-- FOOTER:START (генерируется scripts/build-footer.py — не редактировать вручную) -->'
END = '<!-- FOOTER:END -->'

# Корни сайта для релятивизации абсолютных путей "/...".
SITE_ROOTS = (
    'static', 'media', 'image', 'index.html',
    'articles', 'celi-obrashhenija', 'deystviya-i-tarify',
    'fnc', 'kontakty', 'notarialnaya-kontora', 'pravovaya-informaciya',
)


def relativize(html: str, depth: int) -> str:
    prefix = '../' * depth
    for root in SITE_ROOTS:
        html = html.replace(f'="/{root}', f'="{prefix}{root}')
    return html


# Блок старого (инлайн) подвала: сам <footer>...</footer> с опциональным
# комментарием-заголовком перед ним.
INLINE_RE = re.compile(
    r'(?:<!--[^\n]*?Footer[^\n]*?-->\s*)*'
    r'<footer[^>]*>.*?</footer>',
    re.DOTALL,
)
MARKED_RE = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)


def process_file(path: Path, snippet_abs: str) -> bool:
    html = path.read_text(encoding='utf-8')
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1

    footer = relativize(snippet_abs, depth).rstrip('\n')
    block = f'{START}\n{footer}\n{END}'

    if MARKED_RE.search(html):
        new = MARKED_RE.sub(lambda _: block, html, count=1)
    elif INLINE_RE.search(html):
        new = INLINE_RE.sub(lambda _: block, html, count=1)
    else:
        print(f'  ВНИМАНИЕ: подвал не найден в {rel}')
        return False

    if new != html:
        path.write_text(new, encoding='utf-8')
        return True
    return False


def main() -> int:
    snippet_abs = SNIPPET_PATH.read_text(encoding='utf-8').rstrip('\n')
    files = [p for p in sorted(ROOT.rglob('*.html'))
             if 'html-snippets' not in p.parts]
    changed = sum(process_file(p, snippet_abs) for p in files)
    print(f'Подвал обновлён: {changed} из {len(files)} файлов')
    return 0


if __name__ == '__main__':
    sys.exit(main())
