(() => {
  'use strict';
  const root = document.querySelector('#tariff-reference');
  if (!root) return;
  const input = root.querySelector('#nt-query');
  const actions = [...root.querySelectorAll('.nt-action')];
  const groups = [...root.querySelectorAll('.nt-category')];
  const status = root.querySelector('#nt-results');
  const normalize = text => text.toLocaleLowerCase('ru').replace(/ё/g, 'е').replace(/[^a-zа-я0-9]+/gi, ' ');
  const search = () => {
    const words = normalize(input.value).trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const action of actions) {
      action.hidden = !words.every(word => normalize(action.dataset.search).includes(word));
      if (!action.hidden) count++;
    }
    for (const group of groups) {
      group.hidden = ![...group.querySelectorAll('.nt-action')].some(a => !a.hidden);
      if (words.length && !group.hidden) group.open = true;
    }
    root.querySelector('.nt-empty').hidden = count > 0;
    root.querySelector('.nt-nav').hidden = words.length > 0;
    status.textContent = words.length ? `Найдено действий: ${count} из ${actions.length}` : `В справочнике ${actions.length} действий`;
  };
  const openHash = () => {
    let id; try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !root.contains(target)) return;
    if (target.matches('.nt-category,.nt-action')) {
      input.value = ''; search();
      const group = target.closest('.nt-category');
      if (group) group.open = true;
      requestAnimationFrame(() => target.scrollIntoView({block:'start'}));
    }
  };
  input.addEventListener('input', search);
  root.querySelector('#nt-clear').addEventListener('click', () => { input.value = ''; search(); input.focus(); });
  window.addEventListener('hashchange', openHash);
  root.querySelector('.nt-nav').addEventListener('click', event => { if (event.target.closest('a')?.hash === location.hash) openHash(); });
  root.querySelector('.nt-tools').hidden = false;
  search(); openHash();
})();
