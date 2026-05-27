// Safety net: переинициализирует Owl-карусели, если main.min.js по какой-то
// причине не дошёл до setupCarousels (например, упал ранее на чём-то конкретном).
(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    function tryInit() {
        if (typeof window.jQuery === 'undefined') return false;
        var $ = window.jQuery;
        if (typeof $.fn.owlCarousel !== 'function') return false;

        var inits = [
            { sel: '.notary-help-carousel', opts: { loop: false, margin: 10, nav: true, items: 1 } },
            {
                sel: '.main-carusel',
                opts: {
                    loop: false, margin: 30, dotsEach: true, dots: true, nav: true,
                    responsive: { 0: { items: 1 }, 512: { items: 2 }, 768: { items: 3 }, 1024: { items: 4 } }
                }
            },
            {
                sel: '.main-advantages-slider .advantage--container .advantage__content',
                opts: {
                    loop: false, margin: 0, dotsEach: true, dots: true, nav: true,
                    responsive: { 0: { items: 2 }, 768: { items: 3 }, 1000: { items: 2 }, 1380: { items: 3 } }
                }
            }
        ];

        inits.forEach(function (cfg) {
            $(cfg.sel).each(function () {
                var $el = $(this);
                if ($el.hasClass('owl-loaded')) return;
                // Для main-advantages-slider убедимся, что родителю добавлен класс owl-carousel
                if (cfg.sel.indexOf('main-advantages-slider') !== -1 && !$el.hasClass('owl-carousel')) {
                    $el.addClass('owl-carousel');
                }
                try {
                    $el.owlCarousel(cfg.opts);
                } catch (e) {
                    console.warn('[carousel-fallback] init failed for', cfg.sel, e);
                }
            });
        });
        return true;
    }

    ready(function () {
        // Дать шанс main.min.js: пробуем через 600 мс, потом ещё раз через 1500 мс
        setTimeout(tryInit, 600);
        setTimeout(tryInit, 1500);
    });
})();
