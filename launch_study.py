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
            if json.load(response).get('app')!='taebin-toefl-study':raise ValueError('other application')
        webbrowser.open(URL)
        print('이미 실행 중인 학습 화면을 열었습니다.')
    except Exception:
        print('학습용 주소가 다른 프로그램에서 사용 중입니다. 기존 프로그램을 닫고 다시 시작해주세요.')
    input('Enter 키를 눌러 닫기 ')
else:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    webbrowser.open(URL)
    print('\nTOEFL 학습 화면을 열었습니다.\n학습하는 동안 이 창을 열어두세요.\n끝낼 때는 이 창을 닫거나 Control+C를 누르세요.\n학습 기록은 브라우저에 남습니다.\n')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
