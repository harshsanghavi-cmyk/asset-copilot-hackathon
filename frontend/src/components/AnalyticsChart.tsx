import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import type { EChartsOption } from 'echarts';
/** Own the chart lifecycle explicitly so resize/cancel never retains a stale canvas. */
export default function AnalyticsChart({option,onSelect}:{option:EChartsOption;onSelect?:(name:string)=>void}){
 const node=useRef<HTMLDivElement>(null),instance=useRef<echarts.ECharts|undefined>(undefined),callback=useRef(onSelect);callback.current=onSelect;
 useEffect(()=>{if(!node.current)return;const chart=echarts.init(node.current,undefined,{renderer:'svg'});instance.current=chart;chart.on('click',(event:{name?:string})=>{if(event.name)callback.current?.(event.name);});const resize=new ResizeObserver(()=>{if(!chart.isDisposed())chart.resize();});resize.observe(node.current);return()=>{resize.disconnect();chart.dispose();instance.current=undefined;};},[]);
 useEffect(()=>{instance.current?.setOption(option,{notMerge:true});},[option]);
 return <div ref={node} className="analytics-chart" style={{height:245,width:'100%'}}/>;
}
