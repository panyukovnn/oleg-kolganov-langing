/* Тарифы: кнопка «развернуть/свернуть всё» для аккордеонов <details>. */
(function () {
    'use strict';

    var nextPeriod = document.getElementById('tariff-next-period');
    var year = new URLSearchParams(location.search).get('year');
    if (nextPeriod && year !== '2026') {
        var effectiveAt = Date.parse(nextPeriod.dataset.effectiveFrom);
        var periodTimer;
        function followCurrentPeriod() {
            window.clearTimeout(periodTimer);
            var remaining = effectiveAt - Date.now();
            if (remaining <= 0) {
                location.replace(nextPeriod.href + location.hash);
                return;
            }
            periodTimer = window.setTimeout(followCurrentPeriod, Math.min(remaining, 2147483647));
        }
        followCurrentPeriod();
        window.addEventListener('pageshow', followCurrentPeriod);
    }

    var toggleBtn = document.querySelector('.kn-tariff-toggle-all');
    var groups = Array.prototype.slice.call(document.querySelectorAll('.kn-tariff-group'));
    if (!toggleBtn || !groups.length) {
        return;
    }

    var EXPAND = 'Развернуть все';
    var COLLAPSE = 'Свернуть все';

    function allOpen() {
        return groups.every(function (g) { return g.open; });
    }

    function syncLabel() {
        toggleBtn.textContent = allOpen() ? COLLAPSE : EXPAND;
    }

    toggleBtn.addEventListener('click', function () {
        var open = !allOpen();
        groups.forEach(function (g) { g.open = open; });
        syncLabel();
    });

    // Если пользователь раскрывает/сворачивает группы вручную — обновляем подпись кнопки
    groups.forEach(function (g) {
        g.addEventListener('toggle', syncLabel);
    });

    // При переходе по якорю из оглавления — раскрыть нужную группу
    function openFromHash() {
        if (!location.hash) { return; }
        var target = document.getElementById(location.hash.slice(1));
        if (target && target.classList.contains('kn-tariff-group')) {
            target.open = true;
            syncLabel();
        }
    }
    window.addEventListener('hashchange', openFromHash);

    openFromHash();
    syncLabel();
})();
