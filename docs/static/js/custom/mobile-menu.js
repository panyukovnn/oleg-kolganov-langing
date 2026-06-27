/**
 * Мобильное боковое меню (off-canvas drawer).
 *
 * Бургер открывает/закрывает выезжающую сбоку панель навигации, показывает
 * затемняющий оверлей и блокирует прокрутку фона. Пункты с подменю
 * («Нотариальные действия», «Связаться») раскрываются по тапу на стрелку
 * (аккордеон). Меню закрывается по тапу на оверлей, крестик, Escape и при
 * переходе по обычной ссылке.
 */
(function () {
    var body = document.body;
    var burger = document.querySelector('.kn-burger');
    var nav = document.getElementById('kn-mainnav');
    var overlay = document.querySelector('.kn-nav-overlay');

    if (!burger || !nav) {
        return;
    }

    function openMenu() {
        body.classList.add('kn-menu-open');
        burger.setAttribute('aria-expanded', 'true');
    }

    function closeMenu() {
        body.classList.remove('kn-menu-open');
        burger.setAttribute('aria-expanded', 'false');
    }

    function toggleMenu() {
        if (body.classList.contains('kn-menu-open')) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    burger.addEventListener('click', toggleMenu);

    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }

    var closeBtn = nav.querySelector('.kn-nav__close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMenu);
    }

    // Раскрытие/сворачивание подменю (по стрелке и по заголовку-кнопке «Связаться»)
    var subToggles = nav.querySelectorAll('.kn-nav__toggle, .kn-nav__sublabel');
    Array.prototype.forEach.call(subToggles, function (toggle) {
        toggle.addEventListener('click', function (event) {
            event.preventDefault();
            var item = toggle.closest('.kn-nav__item--has-sub');
            if (!item) {
                return;
            }
            var isOpen = item.classList.toggle('kn-nav__item--open');
            var chevron = item.querySelector('.kn-nav__toggle');
            if (chevron) {
                chevron.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            }
        });
    });

    // Переход по обычной ссылке закрывает меню (кнопка-заголовок «Связаться» — не ссылка)
    nav.addEventListener('click', function (event) {
        var link = event.target.closest('a');
        if (link) {
            closeMenu();
        }
    });

    // Закрытие по Escape
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' || event.key === 'Esc') {
            closeMenu();
        }
    });
})();
