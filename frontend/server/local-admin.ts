import type {Request,Response,NextFunction} from 'express';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
export function allowedAdminPath(path:string,method:string){
 if(path.includes('..')||path.includes('%'))return false;
 return method==='GET'&&(/^\/admin\/memory(?:\/[A-Za-z0-9_-]+)?$/.test(path)||path==='/admin/model'||/^\/retrieval\/(?:overview|catalog|walkthrough|sources(?:\/[A-Za-z0-9_.:-]+)?|records\/[A-Za-z0-9_-]+|chunks|enrichments|issues|traces(?:\/[A-Za-z0-9_-]+)?|evidence\/[A-Za-z0-9_.:-]+)$/.test(path))||method==='POST'&&/^\/retrieval\/(query|search)$/.test(path);
}
export function localOrigin(origin:string|undefined){try{const url=new URL(origin||'');return ['http:','https:'].includes(url.protocol)&&['localhost','127.0.0.1','[::1]'].includes(url.hostname);}catch{return false;}}
export function adminProxy(backend:string){return async(request:Request,response:Response,_next:NextFunction)=>{
 if(request.headers['x-local-admin']!=='1'||!localOrigin(request.headers.origin as string||request.headers.referer as string)){response.status(403).json({error:'Explicit local administrator access is required.'});return;}
 const path=request.path;if(!allowedAdminPath(path,request.method)){response.status(403).json({error:'This route is outside the local diagnostic capability.'});return;}
 try{
  // File is read only on this explicit diagnostic route, never exposed to JS.
  const token=(await readFile(resolve(process.cwd(),'../runtime/admin-token'),'utf8')).trim();
  const upstream=await fetch(backend+'/api'+request.url,{method:request.method,headers:{'content-type':'application/json','x-admin-token':token},body:request.method==='POST'?JSON.stringify(request.body):undefined,signal:AbortSignal.timeout(30000)});
  response.status(upstream.status).type('application/json').send(await upstream.text());
 }catch{response.status(503).json({error:'Local diagnostic access is unavailable. Start the authorized backend administrator service.'});}
};}
