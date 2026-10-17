export class RunnerCapacityError extends Error {}
type Entry<T>={value:T;lastUsed:number;active:number};
/** Ephemeral transport state only. Durable messages are always backend-owned. */
export class RunnerRegistry<T>{
 private entries=new Map<string,Entry<T>>();
 constructor(private factory:()=>T,private options:{maximum:number;idleMs:number;now?:()=>number}){if(options.maximum<1||options.idleMs<1)throw new Error('Invalid runner retention limits.');}
 private now(){return this.options.now?.()??Date.now();}
 prune(){const now=this.now();for(const[key,entry]of this.entries)if(entry.active===0&&now-entry.lastUsed>=this.options.idleMs)this.entries.delete(key);}
 acquire(user:string,session:string){this.prune();const key=JSON.stringify([user,session]);let entry=this.entries.get(key);if(!entry){if(this.entries.size>=this.options.maximum){const idle=[...this.entries].filter(([,value])=>value.active===0).sort((a,b)=>a[1].lastUsed-b[1].lastUsed);if(!idle.length)throw new RunnerCapacityError('All transport slots are active.');this.entries.delete(idle[0][0]);}entry={value:this.factory(),lastUsed:this.now(),active:0};this.entries.set(key,entry);}entry.active++;entry.lastUsed=this.now();let released=false;return {value:entry.value,release:()=>{if(released)return;released=true;entry!.active--;entry!.lastUsed=this.now();}};}
 stats(){return {runners:this.entries.size,activeRequests:[...this.entries.values()].reduce((sum,e)=>sum+e.active,0),maximum:this.options.maximum,idleMs:this.options.idleMs};}
}
export function validUserId(value:unknown):value is string{return typeof value==='string'&&/^[A-Za-z0-9_.:@-]{1,128}$/.test(value);}
export function validSessionId(value:unknown):value is string{return typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);}
