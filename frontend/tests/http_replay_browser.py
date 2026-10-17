"""35-second real browser→preview proxy→actual runtime→AG-UI replay; no LLM."""
import json,subprocess,time,os,tempfile,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2];front=root/'frontend';out=root/'experiments/04-ui-implementation';browser='asset-ui-http-replay';commands=[];children=[];scratch=Path(tempfile.mkdtemp(prefix='asset-ui-http-audit-'))
def cli(*args):
 p=subprocess.run(['agent-browser','--session',browser,*args],capture_output=True,text=True);commands.append({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr;return p.stdout
def ev(source):return json.loads(cli('eval',source))
def alive(url):
 for _ in range(100):
  try:
   with urllib.request.urlopen(url,timeout=1) as response:return json.load(response)
  except Exception:time.sleep(.1)
 raise AssertionError('Service not ready: '+url)
try:
 api=subprocess.Popen([str(front/'node_modules/.bin/tsx'),'tests/http_replay_server.ts'],cwd=front,stdout=subprocess.PIPE,stderr=(scratch/'api.log').open('w'),text=True);children.append(api);fixture=json.loads(api.stdout.readline());
 env={**os.environ,'BACKEND_URL':fixture['url'],'COPILOT_RUNTIME_PORT':'4191','COPILOTKIT_TELEMETRY_DISABLED':'true'};runtime=subprocess.Popen([str(front/'node_modules/.bin/tsx'),'server/runtime.ts'],cwd=front,env=env,stdout=(scratch/'runtime.log').open('w'),stderr=subprocess.STDOUT);children.append(runtime);alive('http://127.0.0.1:4191/health')
 config=scratch/'vite.config.mjs';config.write_text('export default '+json.dumps({'preview':{'proxy':{'/api/copilotkit':'http://127.0.0.1:4191','/api':fixture['url']}}})+';\n');preview=subprocess.Popen([str(front/'node_modules/.bin/vite'),'preview','--config',str(config),'--outDir','/tmp/asset-ui-stable-jcssqzxv','--host','127.0.0.1','--port','5194','--strictPort'],cwd=front,stdout=(scratch/'preview.log').open('w'),stderr=subprocess.STDOUT);children.append(preview);alive('http://127.0.0.1:5194/api/health')
 cli('open','http://localhost:5194');cli('eval',"localStorage.clear();localStorage.setItem('asset-intelligence.mode','live');localStorage.setItem('asset-intelligence.profile.live','recorded-http-operator');void 0");cli('reload')
 for _ in range(100):
  if ev("document.querySelector('.connection-badge')?.textContent==='Connected' && !document.querySelector('.history-loading')"):break
  time.sleep(.1)
 origin=ev('performance.timeOrigin');cli('network','har','start','--content','none');cli('fill','textarea[aria-label="Message Asset Copilot"]','Recorded delayed request — no model');began=time.monotonic();cli('click','button[aria-label="Send message"]');states=[]
 while time.monotonic()-began<48:
  state=ev("({stop:!!document.querySelector('button[aria-label=\"Stop response\"]'),pending:document.querySelector('.stream-status')?.textContent,error:document.querySelector('.response-error')?.textContent,text:document.querySelector('.answer-narrative')?.textContent,origin:performance.timeOrigin})");state['elapsed_seconds']=round(time.monotonic()-began,2);states.append(state)
  if state.get('text','').startswith('Recorded delayed HTTP response') and not state['stop']:break
  time.sleep(1)
 metrics=json.load(urllib.request.urlopen(fixture['url']+'/fixture-metrics'));cli('network','har','stop',str(out/'delayed-runtime-replay.har'));result={'fixture_only':True,'model_generation_calls':0,'actual_agent_requests':metrics['calls'],'time_origin_unchanged':all(s['origin']==origin for s in states),'states':states,'server':metrics,'commands':commands,'scratch_logs':str(scratch)};result['passed']=metrics['calls']==1 and result['time_origin_unchanged'] and any(s['elapsed_seconds']>=30 and s['stop'] for s in states) and states[-1].get('text','').startswith('Recorded delayed HTTP response');(out/'delayed-runtime-browser-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['commands','states']},indent=2));assert result['passed'],'Replay did not keep the actual stream active through30s and publish terminal reply'
finally:
 for child in reversed(children):
  child.terminate()
  try:child.wait(timeout=4)
  except subprocess.TimeoutExpired:child.kill();child.wait()
 try:cli('close')
 except Exception:pass
