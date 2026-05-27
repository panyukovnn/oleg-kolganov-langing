#!/usr/bin/env python3
"""
Пост-обработка зеркала сайта okolganov.ru:
  - вырезает элементы конструктора (cookie-баннер, "версия для слабовидящих", Vue-форма записи и подобное);
  - подключает кастомный CSS/JS (contact-form);
  - инжектит секцию формы обратной связи в главную и страницу контактов;
  - добавляет кнопку "Задать вопрос" в шапку.

Запуск:
    python3 scripts/post-process.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'site'
SNIPPET_PATH = ROOT / 'static' / 'html-snippets' / 'contact-form.html'

# Регулярки для блоков-конструктора, которые удаляем целиком
CONSTRUCTOR_PATTERNS = [
    # Кнопка "Версия для слабовидящих"
    r'<button class="blind-button">[^<]*</button>\s*',
    # Vue-форма записи на приём (CSS-ссылка)
    r'<link rel="stylesheet" href="static/js/appointment-form/style\.css"[^>]*/?>\s*',
    # Vue-форма (JS)
    r'<script src="static/js/appointment-form/appointment-form\.umd\.cjs"[^>]*></script>\s*',
    # Vue CDN
    r'<script src="https://cdn\.jsdelivr\.net/npm/vue@2\.7"[^>]*></script>\s*',
    # Контейнер формы записи (пустой div)
    r'<div class="container container-form">\s*</div>\s*',
]

# Cookie-баннер — был на оригинале, восстанавливаем после очередного зеркалирования
COOKIE_BANNER = '''
<div class="cookie-alert--container">
    <div class="container">
        <p class="cookie-alert">
            <span>Этот сайт использует cookie–файлы.</span>
            <a href="/fnc/personalnye-dannye/index.html">Узнать больше</a>
            <img src="/static/svg/close_black.svg" class="cookie-alert--close" width="15" height="15" alt="" />
        </p>
    </div>
</div>
'''

# Что инжектим в <head> на всех страницах
HEAD_INJECTION = '<link href="/static/css/custom/contact-form.css" rel="stylesheet" type="text/css" />\n'

# Что инжектим перед </body> на всех страницах
BODY_INJECTION = (
    '<script src="/static/js/custom/carousel-fallback.js" defer></script>\n'
    '<script src="/static/js/custom/contact-form.js" defer></script>\n'
)

# CTA-ссылка для навигационного меню (выглядит как остальные пункты меню)
HEADER_CTA_DESKTOP = (
    '<a href="/index.html#contact-form" class="notary-header-menu--link cta-link">'
    'Задать вопрос</a>'
)
HEADER_CTA_MOBILE = (
    '<a href="/index.html#contact-form" class="notary-header-mob__menu--link cta-link">'
    'Задать вопрос</a>'
)


def load_contact_form_snippet() -> str:
    return SNIPPET_PATH.read_text(encoding='utf-8')


def strip_constructor(html: str) -> str:
    for pattern in CONSTRUCTOR_PATTERNS:
        html = re.sub(pattern, '', html)
    return html


def inject_assets(html: str) -> str:
    # Поскольку в HTML много страниц лежат на разной глубине, ссылки на ассеты
    # делаем абсолютными от корня сайта (/static/...). При локальном просмотре
    # через python http.server и на GitHub Pages это работает одинаково.
    if 'contact-form.css' not in html:
        html = html.replace('</head>', f'{HEAD_INJECTION}</head>', 1)
    if 'carousel-fallback.js' not in html:
        html = html.replace('</body>', f'{BODY_INJECTION}</body>', 1)
    return html


def fix_asset_paths_for_subpages(html: str, depth: int) -> str:
    """
    На страницах в подпапках (depth>0) wget оставил относительные пути типа
    'static/...' и 'media/...', которые ломаются. Превращаем их в абсолютные.
    """
    if depth == 0:
        return html
    # href="static/..." / src="static/..." / src="media/..." / href="media/..."
    html = re.sub(r'(href|src)="(static|media)/', r'\1="/\2/', html)
    return html


def replace_help_carousel(html: str) -> str:
    """
    Owl-карусель для блока «Нотариус поможет» работает нестабильно (картинки серые).
    Заменяем её на CSS-only горизонтальный скролл — проще и надёжнее.
    """
    # Меняем класс на свой, чтобы owl его не трогал
    return html.replace(
        '<div class="owl-carousel notary-help-carousel">',
        '<div class="notary-help-grid">',
    )


def fix_inline_bg_urls(html: str) -> str:
    """
    Inline-стили вида style="background-image: url(media/...)" Owl плохо переваривает
    при cloned-элементах. Делаем URL абсолютными от корня сайта.
    """
    # url(media/...) → url(/media/...)
    html = re.sub(r'url\((media|static)/', r'url(/\1/', html)
    # url("media/...") → url("/media/...")
    html = re.sub(r'url\((["\'])(media|static)/', r'url(\1/\2/', html)
    return html


def inject_header_cta(html: str) -> str:
    """Добавляем CTA-ссылку «Задать вопрос» в навигационное меню."""
    if 'class="notary-header-menu--link cta-link"' in html:
        return html  # уже вставлено
    # Десктоп: последняя ссылка в notary-header-menu — «Контакты»
    desktop_pattern = re.compile(
        r'(<a href="[^"]+" class="notary-header-menu--link">Контакты</a>)'
    )
    html = desktop_pattern.sub(r'\1' + '\n\n\t' + HEADER_CTA_DESKTOP, html, count=1)
    # Мобильное меню
    mobile_pattern = re.compile(
        r'(<a href="[^"]+" class="notary-header-mob__menu--link">Контакты</a>)'
    )
    html = mobile_pattern.sub(r'\1' + '\n\n\t' + HEADER_CTA_MOBILE, html, count=1)
    return html


def restore_cookie_banner(html: str) -> str:
    """Возвращает cookie-баннер, если его нет (он удаляется при очередном зеркалировании)."""
    if 'cookie-alert--container' in html:
        return html
    # Вставляем после </header> (и перед основным контентом). Если есть .notary-header-mob, ставим после неё.
    mob_close = '</div>\n    </div>\n    <div class="notary-header-mob--tel">'
    # Ищем закрытие notary-header-mob (последний </div></div> перед основным контентом)
    # Проще: вставляем перед первым крупным div после header'ов
    # Самый надёжный маркер — </header>, а потом дополнительно после notary-header-mob
    # Здесь вставим прямо перед закрытием <body> ... нет, должно быть перед контентом.
    # Делаем так: вставляем после последнего </header> ИЛИ закрытия notary-header-mob.
    # У всех страниц есть `<div class="notary-header-mob">...</div>` после `<header>`.
    # Найдём конец этого блока: следующий тег после mob__menu закрытий.
    pattern = re.compile(r'(</header>\s*<div class="notary-header-mob">[\s\S]*?</div>\s*</div>\s*</div>)', re.MULTILINE)
    m = pattern.search(html)
    if m:
        end_pos = m.end()
        return html[:end_pos] + '\n' + COOKIE_BANNER + html[end_pos:]
    # fallback: после </header>
    return re.sub(r'(</header>)', r'\1\n' + COOKIE_BANNER, html, count=1)


def inject_contact_form(html: str, snippet: str) -> str:
    """Вставляем секцию формы перед футером (только на главной и контактах)."""
    if 'class="contact-section"' in html:
        return html  # уже вставлено
    # Перед <footer ...>
    return re.sub(r'(<footer\b)', snippet + r'\n\1', html, count=1)


def process_file(path: Path, snippet: str, inject_form: bool) -> None:
    html = path.read_text(encoding='utf-8')
    original = html

    # глубина: site/index.html → 0, site/articles/foo.html → 1, site/fnc/tarify/index.html → 2
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1

    html = strip_constructor(html)
    html = fix_asset_paths_for_subpages(html, depth)
    html = fix_inline_bg_urls(html)
    html = replace_help_carousel(html)
    html = inject_assets(html)
    html = inject_header_cta(html)
    html = restore_cookie_banner(html)
    if inject_form:
        html = inject_contact_form(html, snippet)

    if html != original:
        path.write_text(html, encoding='utf-8')


def main() -> int:
    snippet = load_contact_form_snippet()
    html_files = sorted(ROOT.rglob('*.html'))
    # Исключаем сам сниппет
    html_files = [p for p in html_files if 'html-snippets' not in p.parts]

    form_pages = {ROOT / 'index.html', ROOT / 'kontakty' / 'index.html'}

    for path in html_files:
        process_file(path, snippet, inject_form=(path in form_pages))

    print(f'Обработано: {len(html_files)} HTML-файлов')
    return 0


if __name__ == '__main__':
    sys.exit(main())
