from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'study/training-data.json').read_text()); raw=json.loads((ROOT/'study/diagnostic-source.json').read_text())
groups={
'V':['단어 자체를 모름','뜻을 잘못 알고 있었음','다의어 뜻 선택 오류','품사 혼동','연어·결합 표현을 모름','긍정·부정 뉘앙스 혼동','접사·어근·단어 형성 오류','문맥에 뜻을 적용하지 못함','비슷한 단어·어형 혼동'],
'G':['주어를 잘못 찾음','주동사를 잘못 찾음','목적어·보어 관계 오류','수식 범위 오류','시제·태·수일치 오류','전치사·접속사 오류','절 구조 오류','부정·조건문 해석 오류','빈칸의 품사·형태 예측 오류'],
'M':['개별 단어만 해석함','문맥에 맞지 않는 뜻 적용','핵심 메시지 누락','태도·목적 해석 오류','원인·결과 혼동','시간 순서 혼동','비교 대상·방향 혼동','문장 연결·지시 대상 오류'],
'L':['지문 근거 없는 추론','과도한 확대 추론','필요한 추론을 하지 못함','일부를 전체로 일반화','인과 방향 뒤바꿈','조건·예외 무시','배경지식을 근거로 사용'],
'P':['동의어 관계를 놓침','능동·수동 변환을 놓침','긍정·부정 재표현을 놓침','구체·추상 재표현을 놓침','여러 문장의 요약을 놓침','문장 구조가 다른 같은 의미를 놓침'],
'D':['같은 단어에 현혹됨','일부만 맞는 보기를 선택','자연스럽지만 없는 내용을 선택','대상·특징·카테고리를 혼동','과장된 범위 선택','질문의 범위를 벗어난 정보 선택','반대 의미 선택','더 정확한 정답보다 그럴듯한 답 선택'],
'A':['질문의 핵심어 누락','부정어 누락','보기 끝부분 누락','질문의 요구 대상 오인','알고도 다른 답을 선택','집중이 떨어져 내용을 기억 못함'],
'T':['한 문제에 과도한 시간 사용','시간 부족으로 읽지 못함','시간 압박으로 근거 없이 선택','검토 시간 부족','불필요한 답 수정'],
'LI':['소리를 구분하지 못함','들은 단어를 인식하지 못함','들은 단어의 뜻을 모름','문장 구조를 따라가지 못함','들은 정보를 기억하지 못함','강의·대화 핵심 누락','직접 제시된 세부 정보 누락','화자의 의도·암시 해석 오류','설명 전개 구조 누락','메모 누락·비효율','일부 단어만 일치하는 보기에 현혹','특정 구간 집중력 누락']}
labels={'V':'어휘','G':'문법·구조','M':'문맥·의미 (기억 오류와 별개)','L':'추론·논리','P':'바꿔 말하기','D':'선택지 함정','A':'주의','T':'시간','LI':'듣기'}
taxonomy=[dict(code=f'{g}{i+1}',group=g,group_label=labels[g],label=v) for g,vs in groups.items() for i,v in enumerate(vs)]
rule_rows=[
('POS','G9','품사 먼저 정하기','빈칸 앞뒤의 주어·동사·전치사를 확인해 필요한 품사와 형태를 먼저 정한 뒤 철자를 완성한다.'),
('SPELL','V9','철자와 형태 대조','완성한 단어를 제시 철자·칸 수·어형과 대조하고 문장에 다시 넣어 읽는다.'),
('COLLOC','V5','함께 쓰이는 표현 확인','주어진 단어 앞뒤의 결합을 확인하고, 익숙한 뜻만으로 동사를 고르지 않는다.'),
('MEANING','V8','문맥의 뜻과 강도 확인','단어를 문맥 속 뜻으로 바꿔 읽고, 감소·완화와 완전 제거처럼 의미 강도가 달라지는지 확인한다.'),
('ENTITY','D4','대상과 특징 짝짓기','대상마다 특징을 한 줄로 묶고, 선택지의 특징이 질문이 묻는 대상의 것인지 확인한다.'),
('SCOPE','D6','질문이 묻는 범위 유지','질문이 묻는 대상과 목적을 먼저 한 줄로 정하고, 다른 범위의 참인 정보는 제외한다.'),
('EVIDENCE','L1','없는 내용을 보태지 않기','선택지의 각 주장에 본문 근거를 대응시키고 근거가 없는 수식어나 평가를 제외한다.'),
('CAUSE','M5','원인과 결과 방향 확인','무엇이 원인이고 무엇이 결과인지 화살표로 연결한 뒤 선택지의 방향과 비교한다.'),
('TIME','M6','시간과 완료 여부 구분','이미 끝난 일·예정된 일·현재 요청을 구분해 시간 표현과 응답을 맞춘다.'),
('FUNCTION','LI8','발화의 기능부터 정하기','발화를 질문·요청·제안·거절 중 하나로 요약하고 그 기능에 맞는 응답을 고른다.'),
('DIRECT','LI7','직접 나온 정보를 답과 연결','장소·연도·목적·다음 행동의 핵심어를 적고, 선택지가 같은 정보를 재표현하는지 확인한다.'),
('CHANGE','M8','변경 전후와 조건 구분','기존 내용과 변경 내용을 나누고, 현재 적용되는 장소·시간·조건만 답의 근거로 사용한다.'),
('INSERT','M8','삽입문의 연결 기능 확인','지시어가 받는 내용과 요약·예시·대조 기능을 확인한 뒤 앞뒤 문장이 이어지는 자리를 고른다.'),
('MAIN','LI6','강의 전체의 공통 주제 찾기','도입·사례·해결책을 함께 묶는 주제를 고르고 하나의 세부 사례에만 맞는 보기는 제외한다.'),
('INFER','L3','최소한으로 필요한 추론','본문의 직접 단서에서 반드시 따라오는 결론만 고르고 가능한 이야기로 확대하지 않는다.')]
rules=[dict(id='RULE-'+key,code=code,title=title,text=text,status='suggested') for key,code,title,text in rule_rows]
assign={
'TPO2':['POS','SPELL','COLLOC','TIME','SCOPE','CAUSE','EVIDENCE','SPELL','SPELL','POS','POS','MEANING','ENTITY','FUNCTION','DIRECT','ENTITY','DIRECT','SCOPE','ENTITY','DIRECT','ENTITY'],
'TPO3':['POS','POS','POS','MEANING','INSERT','POS','MEANING','COLLOC','SCOPE','INSERT','TIME','FUNCTION','FUNCTION','FUNCTION','FUNCTION','TIME','CHANGE','MEANING','TIME',None],
'TPO4':['MEANING','SPELL','COLLOC','MEANING','INFER','MEANING','SCOPE','INSERT','FUNCTION','CHANGE','DIRECT','DIRECT','ENTITY','ENTITY','DIRECT','DIRECT','INFER','FUNCTION','DIRECT','MAIN','ENTITY','DIRECT']}
pos={'TPO2-R1':'adjective','TPO2-R2':'adjective','TPO2-R3':'verb','TPO2-R8':'verb','TPO2-R9':'noun','TPO2-R10':'participle','TPO2-R11':'noun','TPO3-R1':'verb','TPO3-R2':'gerund','TPO3-R3':'participle','TPO3-R6':'adverb','TPO3-R7':'noun','TPO3-R8':'verb','TPO4-R1':'noun','TPO4-R2':'adjective','TPO4-R3':'verb','TPO4-R4':'noun'}
suggestions={}
for test,keys in assign.items():
 qs=[q for q in d['errors'] if q['test']==test];assert len(qs)==len(keys)
 for q,key in zip(qs,keys):
  rule=next((r for r in rules if r['id']=='RULE-'+str(key)),None)
  suggestions[q['id']]={'primary':rule['code'] if rule else '', 'secondary':[], 'ruleId':rule['id'] if rule else None,'correctionRule':rule['text'] if rule else '', 'status':'inferred' if rule else 'unknown','originalCodes':q['codes'],'evidence':q['evidence'],'expectedPOS':pos.get(q['id']),'whatIThought':'','whyIChose':'','criticalDifference':''}
