#!/usr/bin/env python3
"""
Переоборачивает все внутренние страницы в новый шаблон lexakova-style.
Извлекает из исходного HTML title/description/breadcrumbs/main content
и оборачивает в новую шапку/футер/контакт-форму. Контент содержимого
сохраняется почти как есть — старые классы (.notary-article, .services
и т.д.) переопределены в lexakova-style.css.
"""
import os
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

# Все внутренние HTML файлы, кроме главной и сниппетов
INNER_DIRS = [
    "notarialnaya-kontora",
    "celi-obrashhenija",
    "deystviya-i-tarify",
    "pravovaya-informaciya",
    "kontakty",
    "articles",
    "fnc",
]


def find_inner_files():
    for d in INNER_DIRS:
        for p in (DOCS / d).rglob("*.html"):
            yield p


def base_prefix(depth: int) -> str:
    return "../" * depth


def extract_title(html: str) -> str:
    m = re.search(r"<title>\s*(.*?)\s*</title>", html, re.DOTALL)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else "Нотариус Колганов О. И."


def extract_description(html: str) -> str:
    m = re.search(r'<meta\s+name="description"\s+content="\s*(.*?)\s*"', html, re.DOTALL)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def extract_breadcrumbs(html):
    """Возвращает список (label, href|None). Поддерживает оба формата."""
    # 1) Новый формат — уже сконвертированная страница
    m_new = re.search(r'<ul class="lx-breadcrumbs">(.*?)</ul>', html, re.DOTALL)
    if m_new:
        items = []
        for li in re.findall(r"<li[^>]*>(.*?)</li>", m_new.group(1), re.DOTALL):
            a = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', li, re.DOTALL)
            if a:
                label = re.sub(r"<[^>]+>", " ", a.group(2)).strip()
                label = re.sub(r"\s+", " ", label)
                items.append((label, a.group(1)))
            else:
                label = re.sub(r"<[^>]+>", " ", li).strip()
                label = re.sub(r"\s+", " ", label)
                if label:
                    items.append((label, None))
        return items

    # 2) Старый формат
    m = re.search(r'<ul class="breadcrumbs">(.*?)</ul>', html, re.DOTALL)
    if not m:
        return []
    bc = m.group(1)
    items = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", bc, re.DOTALL):
        a = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', li, re.DOTALL)
        if a:
            label = re.sub(r"<[^>]+>", " ", a.group(2)).strip()
            label = re.sub(r"\s+", " ", label)
            items.append((label, a.group(1)))
        else:
            s = re.search(r'<span[^>]*class="active"[^>]*>(.*?)</span>', li, re.DOTALL)
            if s:
                label = re.sub(r"<[^>]+>", " ", s.group(1)).strip()
                label = re.sub(r"\s+", " ", label)
                if label:
                    items.append((label, None))
    return items


