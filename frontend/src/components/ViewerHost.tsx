import { lazy, Suspense, type ComponentType } from 'react';
import { Button, Empty, Skeleton } from 'antd';
import { Database } from 'lucide-react';
type ViewerModule={RetrievalViewer:ComponentType<{baseAPI:string;initialTab?:string;localAdmin?:boolean;initialAssetId?:string}>};
// The viewer is independently owned. Discover its public entry without coupling
// the chat build to its implementation files or storage schema.
const modules=import.meta.glob<ViewerModule>('../retrieval-viewer/index.tsx');
const loader=Object.values(modules)[0];
const Viewer=loader?lazy(()=>loader().then(module=>({default:module.RetrievalViewer}))):undefined;
export default function ViewerHost({initialTab,localAdmin=false,initialAssetId}:{initialTab?:string;localAdmin?:boolean;initialAssetId?:string}){return Viewer?<Suspense fallback={<div className="viewer-loading"><Skeleton active/><p>Opening workspace diagnostics…</p></div>}><Viewer baseAPI={localAdmin?"/api/local-admin":"/api"} initialTab={initialTab} localAdmin={localAdmin} initialAssetId={initialAssetId}/></Suspense>:<div className="viewer-loading"><Empty image={<Database size={38} color="#7e95ba"/>} description={<span>The data explorer is being connected.<br/>Your conversations remain available.</span>}><Button onClick={()=>location.reload()}>Check again</Button></Empty></div>;}
