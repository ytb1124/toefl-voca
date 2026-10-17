from pathlib import Path
import zipfile,json,re,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
# Original material must stay byte-for-byte intact across packaging.
d=json.loads((ROOT/'study/training-data.json').read_text());assert len({q['id'] for q in d['errors']})==63
for s in d['sources']:assert hashlib.sha256((ROOT/'study'/s['image']).read_bytes()).hexdigest()==s['sha256']
before=subprocess.check_output(['git','show','origin/main:fillintheblank.html'],cwd=ROOT,text=True);after=(ROOT/'fillintheblank.html').read_text()
for name in ['RAW_TASKS','TITLES','NOTES']:
 get=lambda text:json.loads(re.search(r'const '+name+r' = (.*?);\n',text).group(1))
 assert get(before)==get(after),name
assert len(json.loads((ROOT/'study/transfer-data.json').read_text()))==28
for target,full in [('TOEFL_통합학습사이트_v5.zip',True),('GitHub_반영파일_v5.zip',False)]:
 files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts and p.name!='.DS_Store'] if full else [ROOT/'index.html',ROOT/'fillintheblank.html',ROOT/'toefl_vocab_srs_textbook_8.html',ROOT/'검증_결과.json',ROOT/'가이드_구현대조.txt',ROOT/'사용안내.txt',ROOT/'구현전_점검.txt',ROOT/'개인화훈련_구현보고서.txt',ROOT/'단어암기_통합_사용안내.txt',*list((ROOT/'study').rglob('*')),*list((ROOT/'tests').rglob('*')),*list((ROOT/'scripts').rglob('*'))]
 with zipfile.ZipFile(ROOT.parent/target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:
   if p.is_file():
    rel=p.relative_to(ROOT);z.write(p,Path('TOEFL_학습사이트_v5')/rel if full else rel)
 with zipfile.ZipFile(ROOT.parent/target) as z:assert z.testzip() is None
 print(target,(ROOT.parent/target).stat().st_size)
print('51 original hashes and all 49 C-Test templates/titles/notes verified')