def extract_h1(html):
    # Сначала пробуем новый шаблон
    m = re.search(r'<h1[^>]*class="lx-page-title"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", " ", m.group(1)).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            return text
    # Старый шаблон
    m = re.search(r'<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", " ", m.group(1)).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            return text
    return None


def _strip_template_wrappers(content):
    """Удаляет любые вложенные блоки шаблона (на случай повторной конвертации)."""
    patterns = [
        r'<div class="lx-topbar">.*?</div>\s*</div>\s*</div>',  # topbar (3 уровня div)
        r'<div class="lx-topbar">.*?(?=<header|<section|<footer|$)',
        r'<header class="lx-header">.*?</header>',
        r'<section class="lx-page-head"[^>]*>.*?</section>',
        r'<section class="lx-section"[^>]*id="contact-form"[^>]*>.*?</section>',
        r'<footer class="lx-footer">.*?</footer>',
        r'<script src="[^"]*contact-form\.js"[^>]*>\s*</script>',
        r'</body>\s*</html>',
    ]
    for pat in patterns:
        content = re.sub(pat, '', content, flags=re.DOTALL)
    return content.strip()


def extract_main_content(html):
    """Контент между </ul> крошек и блоком sharing/cookie/footer.
    Идемпотентно: на уже сконвертированной странице возвращает содержимое .lx-page."""

    # Уже новый шаблон — берём только содержимое последнего (внутреннего) .lx-page
    matches = list(re.finditer(
        r'<section class="lx-page"[^>]*>\s*<div class="lx-container">\s*(.*?)\s*</div>\s*</section>',
        html, re.DOTALL,
    ))
    if matches:
        # Берём последний (самый вложенный) и дополнительно чистим
        body = matches[-1].group(1).strip()
        body = _strip_template_wrappers(body)
        return body

    after_bc = re.split(r'<ul class="breadcrumbs">.*?</ul>', html, maxsplit=1, flags=re.DOTALL)
    body = after_bc[-1] if len(after_bc) > 1 else html

    # обрезаем хвост: всё, начиная с notary-sharing / contact-section / footer
    end_markers = [
        r'<div class="notary-sharing">',
        r'<div class="container">\s*<div class="notary-sharing"',
        r'<div class="contact-section"',
        r"<footer",
        r'<div class="notary-modal--window">',
    ]
    end_idx = len(body)
    for marker in end_markers:
        m = re.search(marker, body, re.DOTALL)
        if m and m.start() < end_idx:
            end_idx = m.start()
    body = body[:end_idx]

    # Закрываем оставшиеся открытые контейнеры — потом наш шаблон откроет свои
    # Просто доверяем браузеру: посчитаем баланс и добавим </div> при перекосе.
    opens = len(re.findall(r"<div\b", body))
    closes = len(re.findall(r"</div>", body))
    if opens > closes:
        body += "</div>" * (opens - closes)
    elif closes > opens:
        # отрезаем лишние закрывающие в хвосте
        extra = closes - opens
        for _ in range(extra):
            last = body.rfind("</div>")
            if last == -1:
                break
            body = body[:last] + body[last + 6:]
    return body.strip()


def build_template(p: Path, title: str, description: str, breadcrumbs, h1, body: str) -> str:
    depth = len(p.relative_to(DOCS).parts) - 1  # 1 для notarialnaya-kontora/index.html, 2 для fnc/tarify/index.html
    base = base_prefix(depth)

    # Нормализуем breadcrumbs: первый элемент должен ссылаться на главную
    bc_html_items = []
    for i, (label, href) in enumerate(breadcrumbs):
        # пересобираем href под текущую глубину если он указывал на index.html главной
        if href in {"../index.html", "../../index.html", "/", "index.html"}:
            href = base + "index.html"
        if label.lower().startswith("главная"):
            href = base + "index.html"
        is_last = i == len(breadcrumbs) - 1
        if href and not is_last:
            bc_html_items.append(f'<li><a href="{href}">{label}</a></li>')
        else:
            bc_html_items.append(f"<li>{label}</li>")
    breadcrumbs_html = "\n                ".join(bc_html_items)

    # h1: если в исходнике не было title-блока, берём последний breadcrumb
    if not h1 and breadcrumbs:
        h1 = breadcrumbs[-1][0]
    if not h1:
        h1 = "Колганов О. И."

    template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="format-detection" content="telephone=no">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="icon" href="{base}static/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="{base}static/css/custom/lexakova-style.css">
    <link rel="stylesheet" href="{base}static/css/custom/contact-form.css">
</head>
<body class="lx">

<div class="lx-topbar">
    <div class="lx-container lx-topbar__row">
        <div class="lx-topbar__contacts">
            <span>Пн–Пт 10:00–19:00</span>
            <a href="mailto:Notarius@okolganov.ru">Notarius@okolganov.ru</a>
        </div>
        <div class="lx-topbar__contacts">
            <span>Реестр Минюста № 77/2542-н/77</span>
        </div>
    </div>
</div>

<header class="lx-header">
    <div class="lx-container">
        <div class="lx-header__row">
            <a href="{base}index.html" class="lx-logo">
                <span class="lx-logo__mark">КО</span>
                <span class="lx-logo__text">
                    <span class="lx-logo__name">Колганов О. И.</span>
                    <span class="lx-logo__role">Нотариус города Москвы</span>
                </span>
            </a>

            <div class="lx-header__meta">
                <div class="lx-meta-item">
                    <svg class="lx-meta-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <div>
                        <div class="lx-meta-item__label">Адрес</div>
                        <div class="lx-meta-item__value">Москва, ул. Фестивальная, 13к3</div>
                    </div>
                </div>
                <div class="lx-meta-item">
                    <svg class="lx-meta-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
                    <div>
                        <div class="lx-meta-item__label">Метро</div>
                        <div class="lx-meta-item__value">Речной вокзал, 3 мин</div>
                    </div>
                </div>
                <div class="lx-meta-item">
                    <svg class="lx-meta-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    <div>
                        <div class="lx-meta-item__label">Часы работы</div>
                        <div class="lx-meta-item__value">Пн–Пт 10:00–19:00</div>
                    </div>
                </div>
            </div>

            <div class="lx-header__cta">
                <a href="tel:+79956564404" class="lx-header__phone">+7 995 656-44-04</a>
                <a href="#contact-form" class="lx-btn lx-btn--primary">Задать вопрос</a>
            </div>
        </div>

        <nav class="lx-nav">
            <div class="lx-nav__row">
                <a href="{base}index.html" class="lx-nav__link">Главная</a>
                <a href="{base}notarialnaya-kontora/index.html" class="lx-nav__link">О нотариусе</a>
                <a href="{base}celi-obrashhenija/index.html" class="lx-nav__link">Нотариальные действия</a>
                <a href="{base}fnc/tarify/index.html" class="lx-nav__link">Тарифы</a>
                <a href="{base}articles/index.html" class="lx-nav__link">Статьи</a>
                <a href="{base}pravovaya-informaciya/index.html" class="lx-nav__link">Правовая информация</a>
                <a href="{base}kontakty/index.html" class="lx-nav__link">Контакты</a>
                <a href="#contact-form" class="lx-nav__link lx-nav__link--cta">Онлайн-запись</a>
            </div>
        </nav>
    </div>
</header>

<section class="lx-page-head">
    <div class="lx-container">
        <ul class="lx-breadcrumbs">
                {breadcrumbs_html}
        </ul>
        <h1 class="lx-page-title">{h1}</h1>
    </div>
</section>

<section class="lx-page">
    <div class="lx-container">
{body}
    </div>
</section>

<section class="lx-section" id="contact-form" style="background: var(--c-bg-soft);">
    <div class="lx-container">
        <h2 class="lx-h2" style="text-align:center;">Задать вопрос нотариусу</h2>
        <p class="lx-lead" style="margin: 0 auto 32px; text-align:center;">Опишите вашу ситуацию — мы свяжемся с вами и подберём оптимальное решение.</p>

        <form class="contact-form" novalidate>
            <div class="contact-form__row contact-form__row--split">
                <div class="contact-form__field">
                    <label class="contact-form__label contact-form__label--required" for="cf-name">Имя</label>
                    <input class="contact-form__input" type="text" id="cf-name" name="name" required autocomplete="name">
                </div>
                <div class="contact-form__field">
                    <label class="contact-form__label contact-form__label--required" for="cf-phone">Телефон</label>
                    <input class="contact-form__input" type="tel" id="cf-phone" name="phone" required autocomplete="tel" placeholder="+7 ___ ___ __ __">
                </div>
            </div>
            <div class="contact-form__row">
                <div class="contact-form__field">
                    <label class="contact-form__label" for="cf-email">Email <span style="color:#888;font-weight:400;">(необязательно)</span></label>
                    <input class="contact-form__input" type="email" id="cf-email" name="email" autocomplete="email">
                </div>
            </div>
            <div class="contact-form__row">
                <div class="contact-form__field">
                    <label class="contact-form__label contact-form__label--required" for="cf-purpose">Цель обращения</label>
                    <select class="contact-form__select" id="cf-purpose" name="purpose" required>
                        <option value="">— Выберите —</option>
                        <option value="Сделки с недвижимостью">Сделки с недвижимостью</option>
                        <option value="Наследство">Наследство</option>
                        <option value="Завещание">Завещание</option>
                        <option value="Доверенность">Доверенность</option>
                        <option value="Брачно-семейные отношения">Брачно-семейные отношения</option>
                        <option value="Корпоративные отношения">Корпоративные отношения</option>
                        <option value="Депозит нотариуса">Депозит нотариуса</option>
                        <option value="Уведомление о залоге движимого имущества">Уведомление о залоге движимого имущества</option>
                        <option value="Свидетельствование верности копий">Свидетельствование верности копий</option>
                        <option value="Другое">Другое</option>
                    </select>
                </div>
            </div>
            <div class="contact-form__row">
                <div class="contact-form__field">
                    <label class="contact-form__label contact-form__label--required" for="cf-message">Опишите вопрос</label>
                    <textarea class="contact-form__textarea" id="cf-message" name="message" rows="4" required></textarea>
                </div>
            </div>
            <div class="contact-form__row">
                <button class="contact-form__submit" type="submit">Отправить</button>
            </div>
            <div class="contact-form__status"></div>
            <p class="contact-form__hint">Отправляя форму, вы соглашаетесь с <a href="{base}fnc/personalnye-dannye/index.html">обработкой персональных данных</a></p>
        </form>
    </div>
</section>

<footer class="lx-footer">
    <div class="lx-container">
        <div class="lx-footer__grid">
            <div class="lx-footer__about">
                <div class="lx-footer__title">Колганов О. И.</div>
                <p><strong>Нотариус города Москвы</strong></p>
                <p style="margin-top: 12px;">Реестр Минюста № 77/2542-н/77<br>Приказ № 126 от 03.03.2026</p>
                <p style="margin-top: 12px;">125565, г. Москва,<br>ул. Фестивальная, дом 13, корпус 3</p>
            </div>
            <div>
                <div class="lx-footer__title">Разделы</div>
                <nav class="lx-footer__nav">
                    <a href="{base}notarialnaya-kontora/index.html">О нотариусе</a>
                    <a href="{base}celi-obrashhenija/index.html">Нотариальные действия</a>
                    <a href="{base}fnc/tarify/index.html">Тарифы</a>
                    <a href="{base}articles/index.html">Статьи</a>
                    <a href="{base}kontakty/index.html">Контакты</a>
                </nav>
            </div>
            <div>
                <div class="lx-footer__title">Информация</div>
                <nav class="lx-footer__nav">
                    <a href="{base}pravovaya-informaciya/index.html">Правовая информация</a>
                    <a href="{base}fnc/tarify/index.html">Тарифы</a>
                    <a href="{base}fnc/reestry/index.html">Публичные реестры</a>
                    <a href="{base}fnc/lgoty/index.html">Льготы</a>
                    <a href="{base}fnc/personalnye-dannye/index.html">Персональные данные</a>
                </nav>
            </div>
            <div>
                <div class="lx-footer__title">Контакты</div>
                <nav class="lx-footer__nav">
                    <a href="tel:+79956564404">+7 995 656-44-04</a>
                    <a href="mailto:Notarius@okolganov.ru">Notarius@okolganov.ru</a>
                    <span>Max: +7 995 656-44-04</span>
                    <span>Telegram: +7 995 656-44-04</span>
                    <span style="margin-top: 8px; color: #fff;">Пн–Пт 10:00–19:00</span>
                </nav>
            </div>
        </div>
        <div class="lx-footer__bottom">
            <span>© 2026 Нотариус Колганов О. И. Все права защищены.</span>
            <span><a href="{base}fnc/personalnye-dannye/index.html">Политика конфиденциальности</a></span>
        </div>
    </div>
</footer>

<script src="{base}static/js/custom/contact-form.js"></script>
</body>
</html>
"""
    return template


def convert(p):
    try:
        html = p.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"read error: {e}"

    title = extract_title(html)
    description = extract_description(html)
    bc = extract_breadcrumbs(html)
    h1 = extract_h1(html)
    body = extract_main_content(html)

    new = build_template(p, title, description, bc, h1, body)
    p.write_text(new, encoding="utf-8")
    return True, "ok"


def main():
    converted = 0
    errors = []
    for p in find_inner_files():
        ok, msg = convert(p)
        rel = p.relative_to(DOCS)
        if ok:
            converted += 1
            print(f"  ✓ {rel}")
        else:
            errors.append((rel, msg))
            print(f"  ✗ {rel}: {msg}")
    print(f"\nDone: {converted} converted, {len(errors)} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
