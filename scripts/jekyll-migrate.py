#!/usr/bin/env python3
"""
Одноразовая миграция статического сайта в Jekyll (TASK-35).

Что делает:
  1. Строит _includes/header.html и _includes/footer.html из html-snippets,
     заменяя абсолютные пути `/...` на `{{ '/...' | relative_url }}` и добавляя
     подсветку активного пункта меню по переменной page.section.
  2. Переводит каждую страницу docs/**/*.html на layout + front matter:
     вырезает <head>, блоки HEADER:START/END и FOOTER:START/END и финальные
     служебные скрипты — всё это теперь даёт layout/include. В front matter
     выносятся title, description, og-поля, доп. стили и скрипты.
  3. Выносит статьи docs/articles/*.html (кроме index) в коллекцию _articles/
     с permalink, сохраняющим прежние URL, и метаданными категории.
  4. Перегенерирует docs/articles/index.html — список статей строится Liquid-ом
     по site.articles и _data/article_categories.yml.

Запуск (один раз):
    python3 scripts/jekyll-migrate.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SNIPPETS = DOCS / "static" / "html-snippets"

HEADER_START = "<!-- HEADER:START"
HEADER_END = "<!-- HEADER:END -->"
FOOTER_START = "<!-- FOOTER:START"
FOOTER_END = "<!-- FOOTER:END -->"

# Стили/скрипты, которые даёт layout для всех страниц (в front matter не выносим).
UNIVERSAL_CSS = {
    "/static/css/custom/main-style.css",
    "/static/css/custom/contact-form.css",
}
UNIVERSAL_BODY_JS = {"/static/js/custom/contact-form.js"}

# Раздел страницы -> подпись пункта меню для подсветки активности.
SECTION_BY_LABEL = {
    "Главная": "home",
    "О нотариусе": "about",
    "Нотариальные действия": "services",
    "Тарифы": "tariffs",
    "Статьи": "articles",
    "Правовая информация": "legal",
    "Контакты": "contacts",
}


def relativize(text: str) -> str:
    """`href="/x"` / `src="/x"` -> `href="{{ '/x' | relative_url }}"`."""
    return re.sub(
        r'(href|src)="(/[^"]*)"',
        lambda m: f'{m.group(1)}="{{{{ \'{m.group(2)}\' | relative_url }}}}"',
        text,
    )


def norm_path(p: str) -> str:
    """`../../static/x` -> `/static/x`; `static/x` -> `/static/x`."""
    p = re.sub(r"^(\.\./)+", "", p)
    p = p.lstrip("./")
    return "/" + p.lstrip("/")


def section_for(rel: Path) -> str | None:
    parts = rel.parts
    if rel.name == "index.html" and len(parts) == 1:
        return "home"
    top = parts[0]
    return {
        "notarialnaya-kontora": "about",
        "celi-obrashhenija": "services",
        "articles": "articles",
        "kontakty": "contacts",
        "pravovaya-informaciya": "legal",
        "deystviya-i-tarify": "tariffs",
    }.get(top) or (
        ("tariffs" if len(parts) > 1 and parts[1] == "tarify" else "legal")
        if top == "fnc"
        else None
    )


# --------------------------------------------------------------------------- #
#  1. Includes
# --------------------------------------------------------------------------- #
def build_includes() -> None:
    inc = DOCS / "_includes"
    inc.mkdir(exist_ok=True)

    header = relativize((SNIPPETS / "header.html").read_text(encoding="utf-8").rstrip("\n"))
    for label, sec in SECTION_BY_LABEL.items():
        needle = f'class="kn-nav__link">{label}</a>'
        repl = (
            f'class="kn-nav__link{{% if page.section == \'{sec}\' %}}'
            f' kn-nav__link--active{{% endif %}}">{label}</a>'
        )
        if needle not in header:
            raise SystemExit(f"Не найден пункт меню для подсветки: {label}")
        header = header.replace(needle, repl, 1)
    (inc / "header.html").write_text(header + "\n", encoding="utf-8")

    footer = relativize((SNIPPETS / "footer.html").read_text(encoding="utf-8").rstrip("\n"))
    (inc / "footer.html").write_text(footer + "\n", encoding="utf-8")
    print("includes: header.html, footer.html созданы")


# --------------------------------------------------------------------------- #
#  Разбор исходной страницы
# --------------------------------------------------------------------------- #
def attr(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def parse_page(html: str):
    head = re.search(r"<head>(.*?)</head>", html, re.DOTALL).group(1)

    title = attr(r"<title>(.*?)</title>", head)
    description = attr(r'<meta name="description" content="(.*?)">', head)
    og_title = attr(r'<meta property="og:title" content="(.*?)">', head)
    og_description = attr(r'<meta property="og:description" content="(.*?)">', head)

    styles = [
        norm_path(h)
        for h in re.findall(r'<link rel="stylesheet" href="(.*?)"', head)
        if norm_path(h) not in UNIVERSAL_CSS
    ]
    head_scripts = [norm_path(s) for s in re.findall(r'<script src="(.*?)"', head)]
    jsonld_m = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', head, re.DOTALL
    )
    jsonld = jsonld_m.group(1).strip("\n") if jsonld_m else None

    # Тело: между HEADER:END и FOOTER:START.
    a = html.index(HEADER_END) + len(HEADER_END)
    b = html.index(FOOTER_START)
    body = html[a:b].strip("\n")

    # Скрипты после FOOTER:END (кроме универсальных и виджета YClients).
    tail = html[html.index(FOOTER_END) + len(FOOTER_END):]
    body_scripts = [
        norm_path(s)
        for s in re.findall(r'<script src="(.*?)"', tail)
        if "yclients" not in s and norm_path(s) not in UNIVERSAL_BODY_JS
    ]

    return {
        "title": title,
        "description": description,
        "og_title": og_title,
        "og_description": og_description,
        "styles": styles,
        "head_scripts": head_scripts,
        "jsonld": jsonld,
        "body": body,
        "body_scripts": body_scripts,
    }


def y(s: str) -> str:
    """Безопасный YAML-скаляр (двойные кавычки в стиле JSON)."""
    return json.dumps(s, ensure_ascii=False)


def front_matter(fields: dict) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if v in (None, [], ""):
            continue
        if k == "jsonld":
            block = "\n".join("  " + ln for ln in v.splitlines())
            lines.append(f"{k}: |\n{block}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            lines.extend(f"  - {y(item)}" for item in v)
        else:
            lines.append(f"{k}: {y(v)}")
    lines.append("---")
    return "\n".join(lines)


def build_page_fields(parsed: dict, section: str | None, extra: dict | None = None) -> dict:
    fields = {
        "layout": "default",
        "title": parsed["title"],
        "description": parsed["description"],
    }
    if section:
        fields["section"] = section
    if extra:
        fields.update(extra)
    if parsed["og_title"] and parsed["og_title"] != parsed["title"]:
        fields["og_title"] = parsed["og_title"]
    if parsed["og_description"] and parsed["og_description"] != parsed["description"]:
        fields["og_description"] = parsed["og_description"]
    fields["styles"] = parsed["styles"]
    fields["head_scripts"] = parsed["head_scripts"]
    fields["body_scripts"] = parsed["body_scripts"]
    fields["jsonld"] = parsed["jsonld"]
    return fields


# --------------------------------------------------------------------------- #
#  3. Метаданные статей из текущего articles/index.html
# --------------------------------------------------------------------------- #
def parse_article_index():
    """-> (order_of_categories, {slug: {category, label, tag, title, text, order}})."""
    html = (DOCS / "articles" / "index.html").read_text(encoding="utf-8")
    groups = re.findall(
        r'<div class="kn-art-group" data-cat="(.*?)">(.*?)</div>\s*</div>',
        html,
        re.DOTALL,
    )
    meta: dict[str, dict] = {}
    order = 0
    for cat, block in groups:
        label = attr(r'<h3 class="kn-h3">(.*?)</h3>', block)
        cards = re.findall(
            r'<a href="\.\./articles/(.*?)\.html" class="kn-article">(.*?)</a>',
            block,
            re.DOTALL,
        )
        for slug, card in cards:
            order += 1
            meta[slug] = {
                "category": cat,
                "cat_label": label,
                "tag": attr(r'<div class="kn-article__tag">(.*?)</div>', card),
                "card_title": attr(r'<h3 class="kn-article__title">(.*?)</h3>', card),
                "excerpt": attr(r'<p class="kn-article__text">(.*?)</p>', card),
                "order": order,
            }
    return meta


# --------------------------------------------------------------------------- #
#  Перегенерация articles/index.html
# --------------------------------------------------------------------------- #
ARTICLES_INDEX_BODY = """
<section class="kn-page-head">
    <div class="kn-container">
        <ul class="kn-breadcrumbs">
                <li><a href="{{ '/index.html' | relative_url }}">Главная</a></li>
                <li>Статьи</li>
        </ul>
        <h1 class="kn-page-title">Статьи</h1>
    </div>
