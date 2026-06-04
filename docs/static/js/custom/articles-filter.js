// Простая клиентская фильтрация статей по категории (без зависимостей).
(function () {
    var filter = document.querySelector('.kn-art-filter');
    if (!filter) return;

    var buttons = filter.querySelectorAll('.kn-art-filter__btn');
    var groups = document.querySelectorAll('.kn-art-group');

    filter.addEventListener('click', function (e) {
        var btn = e.target.closest('.kn-art-filter__btn');
        if (!btn) return;

        var cat = btn.getAttribute('data-filter');

        buttons.forEach(function (b) {
            b.classList.toggle('kn-art-filter__btn--active', b === btn);
        });

        groups.forEach(function (g) {
            var show = cat === 'all' || g.getAttribute('data-cat') === cat;
            g.classList.toggle('is-hidden', !show);
        });
    });
})();
