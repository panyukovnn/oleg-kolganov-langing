/* Тарифы: кнопка «развернуть/свернуть всё» для аккордеонов <details>. */
(function () {
    'use strict';

    var nextPeriod = document.getElementById('tariff-next-period');
    var year = new URLSearchParams(location.search).get('year');
    if (nextPeriod && year !== '2026' && nextPeriod.dataset.clockUrl) {
        var effectiveAt = Date.parse(nextPeriod.dataset.effectiveFrom);
        var periodTimer, checkingPeriod = false;
        async function followCurrentPeriod() {
            if (checkingPeriod) { return; }
            checkingPeriod = true;
            window.clearTimeout(periodTimer);
            var delay = 30000;
            var started = performance.now();
            var controller = new AbortController();
            var timeout = window.setTimeout(function () { controller.abort(); }, 5000);
            try {
                var response = await fetch(nextPeriod.dataset.clockUrl, {
                    cache: 'no-store', credentials: 'omit', signal: controller.signal
                });
                if (response.ok) {
                    var clock = await response.json();
                    if (Number.isSafeInteger(clock.serverTime)) {
                        if (clock.tariffYear === 2027 && clock.serverTime >= effectiveAt) {
                            location.replace(nextPeriod.href + location.hash);
                            return;
                        }
                        if (clock.tariffYear === 2026 && clock.serverTime < effectiveAt) {
                            delay = Math.max(100, Math.min(3600000, effectiveAt - clock.serverTime - (performance.now() - started)));
                        }
                    }
                }
            } catch (error) {
                // The dated link remains available while the clock service is unreachable.
            } finally {
                window.clearTimeout(timeout);
                checkingPeriod = false;
            }
            periodTimer = window.setTimeout(followCurrentPeriod, delay);
        }
        followCurrentPeriod();
        window.addEventListener('online', followCurrentPeriod);
        window.addEventListener('pageshow', function (event) { if (event.persisted) { followCurrentPeriod(); } });
        document.addEventListener('visibilitychange', function () { if (!document.hidden) { followCurrentPeriod(); } });
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