</section>

<section class="kn-section">
    <div class="kn-container">
        <p class="kn-lead">Практические разборы типовых ситуаций и ответы на частые вопросы по нотариальным действиям. Выберите тему или посмотрите все материалы.</p>

        <div class="kn-art-filter">
            <button type="button" class="kn-art-filter__btn kn-art-filter__btn--active" data-filter="all">Все</button>
            {%- for cat in site.data.article_categories %}
            <button type="button" class="kn-art-filter__btn" data-filter="{{ cat.slug }}">{{ cat.label }}</button>
            {%- endfor %}
        </div>

        {%- for cat in site.data.article_categories %}
        {%- assign items = site.articles | where: "category", cat.slug | sort: "order" %}
        {%- if items.size > 0 %}
        <div class="kn-art-group" data-cat="{{ cat.slug }}">
            <h3 class="kn-h3">{{ cat.label }}</h3>
            <div class="kn-articles">
                {%- for post in items %}
                <a href="{{ post.url | relative_url }}" class="kn-article">
                    <div class="kn-article__body">
                        <div class="kn-article__tag">{{ post.tag }}</div>
                        <h3 class="kn-article__title">{{ post.card_title }}</h3>
                        <p class="kn-article__text">{{ post.excerpt }}</p>
                    </div>
                </a>
                {%- endfor %}
            </div>
        </div>
        {%- endif %}
        {%- endfor %}
    </div>
