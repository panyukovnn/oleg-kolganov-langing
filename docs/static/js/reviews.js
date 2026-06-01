/* Карусель отзывов (только 5★). Vanilla JS, без зависимостей.
   Прогрессивное улучшение: данные берутся из static/data/reviews.json. */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', init);

    function init() {
        var root = document.querySelector('.lx-reviews');
        if (!root) return;

        var track = root.querySelector('.lx-reviews__track');
        var tpl = document.getElementById('lx-review-tpl');
        var prev = root.querySelector('.lx-reviews__nav--prev');
        var next = root.querySelector('.lx-reviews__nav--next');
        if (!track || !tpl) return;

        var url = track.getAttribute('data-src') || 'static/data/reviews.json';

        fetch(url)
            .then(function (r) { return r.ok ? r.json() : []; })
            .then(function (data) {
                var items = (Array.isArray(data) ? data : []).filter(function (r) {
                    return Number(r.rating) === 5; // защитный фильтр: только пятёрки
                });
                if (!items.length) { root.style.display = 'none'; return; }
                items.forEach(function (r) { track.appendChild(buildCard(r, tpl)); });
                wireNav(track, prev, next);
            })
            .catch(function () { root.style.display = 'none'; });
    }

    function buildCard(r, tpl) {
        var node = tpl.content.firstElementChild.cloneNode(true);

        var name = String(r.name || '').trim() || 'Аноним';
        var avatar = node.querySelector('.lx-review__avatar');
        avatar.textContent = name.charAt(0).toUpperCase();
        avatar.style.setProperty('--avatar-bg', colorFromName(name));

        node.querySelector('.lx-review__name').textContent = name;
        node.querySelector('.lx-review__meta').textContent =
            'Источник: ' + (r.source || 'Яндекс.Карты') + ' · ' + formatDate(r.date);

        var textEl = node.querySelector('.lx-review__text');
        textEl.textContent = String(r.text || ''); // textContent — без инъекций

        var more = node.querySelector('.lx-review__more');
        // Кнопка «ещё» нужна, только если текст реально обрезается
        requestAnimationFrame(function () {
            if (textEl.scrollHeight - textEl.clientHeight > 4) {
                more.hidden = false;
            }
        });
        more.addEventListener('click', function () {
            var expanded = textEl.classList.toggle('lx-review__text--expanded');
            more.setAttribute('aria-expanded', String(expanded));
            more.textContent = expanded ? 'свернуть' : 'ещё';
        });

        return node;
    }

    function wireNav(track, prev, next) {
        function step() {
            var card = track.querySelector('.lx-review');
            var gap = 24;
            return card ? card.getBoundingClientRect().width + gap : track.clientWidth;
        }
        if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
        if (next) next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });

        // Стрелки клавиатуры, когда фокус на ленте
        track.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowRight') { e.preventDefault(); track.scrollBy({ left: step(), behavior: 'smooth' }); }
            if (e.key === 'ArrowLeft') { e.preventDefault(); track.scrollBy({ left: -step(), behavior: 'smooth' }); }
        });
    }

    function formatDate(iso) {
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
        if (!m) return String(iso || '');
        return m[3] + '.' + m[2] + '.' + m[1];
    }

    // Детерминированный цвет аватара из имени (hash → HSL)
    function colorFromName(name) {
        var h = 0;
        for (var i = 0; i < name.length; i++) {
            h = (h * 31 + name.charCodeAt(i)) % 360;
        }
        return 'hsl(' + h + ', 45%, 45%)';
    }
})();
