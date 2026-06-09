#!/usr/bin/env python3
"""
Единый источник шапки сайта.

Шапка (topbar + header + nav) описана ОДИН раз в
`docs/static/html-snippets/header.html` с путями от корня (`/...`).
Этот скрипт вставляет её во все страницы `docs/**/*.html`:

  - подставляет относительные пути нужной глубины (../, ../../);
  - помечает активный пункт меню по разделу страницы;
  - оборачивает в маркеры HEADER:START/END, поэтому повторный запуск
    просто пересинхронизирует шапку (идемпотентно).

Запуск:
    python3 scripts/build-header.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'docs'
SNIPPET_PATH = ROOT / 'static' / 'html-snippets' / 'header.html'

START = '<!-- HEADER:START (генерируется scripts/build-header.py — не редактировать вручную) -->'
END = '<!-- HEADER:END -->'

# Корни сайта для релятивизации абсолютных путей "/...".
SITE_ROOTS = (
    'static', 'media', 'image', 'index.html',
    'articles', 'celi-obrashhenija', 'deystviya-i-tarify',
    'fnc', 'kontakty', 'notarialnaya-kontora', 'pravovaya-informaciya',
)

# Раздел → href пункта меню (от корня), который надо подсветить.
SECTION_NAV = {
    'home':     '/index.html',
    'about':    '/notarialnaya-kontora/index.html',
    'services': '/celi-obrashhenija/index.html',
    'tariffs':  '/fnc/tarify/index.html',
    'articles': '/articles/index.html',
    'legal':    '/pravovaya-informaciya/index.html',
    'contacts': '/kontakty/index.html',
}


def section_for(rel: Path) -> str | None:
    parts = rel.parts
    if rel.name == 'index.html' and len(parts) == 1:
        return 'home'
    top = parts[0]
    if top == 'notarialnaya-kontora':
        return 'about'
    if top == 'celi-obrashhenija':
        return 'services'
    if top == 'articles':
        return 'articles'
    if top == 'kontakty':
        return 'contacts'
    if top == 'pravovaya-informaciya':
        return 'legal'
    if top == 'deystviya-i-tarify':
        return 'tariffs'
    if top == 'fnc':
        return 'tariffs' if len(parts) > 1 and parts[1] == 'tarify' else 'legal'
    return None


def set_active(header_abs: str, section: str | None) -> str:
    """Помечает активный пункт меню (пути ещё абсолютные)."""
    if not section:
        return header_abs
    href = SECTION_NAV[section]
    needle = f'<a href="{href}" class="kn-nav__link">'
    repl = f'<a href="{href}" class="kn-nav__link kn-nav__link--active">'
    return header_abs.replace(needle, repl, 1)


def relativize(html: str, depth: int) -> str:
    prefix = '../' * depth
    for root in SITE_ROOTS:
        html = html.replace(f'="/{root}', f'="{prefix}{root}')
    return html


# Блок старой (инлайн) шапки: от topbar до </header>, с опциональными
# комментариями-заголовками перед ним.
INLINE_RE = re.compile(
    r'(?:<!--[^\n]*?(?:Topbar|Header)[^\n]*?-->\s*)*'
    r'<div class="kn-topbar">.*?</header>',
    re.DOTALL,
)
MARKED_RE = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)


def process_file(path: Path, snippet_abs: str) -> bool:
    html = path.read_text(encoding='utf-8')
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1

    header = set_active(snippet_abs, section_for(rel))
    header = relativize(header, depth).rstrip('\n')
    block = f'{START}\n{header}\n{END}'

    if MARKED_RE.search(html):
        new = MARKED_RE.sub(lambda _: block, html, count=1)
    elif INLINE_RE.search(html):
        new = INLINE_RE.sub(lambda _: block, html, count=1)
    else:
        print(f'  ВНИМАНИЕ: шапка не найдена в {rel}')
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
    print(f'Шапка обновлена: {changed} из {len(files)} файлов')
    return 0


if __name__ == '__main__':
    sys.exit(main())
