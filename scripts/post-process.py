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

ROOT = Path(__file__).resolve().parent.parent / 'docs'
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
    # Родная форма обратной связи от конструктора (POST на okolganov.ru/feedback —
    # не работает с GitHub Pages, плюс класс .contact-form конфликтует с нашей формой)
    r'<form action="https://okolganov\.ru/feedback/[^"]*"[^>]*>[\s\S]*?</form>\s*',
    # Сопутствующий комментарий-скрипт от старой формы
    r'<script type="text/javascript">\s*//\s*no \$ here[\s\S]*?</script>\s*',
]

# Кастомные инъекции — удаляются в начале процессинга, чтобы потом гарантированно
# добавиться один раз (true idempotent).
CUSTOM_INJECTION_PATTERNS = [
    r'<link href="[^"]*static/css/custom/redesign\.css"[^>]*/?>\s*',
    r'<link href="[^"]*static/css/custom/contact-form\.css"[^>]*/?>\s*',
    r'<script src="[^"]*static/js/custom/contact-form\.js"[^>]*></script>\s*',
    r'<script src="[^"]*static/js/custom/carousel-fallback\.js"[^>]*></script>\s*',
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

# Что инжектим в <head> на всех страницах.
# redesign.css подключаем ПЕРВЫМ — это база с токенами и общими стилями.
# contact-form.css — поверх, со стилями только для формы.
HEAD_INJECTION = (
    '<link href="/static/css/custom/redesign.css" rel="stylesheet" type="text/css" />\n'
    '<link href="/static/css/custom/contact-form.css" rel="stylesheet" type="text/css" />\n'
)

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


def strip_custom_injections(html: str) -> str:
    """Удаляем наши прошлые инъекции, чтобы потом добавить ровно по одной."""
    for pattern in CUSTOM_INJECTION_PATTERNS:
        html = re.sub(pattern, '', html)
    return html


def inject_assets(html: str) -> str:
    # Инжектим с абсолютными путями; функция relativize_paths ниже превратит их в
    # относительные с учётом глубины страницы.
    html = html.replace('</head>', f'{HEAD_INJECTION}</head>', 1)
    html = html.replace('</body>', f'{BODY_INJECTION}</body>', 1)
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


# Корневые директории/файлы сайта, на которые могут ссылаться абсолютные пути в HTML.
SITE_ROOTS = (
    'static', 'media', 'index.html',
    'articles', 'celi-obrashhenija', 'deystviya-i-tarify',
    'fnc', 'kontakty', 'notarialnaya-kontora', 'pravovaya-informaciya',
)


def relativize_paths(html: str, depth: int) -> str:
    """
    Превращает абсолютные пути от корня сайта (например /static/..., /media/...,
    /index.html#xxx) в относительные пути нужной глубины.

    depth=0 (docs/index.html):     /static/x → static/x
    depth=1 (docs/articles/y.html): /static/x → ../static/x
    depth=2 (docs/fnc/tarify/...): /static/x → ../../static/x

    Сразу работает и в HTML-атрибутах (href, src), и в inline-стилях (url(...)).
    Не трогает протокольные URL (http://, https://, //example.com) и анкоры (#xxx).
    """
    prefix = '../' * depth
    for root in SITE_ROOTS:
        # href="/static/..." → href="{prefix}static/..."
        html = html.replace(f'="/{root}', f'="{prefix}{root}')
        # url(/static/...) и url("/static/..."), url('/static/...')
        html = html.replace(f'url(/{root}', f'url({prefix}{root}')
        html = html.replace(f'url("/{root}', f'url("{prefix}{root}')
        html = html.replace(f"url('/{root}", f"url('{prefix}{root}")
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

    # глубина: docs/index.html → 0, docs/articles/foo.html → 1, docs/fnc/tarify/index.html → 2
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1

    html = strip_constructor(html)
    html = strip_custom_injections(html)
    html = replace_help_carousel(html)
    html = inject_assets(html)
    html = inject_header_cta(html)
    html = restore_cookie_banner(html)
    if inject_form:
        html = inject_contact_form(html, snippet)
    # Финальный шаг: все абсолютные пути → относительные нужной глубины
    html = relativize_paths(html, depth)

    if html != original:
        path.write_text(html, encoding='utf-8')


def main() -> int:
    snippet = load_contact_form_snippet()
    html_files = sorted(ROOT.rglob('*.html'))
    # Исключаем сам сниппет
    html_files = [p for p in html_files if 'html-snippets' not in p.parts]

    form_pages = {
        ROOT / 'index.html',
        ROOT / 'kontakty' / 'index.html',
        ROOT / 'notarialnaya-kontora' / 'index.html',
    }

    for path in html_files:
        process_file(path, snippet, inject_form=(path in form_pages))

    print(f'Обработано: {len(html_files)} HTML-файлов')
    return 0


if __name__ == '__main__':
    sys.exit(main())
