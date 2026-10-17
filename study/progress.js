/* Shared by the study hub and the original C-Test page. No network or account required. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.StudyProgress=api;})(typeof window==='undefined'?globalThis:window,function(){
'use strict';
const KEY='taebin-toefl-study-v2',LEGACY='taebin-toefl-restored-attempts-v1';
const validId=id=>typeof id==='string'&&/^(?:TPO[234]-[RL]\d+|DRILL-\d{2}|CTEST-\d{2}|TRANSFER-\d{2})$/.test(id);
const validCode=c=>/^(?:V[1-9]|G[1-9]|M[1-8]|L[1-7]|P[1-6]|D[1-8]|A[1-6]|T[1-5]|LI(?:[1-9]|1[0-2]))$/.test(c);
const courseOf=id=>id.startsWith('CTEST-')?'ctest':id.startsWith('DRILL-')?'correction':id.startsWith('TRANSFER-')?'transfer':'original';
const blank=()=>({version:3,attempts:[],drafts:{},cursors:{},resume:null,analyses:{},analysisVersions:[],vocabOverrides:{},vocabReviews:[],customVocab:{},testNotes:{}});
const uid=()=>typeof crypto!=='undefined'&&crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random().toString(36).slice(2);
function normalize(raw){
 const s=blank(),rows=Array.isArray(raw)?raw:raw?.attempts||raw?.records;
 if(!Array.isArray(rows)||rows.length>50000)throw Error('올바른 학습 기록 파일이 아닙니다.');
 for(const r of rows){
  if(!r||!validId(r.id)||typeof r.correct!=='boolean'||!Number.isFinite(Date.parse(r.time)))throw Error('문항 또는 시각을 확인할 수 없는 기록이 있습니다.');
  const time=new Date(r.time).toISOString(),course=courseOf(r.id);
  s.attempts.push({...r,uid:r.uid||[r.id,time,String(r.answer)].join('|'),course,time});
 }
 const bad=()=>{throw Error('진단·어휘 데이터 형식을 확인할 수 없습니다. 기존 기록은 변경하지 않았습니다.');};
 for(const [key,a]of Object.entries(raw?.analyses||{}))if(!validId(key)||a.id!==key||(!validCode(a.primary)&&a.primary!=='unknown')||typeof a.correctionRule!=='string'||typeof a.ruleId!=='string')bad();
 for(const field of ['vocabOverrides','customVocab'])for(const [key,v]of Object.entries(raw?.[field]||{})){if(!/^VOC-/.test(key)||!v||typeof v!=='object')bad();for(const f of ['term','meaning','contextMeaning','issue','originalSentence','pos','confusedWith','synonyms','collocations','wordFamily'])if(v[f]!=null&&typeof v[f]!=='string')bad();if(field==='customVocab'&&(v.id!==key||typeof v.term!=='string'))bad();if(v.questionIds!=null&&(!Array.isArray(v.questionIds)||!v.questionIds.every(validId)))bad();if(v.sources!=null&&!Array.isArray(v.sources))bad();}
 if(raw?.vocabReviews!=null&&(!Array.isArray(raw.vocabReviews)||raw.vocabReviews.some(r=>!r||typeof r.id!=='string'||!r.id.startsWith('VOC-')||!['known','uncertain','unknown'].includes(r.result))))bad();
 for(const field of ['analyses','vocabOverrides','customVocab','testNotes'])for(const [key,value]of Object.entries(raw?.[field]||{}))if(key!=='__proto__'&&key!=='constructor'&&value&&typeof value==='object')s[field][key]={...value};
 for(const field of ['analysisVersions','vocabReviews'])if(Array.isArray(raw?.[field]))s[field]=raw[field].filter(x=>x&&typeof x.uid==='string'&&Number.isFinite(Date.parse(x.time)));
 if(typeof raw?.recoveryRaw==='string')s.recoveryRaw=raw.recoveryRaw;
 for(const [id,d] of Object.entries(raw?.drafts||{}))if(validId(id)&&d&&typeof d==='object')s.drafts[id]={...d};
 for(const [c,id] of Object.entries(raw?.cursors||{}))if(['ctest','original','correction','transfer'].includes(c)&&validId(id)&&courseOf(id)===c)s.cursors[c]=id;
 if(raw?.resume&&validId(raw.resume.id))s.resume={...raw.resume,course:courseOf(raw.resume.id)};
 return s;
}
function create(storage,onError=()=>{}){
 let state=blank(),recoveryRaw=null;
 try{const saved=storage.getItem(KEY),old=storage.getItem(LEGACY);recoveryRaw=saved||old;if(saved)state=normalize(JSON.parse(saved));else if(old)state=normalize(JSON.parse(old));}catch{state.recoveryRaw=recoveryRaw;onError('이전 기록을 읽지 못했습니다. 복구용 원값을 백업에 보존했습니다. 학습 기록에서 백업을 내려받아 주세요.');}
 const persist=()=>{try{storage.setItem(KEY,JSON.stringify(state));return true;}catch{onError('기록을 저장하지 못했습니다. 학습 기록에서 백업 파일을 내려받아 주세요.');return false;}};
 const latest=id=>state.attempts.filter(r=>r.id===id).at(-1);
 const needsReview=id=>{const r=latest(id);return !!r&&(!r.correct||r.hinted||r.uncertain||r.confidence==='guess'||r.confidence!=null&&Number(r.confidence)<=2||r.posCorrect===false);};
 const status=id=>state.drafts[id]&&!state.drafts[id].checked?'진행 중':!latest(id)?'아직 안 품':needsReview(id)?'다시 확인':'풀이 완료';
 const next=(ids,after)=>{const start=ids.indexOf(after)+1,ordered=[...ids.slice(start),...ids.slice(0,start)];return ordered.find(id=>!latest(id))||null;};
 function touch(id){const course=courseOf(id);state.cursors[course]=id;state.resume={id,course,time:new Date().toISOString()};persist();}
 function draft(id,value){if(!validId(id))return;state.drafts[id]={...value,updatedAt:new Date().toISOString()};touch(id);}
 function add(value){
  if(!validId(value.id))throw Error('문항 식별자가 올바르지 않습니다.');
  const previous=latest(value.id),weak=!value.correct||value.hinted||value.uncertain||value.confidence!=null&&Number(value.confidence)<=2||value.posCorrect===false;
  const streak=weak?0:(previous?.streak||0)+1,days=weak?1:[1,3,7,14][Math.min(streak-1,3)];
  const snapshot=value.analysisSnapshot||state.analyses[value.id]||null;
  const record={...value,analysisSnapshot:snapshot?JSON.parse(JSON.stringify(snapshot)):null,uid:uid(),course:courseOf(value.id),time:new Date().toISOString(),updatedAt:new Date().toISOString(),streak,dueAt:new Date(Date.now()+days*86400000).toISOString()};
  state.attempts.push(record);if(record.course==='ctest')for(const [index,result]of (record.results||[]).entries())if(!result.correct){const vid=Object.keys(state.customVocab).find(id=>state.customVocab[id].term?.toLowerCase()===result.word.toLowerCase())||'VOC-CTEST-'+result.word.toLowerCase().replace(/[^a-z0-9]+/g,'-');if(state.customVocab[vid]){const v=state.customVocab[vid];v.questionIds=[...new Set([...(v.questionIds||[]),record.id])];if(!v.sources.some(s=>s.test===record.id))v.sources.push({test:record.id,source:record.id+' 빈칸 '+(index+1)});v.updatedAt=record.time;}else state.customVocab[vid]={id:vid,term:result.word,meaning:result.meaning||'',contextMeaning:result.meaning||'',questionIds:[record.id],originalSentence:result.sourceSentence||'',issue:'C-Test에서 복원에 실패한 단어. 뜻을 몰랐는지는 별도 확인 필요.',learnerStatus:'practice_error',sources:[{test:'C-Test',source:record.id+' 빈칸 '+(index+1)}],linkStatus:'observed_error',updatedAt:record.time};}delete state.drafts[value.id];touch(value.id);return record;
 }
 function advance(ids,id){const upcoming=next(ids,id);state.cursors[courseOf(id)]=upcoming||id;state.resume={id:upcoming||id,course:courseOf(id),time:new Date().toISOString()};persist();return upcoming;}
 function due(id,now=Date.now()){const r=latest(id);return !!r&&!!r.dueAt&&Date.parse(r.dueAt)<=now;}
 function merge(raw){const incoming=normalize(raw),seen=new Set(state.attempts.map(r=>r.uid));let added=0;for(const r of incoming.attempts){if(!seen.has(r.uid)){state.attempts.push(r);seen.add(r.uid);added++;}else{const index=state.attempts.findIndex(a=>a.uid===r.uid),old=state.attempts[index];if(Date.parse(r.updatedAt||r.assessment?.time||r.time)>Date.parse(old.updatedAt||old.assessment?.time||old.time))state.attempts[index]=r;}}state.attempts.sort((a,b)=>Date.parse(a.time)-Date.parse(b.time));for(const field of ['analyses','vocabOverrides','customVocab','testNotes'])for(const [key,value]of Object.entries(incoming[field]))if(!state[field][key]||Date.parse(value.updatedAt||0)>Date.parse(state[field][key].updatedAt||0))state[field][key]=value;for(const field of ['analysisVersions','vocabReviews']){const ids=new Set(state[field].map(v=>v.uid));for(const v of incoming[field])if(!ids.has(v.uid)){state[field].push(v);ids.add(v.uid);}state[field].sort((a,b)=>Date.parse(a.time)-Date.parse(b.time));}for(const[id,d]of Object.entries(incoming.drafts))if(!state.drafts[id]||Date.parse(d.updatedAt)>Date.parse(state.drafts[id].updatedAt))state.drafts[id]=d;if(incoming.resume&&(!state.resume||Date.parse(incoming.resume.time)>Date.parse(state.resume.time))){state.resume=incoming.resume;state.cursors={...state.cursors,...incoming.cursors};}persist();return added;}
 function uncertain(id,value){const r=latest(id);if(r){r.uncertain=value;if(value&&r.assessment?.outcome==='resolved')r.assessment={...r.assessment,outcome:'unknown',time:new Date().toISOString()};r.updatedAt=new Date().toISOString();const earlier=state.attempts.filter(a=>a.id===id&&a.uid!==r.uid).at(-1);const weak=value||!r.correct||r.hinted||r.posCorrect===false||r.confidence!=null&&Number(r.confidence)<=2;r.streak=weak?0:(earlier?.streak||0)+1;const days=weak?1:[1,3,7,14][Math.min(r.streak-1,3)];r.dueAt=new Date(Date.now()+days*86400000).toISOString();persist();}}
 function reload(){try{const raw=storage.getItem(KEY);if(raw)state=normalize(JSON.parse(raw));}catch{}}
 function saveAnalysis(id,value){if(!validId(id))throw Error('문항을 확인할 수 없습니다.');if((!validCode(value.primary)&&value.primary!=='unknown')||(value.primary!=='unknown'&&!value.correctionRule?.trim()))throw Error('가장 큰 원인과 다음에 할 행동을 입력해주세요.');const now=new Date().toISOString(),versionId=uid(),analysis={...value,correctionRule:value.correctionRule||'',id,status:value.primary==='unknown'?'user_unresolved':'user_confirmed',versionId,updatedAt:now};state.analyses[id]=analysis;state.analysisVersions.push({...analysis,uid:versionId,time:now});persist();return analysis;}
 function assessAttempt(attemptUid,value){const r=state.attempts.find(a=>a.uid===attemptUid);if(!r)throw Error('풀이 기록을 찾지 못했습니다.');if(['same','resolved'].includes(value.outcome)&&(r.analysisSnapshot?.status!=='user_confirmed'||!validCode(r.analysisSnapshot?.primary)))throw Error('이 풀이 전에 확인한 원인·규칙이 없어 비교할 수 없습니다. 다음 복습부터 비교합니다.');if(value.outcome==='same'&&r.correct)throw Error('정답인 풀이를 같은 오답으로 집계하지 않습니다. 헷갈렸다면 확인 필요를 선택하세요.');if(value.outcome==='resolved'&&(!r.correct||r.hinted||r.uncertain||Number(r.confidence)<4||r.confidence==null||!value.evidence?.trim()||r.posCorrect===false))throw Error('규칙 적용 확인은 힌트 없이 맞히고, 확신도 4 이상과 근거를 남겼을 때 가능합니다.');r.updatedAt=new Date().toISOString();r.assessment={...value,baselineVersion:r.analysisSnapshot?.versionId||null,ruleId:r.analysisSnapshot?.ruleId||value.ruleId||null,primary:r.analysisSnapshot?.primary||value.primary||null,time:new Date().toISOString()};persist();return r;}
 function saveVocab(id,value){state.vocabOverrides[id]={...(state.vocabOverrides[id]||{}),...value,updatedAt:new Date().toISOString()};persist();}
 function reviewVocab(id,value){if(!['known','uncertain','unknown'].includes(value.result))throw Error('어휘 학습 결과를 선택해주세요.');const r={...value,id,uid:uid(),time:new Date().toISOString(),dueAt:new Date(Date.now()+(value.result==='known'?3:1)*86400000).toISOString()};state.vocabReviews.push(r);persist();return r;}
 function saveTest(id,value){state.testNotes[id]={...value,updatedAt:new Date().toISOString()};persist();}
 return{get state(){return state;},latest,needsReview,status,next,touch,draft,add,advance,due,merge,uncertain,reload,persist,saveAnalysis,assessAttempt,saveVocab,reviewVocab,saveTest,key:KEY,courseOf};
}
return{create,normalize,courseOf,validCode,KEY,LEGACY};
});
