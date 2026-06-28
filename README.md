# Сайт нотариуса Колганова О. И.

Статическая копия `okolganov.ru` для размещения на GitHub Pages + форма обратной связи, отправляющая ответы в Google Form.

## Структура

```
.
├── docs/                       # это и есть сайт — деплоится на GitHub Pages
│   ├── index.html              # главная (с формой обратной связи)
│   ├── articles/               # 24 статьи
│   ├── celi-obrashhenija/      # 22 цели обращения (услуги)
│   ├── deystviya-i-tarify/     # действия и тарифы
│   ├── kontakty/               # контакты (с формой)
│   ├── notarialnaya-kontora/   # о конторе
│   ├── pravovaya-informaciya/  # правовая информация
│   ├── fnc/                    # тарифы, реестры, льготы, согласия
│   ├── media/                  # картинки/SVG из контента
│   └── static/
│       ├── css/custom/contact-form.css     # стили формы (своё)
│       ├── js/custom/contact-form.js       # отправка в Google Form (своё)
│       └── html-snippets/contact-form.html # HTML формы (своё)
└── scripts/
    └── post-process.py         # пост-обработка после очередного зеркалирования
```

## Локальная разработка

Сайт собирается движком **Jekyll** (страницы используют Liquid-шаблоны,
`_layouts`, `_includes`, коллекцию `_articles`). Поэтому открыть `docs/`
обычным статическим сервером (`python3 -m http.server`) **нельзя** — вы увидите
необработанные шаблоны `{{ ... }}` без шапки/подвала. Нужен предпросмотр через
Jekyll — см. раздел [«Локальный предпросмотр»](#локальный-предпросмотр).

## Настройка формы обратной связи

Форма отправляет ответы в публичную Google Form через `POST` на `formResponse`.

> ✅ **Статус: настроено.** Форма подключена к Google Form
> `1FAIpQLSeQsqkfe-mDxsQUjPZmBHNcC86Zvhi9iSgarmP01OnqjKdu_Q`
> (https://docs.google.com/forms/d/e/1FAIpQLSeQsqkfe-mDxsQUjPZmBHNcC86Zvhi9iSgarmP01OnqjKdu_Q/viewform).
> ID формы и полей уже прописаны в `docs/static/js/custom/contact-form.js` (см. шаг 3).
> Инструкция ниже нужна, только если потребуется переподключить другую форму.

### 1. ✅ Создать Google Form

1. Открыть https://forms.google.com → создать новую форму.
2. Добавить поля:
   - **Имя** (короткий ответ)
   - **Телефон** (короткий ответ)
   - **Email** (короткий ответ)
   - **Цель обращения** (короткий ответ или раскрывающийся список с теми же значениями, что в `docs/static/html-snippets/contact-form.html`)
   - **Сообщение** (абзац)
3. Открыть **«Ответы» → таблица Google Sheets** — туда будут падать заявки.

### 2. ✅ Получить ID формы и полей

1. В редакторе формы нажми `⋮` (три точки сверху) → **«Получить ссылку для предзаполнения»**.
2. Заполни все поля любыми пробными значениями → **«Получить ссылку»**.
3. В скопированной ссылке ищи:
   - **ID формы** (между `/d/e/` и `/viewform`): `https://docs.google.com/forms/d/e/`**`1FAIpQLSe...`**`/viewform`
   - **ID каждого поля**: параметры `entry.123456789=значение`

### 3. ✅ Подставить значения в `docs/static/js/custom/contact-form.js`

Текущие (рабочие) значения:

```js
var GOOGLE_FORM_ID = '1FAIpQLSeQsqkfe-mDxsQUjPZmBHNcC86Zvhi9iSgarmP01OnqjKdu_Q';
var FIELDS = {
    name:    'entry.1604397642',
    phone:   'entry.1362560022',
    email:   'entry.1344492135',
    purpose: 'entry.1845173671',
    message: 'entry.1139492886'
};
```

### 4. Проверить

Заполнить форму на сайте → должна появиться запись в таблице Google Sheets.

> ⚠️ Из-за `mode: 'no-cors'` браузер не сможет прочитать ответ Google. Скрипт считает запрос успешным, если он не упал сетью. Главный способ проверки — таблица в Google Sheets.

## Обновление с оригинала

Если на `okolganov.ru` изменился контент:

```bash
rm -rf docs/articles docs/celi-obrashhenija docs/deystviya-i-tarify \
       docs/notarialnaya-kontora docs/pravovaya-informaciya docs/fnc \
       docs/media docs/index.html docs/kontakty
# скачать заново
wget --mirror --convert-links --adjust-extension --page-requisites \
     --no-parent -e robots=off --restrict-file-names=unix \
     --user-agent="Mozilla/5.0" --wait=0.3 --random-wait \
     --no-host-directories --domains=okolganov.ru \
     -P docs/ https://okolganov.ru/
# переименовать проблемный файл пагинации
mv 'docs/celi-obrashhenija/index.html?page=2.html' docs/celi-obrashhenija/page-2.html
grep -rl 'index.html%3Fpage=2.html' --include="*.html" docs/ \
  | xargs sed -i '' 's|index.html%3Fpage=2.html|page-2.html|g'
# применить пост-обработку (удалить блоки конструктора, вставить форму)
python3 scripts/post-process.py
```

## Движок: Jekyll (GitHub Pages)

Сайт собирается нативным для GitHub Pages движком **Jekyll** — самописная сборка
шапки/подвала Python-скриптами больше не используется.

Структура Jekyll (внутри `docs/`):

- `_config.yml` — конфигурация (`baseurl: /oleg-kolganov-langing`, коллекция статей).
- `_layouts/default.html` — общий каркас страницы: `<head>`, подключение
  `_includes/header.html` и `_includes/footer.html`, общие CSS/JS.
- `_includes/header.html`, `_includes/footer.html` — **единый источник** шапки и
  подвала. Пути собираются фильтром `{{ '/path' | relative_url }}` с учётом
  `baseurl`, активный пункт меню — по переменной `page.section`.
- `_articles/*.html` — статьи как коллекция (front matter + permalink, см. ниже).
- `_data/article_categories.yml` — категории и порядок их вывода на `/articles/`.

Каждая страница начинается с front matter (`layout`, `title`, `description`,
`section`, при необходимости `styles` / `head_scripts` / `body_scripts`).

> Менять шапку/подвал нужно в `_includes/header.html` / `_includes/footer.html`.
> Отдельные страницы трогать не нужно — общий каркас даёт layout.

### Локальный предпросмотр

> ⚠️ Каталог `.devcontainer/` к сайту отношения не имеет — это контейнер для
> запуска агента Claude Code (базовый образ Java + `claude-code`). Сам сайт в
> Docker’е не «стартует»: на проде его собирает GitHub Pages, а локально его
> нужно собрать движком Jekyll одним из способов ниже. Готовый сайт Jekyll
> кладёт в `docs/_site/` (этот каталог в `.gitignore`).

После запуска сервер слушает порт `4000`, но из-за `baseurl` сайт открывается по
адресу **http://localhost:4000/oleg-kolganov-langing/** (со слешем на конце).
Jekyll следит за файлами и пересобирает сайт при изменениях — достаточно обновить
страницу в браузере.

#### Вариант A — через Docker (рекомендуется, Ruby ставить не нужно)

Системный Ruby на macOS (2.6) слишком старый для гема `github-pages` (нужен
Ruby 3.x), поэтому проще всего поднять предпросмотр в контейнере с Ruby 3:

```bash
cd docs
docker run --rm -it \
  -v "$PWD":/srv -w /srv -p 4000:4000 \
  ruby:3.3 \
  sh -c "bundle install && bundle exec jekyll serve --host 0.0.0.0 --livereload"
```

Первый запуск дольше — контейнер скачивает образ и ставит гемы; повторные
быстрее. Остановить — `Ctrl+C`.

#### Вариант B — нативно (нужен Ruby 3.x, напр. через Homebrew или rbenv)

```bash
cd docs
bundle install
bundle exec jekyll serve --livereload
```

### Статьи (коллекция `_articles`)

Каждая статья — файл `docs/_articles/<slug>.html` с front matter: `title`,
`description`, `permalink` (сохраняет прежний URL `/articles/<slug>.html`),
`category` (slug из `_data/article_categories.yml`), `tag`, `card_title`,
`excerpt`, `order`. Список статей и фильтр по категориям на странице
`/articles/` строятся Liquid-ом по `site.articles` — вручную карточки добавлять
не нужно, достаточно создать новый файл в `_articles/`.

## Деплой на GitHub Pages

1. Создать репозиторий на GitHub.
2. Запушить репозиторий:

```bash
git init
git add .
git commit -m "Initial site"
git branch -M main
git remote add origin https://github.com/USER/REPO.git
git push -u origin main
```

3. **Settings → Pages → Source: `main` / folder: `/docs`** → Save.
4. Через 1–2 минуты сайт будет доступен по `https://USER.github.io/REPO/`.

### Кастомный домен

1. Купить домен (например `kolganov-notarius.ru`).
2. В DNS-настройках домена добавить:
   - 4 A-записи на корневой домен: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - CNAME `www` → `USER.github.io`
3. **Settings → Pages → Custom domain** → ввести домен.
4. Дождаться выдачи SSL (галочка «Enforce HTTPS»).

## Что отличается от оригинала

- Удалена кнопка «Версия для слабовидящих» (специфика конструктора).
- Удалена встроенная Vue-форма записи на приём (заменена нашей формой → Google Form).
- Все ссылки на ассеты сделаны абсолютными от корня (`/static/...`, `/media/...`), чтобы одинаково работать на всех уровнях вложенности.
- Добавлена кнопка «Задать вопрос» в навигации (якорь на форму).
- Owl-карусель в блоке «Нотариус поможет» заменена на CSS-сетку (стабильнее, без зависимостей).
- Hero-фон главной задаётся напрямую через CSS (раньше — через JS-плейсхолдер).
