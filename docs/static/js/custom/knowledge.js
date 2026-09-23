(()=>{'use strict';
const tools=document.querySelector('.kb-tools');
if(tools){
  tools.hidden=false;
  tools.querySelector('[data-kb-print]').addEventListener('click',()=>window.print());
  tools.querySelector('[data-kb-copy]').addEventListener('click',async()=>{
    const status=tools.querySelector('.kb-tool-status'),fallback=tools.querySelector('.kb-copy-fallback');
    const url=new URL(location.href);url.search='';
    fallback.hidden=true;
    try{if(!navigator.clipboard?.writeText)throw Error('unavailable');await navigator.clipboard.writeText(url.href);status.textContent='Ссылка скопирована.';}
    catch{status.textContent='Выделенная ссылка готова для копирования.';fallback.hidden=false;const field=fallback.querySelector('input');field.value=url.href;field.focus();field.select();}
  });
}
document.querySelectorAll('.kb-prose table').forEach(table=>{const wrap=document.createElement('div');wrap.className='kb-table-scroll';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Таблица, доступна горизонтальная прокрутка');table.before(wrap);wrap.append(table)});
if(matchMedia('(max-width:760px)').matches)document.querySelectorAll('.kb-toc').forEach(x=>x.open=false);
const input=document.querySelector('#kb-query');if(!input)return;
const norm=s=>s.toLowerCase().replace(/ё/g,'е').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const cards=[...document.querySelectorAll('.kb-card')],box=document.querySelector('#kb-results'),count=document.querySelector('#kb-count'),reset=document.querySelector('#kb-reset'),empty=document.querySelector('#kb-empty'),sections=document.querySelector('#kb-sections'),groups=[...document.querySelectorAll('.kb-group')];
let data=new Map(),topic='all';
function saveUrl(){const url=new URL(location.href);input.value.trim()?url.searchParams.set('q',input.value.trim()):url.searchParams.delete('q');topic!=='all'?url.searchParams.set('topic',topic):url.searchParams.delete('topic');history.replaceState(null,'',url)}
function apply(push=false){
 const query=norm(input.value),words=query.split(' ').filter(Boolean);let visible=0;
 sections.hidden=!!query;box.hidden=!query;
 const ranked=cards.map((card,i)=>{const item=data.get(card.dataset.slug),title=norm(card.querySelector('h3').textContent),aliases=norm(item?[item.query,...item.synonyms].join(' '):''),body=norm(item?.text||card.textContent);const score=!words.length?1:(title.includes(query)?100:aliases.includes(query)?90:words.every(w=>(title+' '+aliases).includes(w))?70:words.every(w=>body.includes(w))?10:0);const show=!query||((topic==='all'||card.dataset.category===topic)&&score>0);card.hidden=!show;if(show)visible++;return{card,score,i}});
 if(query){ranked.sort((a,b)=>b.score-a.score||a.i-b.i).forEach(x=>box.append(x.card))}
 else{cards.forEach(card=>groups.find(g=>g.dataset.topic===card.dataset.category).querySelector('.kb-group-items').append(card));groups.forEach(g=>g.open=g.dataset.topic===topic)}
 count.textContent=query?'Найдено материалов: '+visible:'Откройте нужный раздел или найдите статью по вопросу.';
 empty.hidden=!query||!!visible;reset.hidden=!query&&topic==='all';if(push)saveUrl();
}
function restore(){const p=new URLSearchParams(location.search);input.value=p.get('q')||'';const t=p.get('topic');topic=groups.some(g=>g.dataset.topic===t)?t:'all';apply()}
// Native toggle events are queued: using them to close other groups can
// let an earlier event override the reader's most recent activation.
// Handle summary activation synchronously; details still works without JS.
groups.forEach(group=>group.querySelector('summary').addEventListener('click',event=>{
 event.preventDefault();
 topic=group.open?'all':group.dataset.topic;
 groups.forEach(g=>g.open=g.dataset.topic===topic);
 reset.hidden=topic==='all'&&!input.value.trim();saveUrl();
}));
document.querySelector('.kb-search').addEventListener('submit',e=>{e.preventDefault();topic='all';apply(true)});
input.addEventListener('input',()=>{topic='all';apply(true)});
reset.addEventListener('click',()=>{input.value='';topic='all';apply(true);document.querySelector('#kb-topics-title').focus()});
window.addEventListener('popstate',restore);restore();
fetch('/articles/search.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(items=>{data=new Map(items.map(x=>[x.slug,x]));if(norm(input.value))apply()}).catch(()=>{if(input.value.trim())count.textContent+=' · Поиск доступен по заголовкам и описаниям.'});
})();