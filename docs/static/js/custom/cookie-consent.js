/**
 * Уведомление об использовании cookie.
 *
 * Баннер в разметке скрыт по умолчанию (атрибут hidden). Скрипт показывает его
 * только тем, кто ещё не нажал «Принять», — чтобы у согласившихся не было мигания.
 * Факт согласия запоминается в localStorage и больше не показывается.
 */
(function () {
    var KEY = 'kn-cookie-consent';
    var banner = document.getElementById('kn-cookie');
    if (!banner) {
        return;
    }

    try {
        if (localStorage.getItem(KEY)) {
            return; // уже принято — баннер не показываем
        }
    } catch (e) {
        // localStorage недоступен (приватный режим и т. п.) — просто покажем баннер
    }

    banner.hidden = false;

    var accept = document.getElementById('kn-cookie-accept');
    if (accept) {
        accept.addEventListener('click', function () {
            try {
                localStorage.setItem(KEY, '1');
            } catch (e) {
                // не удалось сохранить — всё равно скрываем на текущей сессии
            }
            banner.hidden = true;
        });
    }
})();
