(function () {
    'use strict';
    var notices = document.querySelectorAll('meta[name="office-hours-notice"]');
    if (!notices.length) return;
    var style = document.createElement('style');
    document.head.appendChild(style);
    var timer;
    function update() {
        window.clearTimeout(timer);
        var now = Date.now();
        var next = Infinity;
        var rules = [];
        notices.forEach(function (notice) {
            var id = notice.getAttribute('data-id');
            if (!/^[a-f0-9]{64}$/.test(id || '')) return;
            var startsAt = Date.parse(notice.getAttribute('data-from'));
            var endsAt = Date.parse(notice.getAttribute('data-until'));
            var valid = Number.isFinite(startsAt) && Number.isFinite(endsAt) && startsAt < endsAt;
            var active = valid && startsAt <= now && now < endsAt;
            rules.push('.kn-schedule-notice[data-notice-id="' + id + '"]{display:' + (active ? 'block' : 'none') + '}');
            if (valid && now < endsAt) next = Math.min(next, now < startsAt ? startsAt : endsAt);
        });
        style.textContent = rules.join('\n');
        if (Number.isFinite(next)) timer = window.setTimeout(update, Math.min(next - now, 2147483647));
    }
    update();
    window.addEventListener('pageshow', update);
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) update();
    });
})();
