"""Actual browser status-resume regression with recorded API receipts; no model."""
import json,subprocess,time,uuid,datetime
from pathlib import Path
name='asset-ui-pending';out=Path(__file__).resolve().parents[2]/'experiments/04-ui-implementation';logs=[]
def cli(*args):
 p=subprocess.run(['agent-browser','--session',name,*args],capture_output=True,text=True);logs.append({'args':args,'status':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr;return p.stdout
def ev(source):return json.loads(cli('eval',source))
def wait(source):
 for _ in range(80):
  if ev(source):return
  time.sleep(.15)
 raise AssertionError(source)
sid=str(uuid.uuid4());now='2026-10-17T09:00:00Z';actor='recorded-poll-actor';session={'id':sid,'user_id':actor,'title':'Recorded running response','created_at':now,'updated_at':now};user={'id':'recorded-run:user','client_message_id':'recorded-question','run_id':'recorded-run','run_status':'running','role':'user','content':'Recorded request, not a model call','created_at':now,'status':'received'};history={'session':session,'messages':[user]}
base=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=10)
def phase(sid,stage,status,second,attempt):return {'stage_id':sid,'stage':stage,'status':status,'timestamp':(base+datetime.timedelta(seconds=second)).isoformat(),'attempt_id':attempt}
user['stages']=[phase('plan-old','planner','completed',1,'older'),phase('make-old','maker','failed',3,'older'),phase('plan-new','planner','started',4,'current'),phase('plan-new','planner','completed',5,'current'),phase('query-new','query_records','started',6,'current')]
history={'session':session,'messages':[user]}
cli('open','http://localhost:5192');cli('network','unroute')
for path,body in [('**/api/health',{'model_configured':True,'model_generation_enabled':True,'data_ready':True}),('**/api/users',{'users':[{'user_id':actor,'name':'Recorded Protocol Operator'}]}),('**/api/sessions?*',{'sessions':[session]}),('**/api/sessions/'+sid+'/messages',history)]:cli('network','route',path,'--body',json.dumps(body))
cli('network','route','**/api/copilotkit/agent/*/run','--abort')
cli('eval',"Object.keys(localStorage).filter(k=>k.startsWith('asset-intelligence')).forEach(k=>localStorage.removeItem(k));localStorage.setItem('asset-intelligence.mode','live');localStorage.setItem('asset-intelligence.profile.live','recorded-poll-actor');void 0")
cli('reload');wait("!!document.querySelector('.chat-message.assistant .stream-status')");assert ev("document.querySelector('.assistant-heading').textContent.includes('Querying records')");assert ev("document.querySelector('.execution-stepper').textContent.includes('Planning') && !document.querySelector('.execution-stepper').textContent.includes('Preparing answer') && !!document.querySelector('.earlier-attempts')");time.sleep(3.2);assert ev("!document.querySelector('.response-error') && !!document.querySelector('.stream-status')");assert ev("document.querySelector('button[aria-label=\"Send message\"]').disabled");cli('screenshot',str(out/'recorded-server-running.png'))
history['messages']=[{**user,'run_status':'complete'},{'id':'recorded-run:assistant','role':'assistant','content':'Recorded completed response from scoped history.','created_at':now,'status':'complete'}]
cli('network','unroute','**/api/sessions/'+sid+'/messages');cli('network','route','**/api/sessions/'+sid+'/messages','--body',json.dumps(history));wait("document.querySelector('.answer-narrative')?.textContent.includes('Recorded completed response')");assert ev("!document.querySelector('.stream-status') && !document.querySelector('.response-error')");assert ev("document.querySelectorAll('.chat-message.user').length===1 && document.querySelectorAll('.chat-message.assistant').length===1");cli('reload');wait("document.querySelector('.answer-narrative')?.textContent.includes('Recorded completed response')");assert ev("document.querySelectorAll('.chat-message.user').length===1")
(out/'pending-history-browser-results.json').write_text(json.dumps({'passed':True,'fixture_only':True,'model_generation_calls':0,'checks':['running receipt stays active past idle interval','no false interruption or enabled duplicate send','scoped history poll renders terminal response','reload preserves one user and one assistant'],'commands':logs},indent=2)+'\n');print('PASS: recorded running → terminal → reload, no model calls')
cli('close')
