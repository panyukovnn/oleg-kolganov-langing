import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2), core=args[args.indexOf('--core')+1];
if(!args.includes('--core')||!core)throw Error('Usage: node scripts/sync-tariff-reference.mjs --core PATH [--check]');
const {loadCatalog}=await import(pathToFileURL(path.resolve(core,'src/catalog.js')));
const {searchDocument}=await import(pathToFileURL(path.resolve(core,'src/search.js')));
const catalog=await loadCatalog();
const master=JSON.parse(await fs.readFile(path.resolve(core,'data/Тарифы_2026_мастер.json'),'utf8'));
const edits=JSON.parse(await fs.readFile(path.join(repo,'maintenance/tariff-reference-editorial.json'),'utf8'));
const actions=catalog.actions.map(a=>Object.fromEntries(['id','number','section','title','federal','regional','legalBasis','notes'].map(k=>[k,a[k]??''])));
for(const e of edits){const a=actions.find(a=>a.id===e.id);if(!a||a[e.field]!==e.original)throw Error(`Re-review editorial change: ${e.id}.${e.field}`);a[e.field]=e.value;}
for(const a of actions)a.search=searchDocument(a);
const sourceHashes={};
for(const f of ['data/Тарифы_2026_мастер.json','data/benefit-applicability.json','src/catalog.js','src/calculator.js','src/utils.js','src/validation.js','src/search.js','shared/action-popularity.js','shared/matcap-share.js'])sourceHashes[f]=createHash('sha256').update(await fs.readFile(path.resolve(core,f))).digest('hex');
const sections=[];
for(const a of actions){let s=sections.find(s=>s.title===a.section);if(!s){s={id:'tariff-'+(sections.length<13?sections.length+1:sections.length+2),title:a.section,actions:[]};sections.push(s);}s.actions.push(a);}
const labels=['Одно действие для инвалида I группы','Одно действие для лица в СИЗО','Одно действие для одного лица: остальные случаи','Несколько действий для одного лица','Несколько действий для членов одной семьи','Одно действие для нескольких лиц','Несколько действий для нескольких юридических лиц и/или их сотрудников по одному адресу'];
const money=n=>Number(n).toLocaleString('ru-RU')+' руб.';
const expectedCases=['one_action_one_person_disability_I','one_action_one_person_in_sizo','one_action_one_person_other','several_actions_one_person','several_actions_one_family','one_action_several_persons','several_actions_several_legal_entities_or_employees'];
if(JSON.stringify(master.outcall.rates.map(r=>r.case))!==JSON.stringify(expectedCases))throw Error('Review changed outcall categories');
if(master.outcall.rates[3].rub_per_hour!=='2000_or_6000_by_person_case'||master.outcall.time_rules.billing_unit!=='hour'||master.outcall.time_rules.partial_hour!=='round_up_to_full_hour')throw Error('Review changed outcall time rules');
const outcall=master.outcall.rates.map((r,i)=>({label:labels[i],rate:typeof r.rub_per_hour==='number'?money(r.rub_per_hour):r.first_person_rub_per_hour?money(r.first_person_rub_per_hour)+' за первого + '+money(r.each_additional_person_rub_per_hour)+' за каждого следующего':'2 000 или 6 000 руб. в зависимости от категории лица',note:r.minimum_rub_per_person?'Не менее '+money(r.minimum_rub_per_person)+' с каждого лица':r.if_any_disability_I_rub_per_hour?'Если хотя бы одно лицо — инвалид I группы: '+money(r.if_any_disability_I_rub_per_hour):''}));
const output=JSON.stringify({version:catalog.meta.schemaVersion,period:catalog.meta.effectivePeriod,sourceHashes,sections,outcall,timeRules:master.outcall.time_rules,federalMultiplier:master.outcall.federal_multiplier},null,2)+'\n';
const dest=path.join(repo,'docs/_data/tariff_reference.json');
if(args.includes('--check')){if((await fs.readFile(dest,'utf8')).replace(/\r\n/g,'\n')!==output)throw Error('Tariff reference is stale; regenerate and review.');console.log(`OK: ${actions.length} actions match canonical source and reviewed editorial changes.`);}else{await fs.writeFile(dest,output);console.log(`Exported ${actions.length} actions.`);}
