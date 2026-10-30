import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import urlparse
import uuid
from fixture import make_fixture, git
from history import mine
from model import converse, MODEL, REVISION
from ritual import replay

BASE=Path(__file__).resolve().parent
REPO=make_fixture(Path(os.environ.get('GRAVEYARD_DATA','/tmp/graveyard-shift-data'))/'demo')
CATALOG=mine(REPO)
JOBS={}
LOCK=threading.Lock()
ACTIVE=threading.BoundedSemaphore(3)

def find(ident):
    return next(g for g in CATALOG['ghosts'] if g['id']==ident)

def evidence(ghost):
    head=git(REPO,'rev-parse','HEAD')
    current=next(x for x in CATALOG['living'] if x['name']==('run_with_retry' if ghost['name']=='legacy_retry' else 'load_settings'))
    return [
        {'id':'E1','fact':'Last observed function body before disappearance.',
         'revision':ghost['revision'],'path':ghost['path'],'start':ghost['start'],'end':ghost['end'],'quote':ghost['source']},
        {'id':'E2','fact':'The disappearance commit records: '+ghost['message'],
         'revision':ghost['disappearance'],'path':ghost['path'],'quote':ghost['diff']},
        {'id':'E3','fact':'Current '+current['name']+' body. '+('Exact normalized AST-body match supports a rename/move candidate.' if ghost['descendant'] else 'A different implementation; a shared name or purpose does not establish correctness.'),
         'revision':head,'path':current['path'],'start':current['start'],'end':current['end'],'quote':current['source']},
    ]

def submit(action, data):
    if not ACTIVE.acquire(blocking=False):
        raise RuntimeError('The graveyard is busy. Wait for a running job to finish.')
    ident=str(uuid.uuid4())
    job={'id':ident,'action':action,'status':'queued','started':time.time(),'events':[]}
    with LOCK:
        if len(JOBS)>=24:
            done=[k for k,v in JOBS.items() if v['status'] in ['completed','failed']]
            if done: del JOBS[done[0]]
            else:
                ACTIVE.release();raise RuntimeError('All retained jobs are active.')
        JOBS[ident]=job
    def event(message):
        with LOCK:job['events'].append({'text':message,'elapsed':round(time.time()-job['started'],2)})
    def work():
        try:
            job['status']='running'
            if action=='mine':
                event('Reading the authored repository. No visitor repository is uploaded.')
                result=mine(REPO,progress=lambda n,total:event(f'Read commit {n} of {total}'))
            elif action=='ask':
                ghost=find(data['ghost']); event('Selected immutable source evidence. Loading or running Qwen on CPU.')
                result=converse(data['question'],ghost,evidence(ghost))
                event('Generation finished. Checking citation IDs; read the snippets to judge the interpretation.')
            elif action=='challenge':
                ghost=find(data['ghost']); event('Re-reading the disappearance and current Python syntax trees.')
                again=mine(REPO); candidate=next(g for g in again['ghosts'] if g['id']==ghost['id'])
                result={'status':candidate['status'],'descendant':candidate['descendant'],
                        'verified_body_match':candidate['descendant'] is not None}
            elif action=='ritual':
                if find(data['ghost'])['name']!='legacy_retry':raise ValueError('This ghost has no authored regression fixture.')
                event('Running fixed authored tests against the rewrite in a fresh temporary directory.')
                result=replay(find(data['ghost'])['source'])
                event('Before/after runs completed. Checking return codes and the expected assertions.')
            else:raise ValueError('Unknown action')
            with LOCK:job.update(status='completed',result=result,elapsed=round(time.time()-job['started'],3))
        except Exception as exc:
            with LOCK:job.update(status='failed',error=str(exc)[:350],elapsed=round(time.time()-job['started'],3))
        finally:ACTIVE.release()
    threading.Thread(target=work,daemon=True).start()
    return ident

class Handler(BaseHTTPRequestHandler):
    def send(self,body,status=200,kind='application/json; charset=utf-8'):
        raw=json.dumps(body).encode() if isinstance(body,(dict,list)) else body.encode() if isinstance(body,str) else body
        self.send_response(status);self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store' if kind.startswith('application/json') else 'public, max-age=60')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        self.end_headers();self.wfile.write(raw)

    def do_GET(self):
        route=urlparse(self.path).path
        if route=='/api/catalog':return self.send({**CATALOG,'model':MODEL,'revision':REVISION,'authored_fixture':True})
        if route.startswith('/api/jobs/'):
            with LOCK:job=JOBS.get(route.rsplit('/',1)[-1]); payload=json.loads(json.dumps(job)) if job else None
            return self.send(payload or {'error':'Run not retained; start a new one.'},200 if payload else 404)
        if route.startswith('/api/ghost/'):
            try:
                g=find(route.rsplit('/',1)[-1]);return self.send({**g,'evidence':evidence(g)})
            except StopIteration:return self.send({'error':'Unknown ghost'},404)
        if route.startswith('/evidence/'):
            try:
                _,_,ident,ref=route.split('/');e=next(e for e in evidence(find(ident)) if e['id']==ref)
                content=f"<h1>{html.escape(e['id'])}: {html.escape(e['fact'])}</h1><p>Authored demo history · revision {e['revision']} · {e['path']} · lines {e.get('start','diff')}–{e.get('end','diff')}</p><pre>{html.escape(e['quote'])}</pre>"
                return self.send('<!doctype html><meta charset="utf-8"><title>Graveyard Shift evidence</title><style>body{font:18px system-ui;max-width:1000px;margin:40px auto;padding:24px}pre{white-space:pre-wrap;line-height:1.6}</style>'+content,kind='text/html; charset=utf-8')
            except (ValueError,StopIteration):return self.send({'error':'Unknown evidence'},404)
        files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if route in files:
            f=BASE/'web'/files[route]
            kind='text/html' if f.suffix=='.html' else 'text/css' if f.suffix=='.css' else 'text/javascript'
            return self.send(f.read_bytes(),kind=kind+'; charset=utf-8')
        return self.send({'error':'Not found'},404)

    def do_POST(self):
        if urlparse(self.path).path!='/api/jobs':return self.send({'error':'Not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=2048:raise ValueError('Request too large or empty')
            data=json.loads(self.rfile.read(length));action=data.get('action')
            if action not in ['mine','ask','challenge','ritual']:raise ValueError('Unknown action')
            if action!='mine':find(data.get('ghost'))
            if action=='ask' and (not isinstance(data.get('question'),str) or not 3<=len(data['question'])<=350):raise ValueError('Question must contain 3–350 characters')
            return self.send({'id':submit(action,data)},202)
        except (ValueError,KeyError,StopIteration):return self.send({'error':'Invalid action, ghost or question'},400)
        except RuntimeError as exc:return self.send({'error':str(exc)},429)

if __name__=='__main__':
    port=int(os.environ.get('PORT','7860'))
    print(f'Graveyard Shift listening on {port}',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
