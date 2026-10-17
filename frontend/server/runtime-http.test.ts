import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer,type Server} from 'node:http';
import {randomUUID} from 'node:crypto';
import express from 'express';
import {HttpAgent,EventType,type BaseEvent} from '@ag-ui/client';
import {EventEncoder} from '@ag-ui/encoder';
import {CopilotRuntime,InMemoryAgentRunner} from '@copilotkit/runtime/v2';
import {createCopilotExpressHandler} from '@copilotkit/runtime/v2/express';
process.env.COPILOTKIT_TELEMETRY_DISABLED='true';
async function listen(server:Server){await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));const address=server.address();if(!address||typeof address==='string')throw new Error('No test port');return `http://127.0.0.1:${address.port}`;}
async function close(server:Server){server.closeAllConnections();await new Promise<void>(resolve=>server.close(()=>resolve()));}
test('actual HTTP AG-UI and self-hosted runtime keep an idle stream open until terminal event',async()=>{
 const upstream=createServer(async(request,response)=>{
  let body='';for await(const part of request)body+=part;const input=JSON.parse(body);const encoder=new EventEncoder({accept:'text/event-stream'});
  response.writeHead(200,{'Content-Type':encoder.getContentType(),'Cache-Control':'no-cache'});
  const emit=<T extends BaseEvent>(event:T)=>response.write(encoder.encode(event));
  emit({type:EventType.RUN_STARTED,threadId:input.threadId,runId:input.runId});
  emit({type:EventType.CUSTOM,name:'asset_progress',value:{message:'Recorded protocol wait; no model'}});
  await new Promise(resolve=>setTimeout(resolve,500));response.write(': keep-alive\n\n');await new Promise(resolve=>setTimeout(resolve,900));
  if(response.destroyed)return;
  emit({type:EventType.TEXT_MESSAGE_START,messageId:'recorded-response',role:'assistant'});
  emit({type:EventType.TEXT_MESSAGE_CONTENT,messageId:'recorded-response',delta:'Recorded delayed protocol fixture.'});
  emit({type:EventType.TEXT_MESSAGE_END,messageId:'recorded-response'});
  emit({type:EventType.RUN_FINISHED,threadId:input.threadId,runId:input.runId});response.end();
 });
 const app=express();const server=createServer(app);
 try{
  const upstreamURL=await listen(upstream);const runtime=new CopilotRuntime({agents:{default:new HttpAgent({url:upstreamURL})},runner:new InMemoryAgentRunner({maxThreads:4,maxRunsPerThread:2,maxBytes:1024*1024})});app.use(createCopilotExpressHandler({runtime,basePath:'/api/copilotkit'}));
  const runtimeURL=await listen(server);const agent=new HttpAgent({url:runtimeURL+'/api/copilotkit/agent/default/run',threadId:randomUUID()});agent.setMessages([{id:'recorded-question',role:'user',content:'Recorded protocol test'}]);let text='',terminal=false;const began=performance.now();
  await agent.runAgent({runId:randomUUID()},{onTextMessageContentEvent:({event})=>{text+=event.delta;},onRunFinishedEvent:()=>{terminal=true;}});
  assert.ok(performance.now()-began>=1300,'A live run must not finish during the upstream idle interval');assert.equal(terminal,true);assert.equal(text,'Recorded delayed protocol fixture.');
 }finally{await Promise.all([close(server),close(upstream)]);}
});