# Links are proposed from the report context. They never assert that the learner did not know a word.
links=[
['TPO2-R1'],['TPO2-R2'],['TPO2-R3'],['TPO2-R8'],['TPO2-R9'],['TPO2-R10'],['TPO2-R11'],['TPO2-R12'],['TPO2-R13'],['TPO2-R5','TPO2-R6','TPO2-R7'],['TPO2-R4'],['TPO2-L3'],['TPO2-L3'],['TPO2-L1'],['TPO2-L1'],['TPO2-L7'],['TPO2-L7'],
['TPO3-R4'],['TPO3-R4'],['TPO3-R1'],['TPO3-R2'],['TPO3-R3'],['TPO3-R6'],['TPO3-R7'],['TPO3-R8'],['TPO3-L1'],['TPO3-L2'],['TPO3-L3'],['TPO3-L4'],['TPO3-L3'],['TPO3-L5'],['TPO3-L6'],['TPO3-L7'],['TPO3-L8'],['TPO3-R10'],
['TPO4-R1'],['TPO4-R1'],['TPO4-R2'],['TPO4-R3'],['TPO4-R4'],['TPO4-R5'],['TPO4-R6'],['TPO4-R6'],['TPO4-R6'],['TPO4-R7'],['TPO4-R8'],['TPO4-L1'],['TPO4-L1'],['TPO4-L2'],['TPO4-L3'],['TPO4-L4'],['TPO4-L6'],['TPO4-L5'],['TPO4-L5'],['TPO4-L7'],['TPO4-L7'],['TPO4-L7'],['TPO4-L8'],['TPO4-L9'],['TPO4-L10'],['TPO4-L11'],['TPO4-L13'],['TPO4-L12','TPO4-L13'],['TPO4-L12'],['TPO4-L13'],['TPO4-L14']]
assert len(links)==len(raw['vocab'])
vocab=[];byterm={};stimuli={s['id']:s for s in d['stimuli']};errors={q['id']:q for q in d['errors']}
for v,ids in zip(raw['vocab'],links):
 key=v['term'].lower().strip()
 if key in byterm:
  item=byterm[key];item['questionIds']=list(dict.fromkeys(item['questionIds']+ids));item['sources'].append(dict(test=v['test'],source=v['source'],issue=v['issue']));continue
 item=dict(v,id=f'VOC-{len(vocab)+1:03}',questionIds=ids,sources=[dict(test=v['test'],source=v['source'],issue=v['issue'])],linkStatus='suggested',learnerStatus='unconfirmed',pos='',contextMeaning=v['meaning'],synonyms='',collocations='',wordFamily='',originalSentence='',sentenceBasis='not_found')
 aliases=[a.strip().rstrip('.') for a in v['term'].split('/')];qs=[errors[x] for x in ids]
 for q in qs:
  text=stimuli[q['stimulus_id']]['text']
  for sentence in re.split(r'(?<=[.!?])\s+|\n',text):
   if any(re.search(r'\b'+re.escape(a)+r'\b',sentence,re.I) for a in aliases if a):
    item['originalSentence']=sentence;item['sentenceBasis']='restored_transcript';break
  if item['originalSentence']:break
 vocab.append(item);byterm[key]=item
