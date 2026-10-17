/** Backend-owned history is authoritative; SDK process-global thread APIs stay private. */
export function runtimeRoute(method:string,path:string,session:string,body:unknown):'info'|'owned'|'reject'{
 if(method==='GET'&&path==='/api/copilotkit/info')return 'info';
 if(method!=='POST')return 'reject';
 if(path===`/api/copilotkit/agent/default/stop/${session}`)return 'owned';
 if(!['/api/copilotkit/agent/default/run','/api/copilotkit/agent/default/connect'].includes(path))return 'reject';
 return typeof body==='object'&&body!==null&&!Array.isArray(body)&&(body as {threadId?:unknown}).threadId===session?'owned':'reject';
}
export async function ownedRuntimeSession(backend:string,user:string,session:string,fetcher:typeof fetch=fetch):Promise<number>{
 try{const response=await fetcher(backend+'/api/sessions/'+encodeURIComponent(session),{headers:{'x-user-id':user,'x-session-id':session},signal:AbortSignal.timeout(5000)});if([401,403,404].includes(response.status))return response.status;if(!response.ok)return 503;const value=await response.json();return value.id===session&&value.user_id===user?200:403;}catch{return 503;}
}
