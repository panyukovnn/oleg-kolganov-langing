/**
 * Автоскрытие шапки при скролле.
 *
 * При прокрутке вниз сайту добавляется класс `.kn-header--hidden`
 * (шапка уезжает вверх через transform: translateY(-100%)), при прокрутке
 * вверх класс убирается и шапка снова показывается. У самого верха страницы
 * шапка всегда видна (порог TOP_THRESHOLD). Когда открыто боковое меню
 * (`body.kn-menu-open`, TASK-23) — шапку не прячем.
 */
(function () {
    var header = document.querySelector('.kn-header');
    var body = document.body;

    if (!header) {
        return;
    }

    // Порог у верха страницы: ближе этого значения шапку не скрываем.
    var TOP_THRESHOLD = 80;
    // Минимальное смещение скролла, после которого реагируем (защита от дрожания).
    var DELTA = 6;

    var lastScroll = window.pageYOffset || document.documentElement.scrollTop || 0;
    var ticking = false;

    function update() {
        ticking = false;

        var current = window.pageYOffset || document.documentElement.scrollTop || 0;

        // При открытом боковом меню ничего не трогаем (drawer из TASK-23).
        if (body.classList.contains('kn-menu-open')) {
            lastScroll = current;
            return;
        }

        // У верха страницы шапка всегда видна.
        if (current <= TOP_THRESHOLD) {
            header.classList.remove('kn-header--hidden');
            lastScroll = current;
            return;
        }

        var diff = current - lastScroll;

        if (Math.abs(diff) < DELTA) {
            return;
        }

        if (diff > 0) {
            // Скролл вниз — прячем.
            header.classList.add('kn-header--hidden');
        } else {
            // Скролл вверх — показываем.
            header.classList.remove('kn-header--hidden');
        }

        lastScroll = current;
    }

    function onScroll() {
        if (!ticking) {
            window.requestAnimationFrame(update);
            ticking = true;
        }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
})();
