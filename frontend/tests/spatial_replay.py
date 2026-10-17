"""Replay an actual archived coordinate heatmap without model/retrieval calls."""
import json,subprocess,time,shutil,threading,tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'experiments/04-ui-implementation';name='asset-ui-spatial-replay';r=json.load(open('/tmp/asset-coordinate-heatmaps.json'))[-1];a=r['answer'];b=r['block'];sid=r['session_id'];owner=r['user_id'];now='2026-10-17T11:00:00Z';commands=[]
def cli(*args):
 p=subprocess.run(['agent-browser','--session',name,*args],capture_output=True,text=True);commands.append({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr;return p.stdout
def ev(js):return json.loads(cli('eval',js))
def wait(js):
 for _ in range(120):
  if ev(js):return
  time.sleep(.15)
 raise AssertionError(js)
session={'id':sid,'user_id':owner,'namespace':a['dataset_namespace'],'title':'Historical spatial chart replay','created_at':now,'updated_at':now};history={'session':session,'messages':[{'id':'recorded-user','role':'user','content':'Recorded historical chart review — no model request','created_at':now,'status':'complete'},{'id':'recorded-answer','role':'assistant','content':a['narrative'],'created_at':now,'status':'complete','envelope':a}]}
class API(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=self.path.split('?')[0]
  if path=='/api/health':body={'data_ready':True,'model_configured':True,'model_generation_enabled':True,'model':'gemma-4-26b-a4b-it','dataset_namespace':a['dataset_namespace'],'reference_date':a['reference_date']}
  elif path=='/api/users':body={'users':[{'user_id':owner,'name':'Historical chart replay'}]}
  elif path=='/api/sessions':body={'sessions':[session]}
  elif path=='/api/sessions/'+sid+'/messages':body=history
  else:body={'answer_id':a['answer_id'],'status':'error','error_code':'not_requested','suggestions':[]}
  raw=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
api=ThreadingHTTPServer(('127.0.0.1',0),API);threading.Thread(target=api.serve_forever,daemon=True).start();scratch=Path(tempfile.mkdtemp(prefix='asset-spatial-replay-'));config=scratch/'vite.config.mjs';config.write_text('export default '+json.dumps({'preview':{'proxy':{'/api/copilotkit':'http://127.0.0.1:4190','/api':'http://127.0.0.1:'+str(api.server_port)}}})+';');preview=subprocess.Popen([str(root/'frontend/node_modules/.bin/vite'),'preview','--config',str(config),'--outDir','/tmp/asset-ui-stable-jcssqzxv','--host','127.0.0.1','--port','5195','--strictPort'],cwd=root/'frontend',stdout=(scratch/'preview.log').open('w'),stderr=subprocess.STDOUT);time.sleep(.7)
cli('open','http://localhost:5195');cli('network','unroute')
cli('network','route','**/api/copilotkit/agent/*/run','--abort');cli('eval',"localStorage.clear();localStorage.setItem('asset-intelligence.mode','live');localStorage.setItem('asset-intelligence.profile.live',"+json.dumps(owner)+");localStorage.setItem('asset-intelligence.dataset-namespace',"+json.dumps(a['dataset_namespace'])+");void 0");cli('reload');wait("!!document.querySelector('[data-panel=\""+b['id']+"\"] .leaflet-container')");cli('set','viewport','1440','1000');selector='[data-panel="'+b['id']+'"] button[aria-label^="Expand"]';cli('eval',"document.querySelector("+json.dumps(selector)+").scrollIntoView({block:'center'});void 0");cli('click',selector);wait("document.querySelectorAll('.expanded-view .leaflet-interactive').length===200");time.sleep(.5);details=ev("({markers:document.querySelectorAll('.expanded-view .leaflet-interactive').length,scale:document.querySelector('.expanded-view .map-numeric-scale')?.textContent,categoryChart:!!document.querySelector('.expanded-view .chart-view svg'),title:document.querySelector('.expanded-view .ant-drawer-title')?.textContent})");assert details['markers']==200 and not details['categoryChart'];assert '0.3' in details['scale'] and '37.6' in details['scale'] and '4 areas' in details['scale'];cli('screenshot',str(out/'heatmap-geographic-after.png'));shutil.copyfile('/tmp/orca-paste-1792237201635-8a1ae20f-4041-4ca2-9478-6f7e873d0d0f.png',out/'heatmap-category-before.png');(out/'spatial-replay-results.json').write_text(json.dumps({'passed':True,'recorded_original_envelope':True,'model_generation_calls':0,'retrieval_calls':0,'original_answer_id':a['answer_id'],'original_block_encoding':b['encoding'],'original_result_rows':len(a['results'][b['result_set_id']]['rows']),'observed':details,'aggregation':'none; exact observations colored at geographic coordinates','commands':commands},indent=2)+'\n');print(json.dumps(details,indent=2));cli('close');preview.terminate();preview.wait(timeout=5);api.shutdown()