</section>

<section class="kn-section" id="contact-form" style="background: var(--c-bg);">
    <div class="kn-container">
        <h2 class="kn-h2" style="text-align:center;">Задать вопрос нотариусу</h2>
        <p class="kn-lead" style="margin: 0 auto 32px; text-align:center;">Опишите вашу ситуацию — мы свяжемся с вами и подберём оптимальное решение.</p>

        <div data-contact-form></div>
    </div>
</section>
""".strip("\n")


def migrate():
    build_includes()
    art_meta = parse_article_index()

    pages = [
        p
        for p in sorted(DOCS.rglob("*.html"))
        if "html-snippets" not in p.parts and "_includes" not in p.parts
    ]

    converted = 0
    for path in pages:
        rel = path.relative_to(DOCS)
        html = path.read_text(encoding="utf-8")
        if HEADER_START not in html:
            continue  # уже мигрирована или не страница сайта
        is_article = rel.parts[0] == "articles" and rel.name != "index.html"
        if rel == Path("articles/index.html"):
            continue  # перегенерируем отдельно

        parsed = parse_page(html)
        section = section_for(rel)

        if is_article:
            slug = path.stem
            m = art_meta.get(slug, {})
            extra = {
                "permalink": f"/articles/{slug}.html",
                "category": m.get("category"),
                "cat_label": m.get("cat_label"),
                "tag": m.get("tag"),
                "card_title": m.get("card_title"),
                "excerpt": m.get("excerpt"),
                "order": m.get("order"),
            }
            fields = build_page_fields(parsed, None, extra)
            fields.pop("section", None)  # секция задаётся defaults коллекции
            out = DOCS / "_articles" / f"{slug}.html"
            out.parent.mkdir(exist_ok=True)
            out.write_text(front_matter(fields) + "\n" + parsed["body"] + "\n", encoding="utf-8")
            path.unlink()  # убираем оригинал из docs/articles/
            converted += 1
        else:
            fields = build_page_fields(parsed, section)
            path.write_text(front_matter(fields) + "\n" + parsed["body"] + "\n", encoding="utf-8")
            converted += 1

    # Articles index
    idx_html = (DOCS / "articles" / "index.html").read_text(encoding="utf-8")
    parsed_idx = parse_page(idx_html)
    idx_fields = {
        "layout": "default",
        "title": parsed_idx["title"],
        "description": parsed_idx["description"],
        "section": "articles",
        "permalink": "/articles/index.html",
    }
    if parsed_idx["og_title"] and parsed_idx["og_title"] != parsed_idx["title"]:
        idx_fields["og_title"] = parsed_idx["og_title"]
    if parsed_idx["og_description"] and parsed_idx["og_description"] != parsed_idx["description"]:
        idx_fields["og_description"] = parsed_idx["og_description"]
    idx_fields["styles"] = parsed_idx["styles"]
    idx_fields["body_scripts"] = parsed_idx["body_scripts"]
    (DOCS / "articles" / "index.html").write_text(
        front_matter(idx_fields) + "\n" + ARTICLES_INDEX_BODY + "\n", encoding="utf-8"
    )

    print(f"Сконвертировано страниц: {converted}")
    print(f"Статей в коллекции: {len(list((DOCS / '_articles').glob('*.html')))}")


if __name__ == "__main__":
    migrate()
