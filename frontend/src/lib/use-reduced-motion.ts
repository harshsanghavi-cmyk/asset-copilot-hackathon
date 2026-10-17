import { useSyncExternalStore } from 'react';
const query='(prefers-reduced-motion: reduce)';
function subscribe(listener:()=>void){const media=window.matchMedia(query);media.addEventListener('change',listener);return()=>media.removeEventListener('change',listener);}
function snapshot(){return typeof window!=='undefined'&&window.matchMedia(query).matches;}
/** Subscribe explicitly so a system change updates charts/maps as well as Motion. */
export function useReducedMotion(){return useSyncExternalStore(subscribe,snapshot,()=>false);}
