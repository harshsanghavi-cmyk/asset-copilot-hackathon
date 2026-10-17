import express from 'express';
import {runtimeRoute,ownedRuntimeSession} from './runtime-scope';
import {adminProxy} from './local-admin';
import { HttpAgent } from '@ag-ui/client';
import { CopilotRuntime, InMemoryAgentRunner } from '@copilotkit/runtime/v2';
import { createCopilotExpressHandler } from '@copilotkit/runtime/v2/express';
import { RunnerRegistry, RunnerCapacityError, validUserId, validSessionId } from './runner-registry';
process.env.COPILOTKIT_TELEMETRY_DISABLED='true';
const backend=(process.env.BACKEND_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
function bounded(value:string|undefined,fallback:number,min:number,max:number){const number=Number(value);return Number.isFinite(number)&&number>=min&&number<=max?Math.floor(number):fallback;}
const maximum=bounded(process.env.RUNNER_MAX,24,1,256);const memoryLimits={maxThreads:maximum,maxRunsPerThread:16,maxBytes:32*1024*1024};
const runners=new RunnerRegistry(()=>new InMemoryAgentRunner(memoryLimits),{maximum,idleMs:bounded(process.env.RUNNER_IDLE_MS,10*60*1000,1000,60*60*1000)});
const cleanup=setInterval(()=>runners.prune(),60000);cleanup.unref();
const app=express();
app.use('/api/copilotkit',express.json({limit:'256kb'}));
app.use('/api/local-admin',express.json({limit:'64kb'}),adminProxy(backend));
app.get('/health',(_request,response)=>response.json({service:'asset-copilot-ui-runtime',ephemeral:runners.stats(),durableHistory:'backend-owned',directModelCalls:false,memoryLimits}));
app.use(async(request,response,next)=>{
 const user=request.headers['x-user-id'],session=request.headers['x-session-id'];
 if(!user||!session){response.status(401).json({error:'A user and conversation are required.'});return;}
 if(!validUserId(user)||!validSessionId(session)){response.status(400).json({error:'Invalid user or conversation identifier.'});return;}
 const route=runtimeRoute(request.method,request.path,session,request.body);if(route==='reject'){response.status(403).json({error:'Only the selected conversation protocol is available through this endpoint.'});return;}if(route==='owned'){const status=await ownedRuntimeSession(backend,user,session);if(status!==200){response.status(status).json({error:status===503?'Conversation ownership could not be checked.':'This conversation is unavailable to the selected profile.'});return;}}
 let lease;try{lease=runners.acquire(user,session);}catch(error){if(error instanceof RunnerCapacityError){response.setHeader('Retry-After','5');response.status(503).json({error:'The workspace is busy. Please try again shortly.'});return;}next(error);return;}
 // IncomingMessage close may fire after reading a request while SSE is active.
 // Track the response lifecycle instead, and release each lease exactly once.
 response.once('finish',lease.release);response.once('close',lease.release);request.once('aborted',lease.release);
 const runtime=new CopilotRuntime({agents:{default:new HttpAgent({url:backend+'/api/agent',threadId:session,headers:{'x-user-id':user,'x-session-id':session}})},runner:lease.value});
 return createCopilotExpressHandler({runtime,basePath:'/api/copilotkit'})(request,response,next);
});
const port=Number(process.env.COPILOT_RUNTIME_PORT||4190);
const server=app.listen(port,'127.0.0.1',()=>process.stdout.write(`Asset UI runtime listening on http://127.0.0.1:${port}\n`));
server.once('close',()=>clearInterval(cleanup));