assert len(vocab)==65
for v in vocab:
 if v['term'].lower() in ['residue','resident']:v['pos']='명사';v['synonyms']='';v['wordFamily']='';v['collocations']='plant residue' if v['term']=='residue' else '';v['issue']+=' · 두 단어를 품사·뜻·문맥으로 구분'
 if v['term']=='mitigate':v['synonyms']='lessen (강도 완화 문맥)';v['collocations']='mitigate the impact'
 if v['term']=='eliminate':v['issue']+=' · mitigate/lessen보다 강한 완전 제거'
 for qid in v['questionIds']:suggestions[qid].setdefault('vocabIds',[]).append(v['id'])
tests=[]
for test,day,n in [('TPO2','2026-10-02',21),('TPO3','2026-10-08',20),('TPO4','2026-10-12',22)]:
 tests.append(dict(id=test,date=day,format='2026 유형 포함 자료 (원보고서 기준)',errorCount=n,partialListening=test=='TPO3',scores=[s for s in raw['scores'] if s['test']==test],timeSpent=None,timeLimit=None,difficulty=None,environment=None,concentration=None,notes='TPO3 Listening 단독 오답 6개의 분모 없음. 확인 미니세트만 표시.' if test=='TPO3' else '확인된 세트 기준.'))
result=dict(version=3,taxonomy=taxonomy,rules=rules,suggestions=suggestions,vocab=vocab,tests=tests,codeNote='원보고서 V/G/C/I/J/A/M/T는 별도 보존. 가이드의 M은 문맥 의미, 원보고서 M은 기억. 듣기 기억의 세부 코드는 LI5.',provenance='원인·연결·교정 규칙은 제안이며 사용자 확인 전 실제 사고 과정으로 집계하지 않음.')
(ROOT/'study/diagnostic-data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(ROOT/'study/diagnostic-data.js').write_text('window.TOEFL_DIAGNOSTICS='+json.dumps(result,ensure_ascii=False)+';\n')
print('63 diagnostic suggestions, 65 vocabulary candidates, 3 tests')
