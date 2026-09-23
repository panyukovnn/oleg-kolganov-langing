import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const data=JSON.parse(await fs.readFile(new URL('../docs/_data/tariff_reference.json',import.meta.url),'utf8'));
const actions=data.sections.flatMap(s=>s.actions);
const get=n=>actions.find(a=>a.number===n);
test('complete catalog, stable category and action links',()=>{
 assert.equal(actions.length,88);assert.equal(new Set(actions.map(a=>a.id)).size,88);
 assert.deepEqual(actions.map(a=>a.number),Array.from({length:88},(_,i)=>i+1));
 for(let n=1;n<=13;n++)assert.ok(data.sections.some(s=>s.id===`tariff-${n}`));
 for(const a of actions)for(const field of ['title','federal','regional','legalBasis','search'])assert.ok(a[field]?.trim(),`${a.id}.${field}`);
});
test('corrected federal scales and separate regional amounts',()=>{
 assert.match(get(8).federal,/0,15%/);assert.match(get(9).federal,/0,15%/);
 assert.equal(get(31).federal,'500 руб.');
 for(const n of [8,9,30,31])assert.doesNotMatch(get(n).regional,/%/);
 assert.equal(get(8).regional.split('\n').length,3);assert.equal(get(9).regional.split('\n').length,3);
 assert.match(get(42).notes,/за них не взимается/);assert.match(get(65).notes,/100%/);
});
test('common public search words have results',()=>{
 for(const q of ['доверенность','наследство','дарственная','маткапитал','копия','осмотр сайта'])assert.ok(actions.some(a=>q.split(' ').every(w=>a.search.includes(w))),q);
});
test('public projection contains no calculator execution or internal fields',()=>{
 for(const a of actions)assert.deepEqual(Object.keys(a).sort(),['id','number','section','title','federal','regional','legalBasis','notes','search'].sort());
 assert.equal(data.outcall.length,7);
 assert.ok(Object.values(data.sourceHashes).every(hash=>/^[a-f0-9]{64}$/.test(hash)));
});
