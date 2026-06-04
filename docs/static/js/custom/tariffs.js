/* Тарифы: кнопка «развернуть/свернуть всё» для аккордеонов <details>. */
(function () {
    'use strict';

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
        var target = document.querySelector(location.hash);
        if (target && target.classList.contains('kn-tariff-group')) {
            target.open = true;
            syncLabel();
        }
    }
    window.addEventListener('hashchange', openFromHash);

    openFromHash();
    syncLabel();
})();
