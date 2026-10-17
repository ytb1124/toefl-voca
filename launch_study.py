"""Double-click launcher uses a fixed origin so browser progress stays together."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
from urllib.request import urlopen
import threading, webbrowser, json
ROOT=Path(__file__).resolve().parent
PORT=8871
URL=f'http://127.0.0.1:{PORT}/study/index.html'
handler=partial(SimpleHTTPRequestHandler,directory=str(ROOT))
try:
    server=ThreadingHTTPServer(('127.0.0.1',PORT),handler)
except OSError:
    try:
        with urlopen(f'http://127.0.0.1:{PORT}/study/version.json',timeout=2) as response:
            running=json.load(response)
            expected=json.loads((ROOT/'study/version.json').read_text())
            if running.get('app')!='taebin-toefl-study' or running.get('build')!=expected.get('build'):raise ValueError('different study version')
        webbrowser.open(URL)
        print('이미 실행 중인 학습 화면을 열었습니다.')
    except Exception:
        print('이전 학습 창이나 다른 프로그램이 실행 중입니다. 이전 학습용 터미널 창을 닫고 이 시작 파일을 다시 실행해주세요. 브라우저에 저장된 기록은 유지됩니다.')
    input('Enter 키를 눌러 닫기 ')
else:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    webbrowser.open(URL)
    print('\nTOEFL 학습 화면을 열었습니다.\n학습하는 동안 이 창을 열어두세요.\n끝낼 때는 이 창을 닫거나 Control+C를 누르세요.\n학습 기록은 브라우저에 남습니다.\n')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
