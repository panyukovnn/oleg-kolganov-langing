#!/usr/bin/env python3
"""Вставляет группу кнопок мессенджеров (WhatsApp, Telegram, Max) и email
в блок .kn-header__cta на всех страницах с общей шапкой.

WhatsApp и email — известные данные (тот же номер/адрес, что в контактах).
Telegram username и ссылка Max пока неизвестны — оставлены placeholder + TODO.
Иконки инлайнятся в разметку (currentColor), чтобы не зависеть от глубины пути.
"""
import pathlib

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"

OLD = (
    '            <div class="kn-header__cta">\n'
    '                <a href="tel:+79956564404" class="kn-header__phone">+7 (995) 656-44-04</a>\n'
    '                <a href="#contact-form" class="kn-btn kn-btn--primary">Задать вопрос</a>\n'
    '            </div>'
)

WA = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
      '<path d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.96L2.05 22l5.25-1.38a9.9 9.9 0 0 0 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.91-7.01zM12.05 20.15h-.01a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.2 8.2 0 0 1-1.26-4.38c0-4.54 3.7-8.23 8.24-8.23 2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.83c0 4.54-3.69 8.23-8.23 8.23zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.25-.64.81-.79.97-.14.17-.29.19-.54.06-.25-.12-1.05-.39-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.01-.38.11-.51.11-.11.25-.29.37-.43.13-.14.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.43.06-.66.31-.23.25-.86.85-.86 2.07 0 1.22.89 2.4 1.01 2.56.12.17 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.47-.6 1.67-1.18.21-.58.21-1.07.14-1.18-.06-.11-.22-.17-.47-.29z"/></svg>')

TG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
      '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.21-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 0 0-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>')

MAX = '<img src="/static/image/max-logo.png" alt="" width="17" height="17">'

EMAIL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
         '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zm8 7.1 8-5.1H4l8 5.1zM4 8.2V18h16V8.2l-8 5.1-8-5.1z"/></svg>')

NEW = (
    '            <div class="kn-header__cta">\n'
    '                <a href="tel:+79956564404" class="kn-header__phone">+7 (995) 656-44-04</a>\n'
    '                <div class="kn-header__messengers">\n'
    f'                    <a href="https://wa.me/79956564404" class="kn-msg-btn kn-msg-btn--whatsapp" target="_blank" rel="noopener" aria-label="Написать в WhatsApp" title="WhatsApp">{WA}</a>\n'
    f'                    <a href="https://t.me/Okolganov" class="kn-msg-btn kn-msg-btn--telegram" target="_blank" rel="noopener" aria-label="Написать в Telegram" title="Telegram">{TG}</a>\n'
    f'                    <a href="https://max.ru/u/f9LHodD0cOIRdgVJ1zxPwkshPcipNgZIbqhFZIq8madFqTMSitCO0bGGb80" class="kn-msg-btn kn-msg-btn--max" target="_blank" rel="noopener" aria-label="Написать в Max" title="Max">{MAX}</a>\n'
    f'                    <a href="mailto:Notarius@okolganov.ru" class="kn-msg-btn kn-msg-btn--email" aria-label="Написать на email" title="Электронная почта">{EMAIL}</a>\n'
    '                </div>\n'
    '                <a href="#contact-form" class="kn-btn kn-btn--primary">Задать вопрос</a>\n'
    '            </div>'
)

changed, skipped = [], []
for path in sorted(DOCS.rglob("*.html")):
    text = path.read_text(encoding="utf-8")
    if OLD in text:
        path.write_text(text.replace(OLD, NEW), encoding="utf-8")
        changed.append(str(path.relative_to(DOCS)))
    elif "kn-header__cta" in text:
        skipped.append(str(path.relative_to(DOCS)))

print(f"Изменено файлов: {len(changed)}")
for c in changed:
    print("  +", c)
if skipped:
    print(f"\nПропущено (есть kn-header__cta, но блок не совпал): {len(skipped)}")
    for s in skipped:
        print("  !", s)
