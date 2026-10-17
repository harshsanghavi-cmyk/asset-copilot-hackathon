import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, Card, Col, Descriptions, Drawer, Empty, Input, Select, Space, Spin, Statistic, Table, Tabs, Tag, Typography } from 'antd';
import './viewer.css';
import { Walkthrough } from './Walkthrough';

type Row = Record<string, any>;
type Page = { items: Row[]; total: number; limit?: number; offset?: number };
type Props = { baseAPI: string; initialTab?: string; localAdmin?: boolean; initialAssetId?: string };
const { Text, Title, Paragraph } = Typography;
const short = (value: unknown, max = 140) => { const text = typeof value === 'string' ? value : JSON.stringify(value ?? ''); return text.length > max ? text.slice(0, max) + '…' : text; };
function Json({ value }: { value: unknown }) { return <pre className="rv-json">{JSON.stringify(value, null, 2)?.slice(0, 32000)}</pre>; }

export function RetrievalViewer({ baseAPI, initialTab = 'overview', localAdmin = false, initialAssetId }: Props) {
  const [tab, setTab] = useState(initialTab);
  const [adminToken, setAdminToken] = useState('');
  const [connectedToken, setConnectedToken] = useState('');
  const [overview, setOverview] = useState<Row | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState<Page>({ items: [], total: 0 });
  const [pageNumber, setPageNumber] = useState(1);
  const [searchText, setSearchText] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [collection, setCollection] = useState('inspections');
  const [asset, setAsset] = useState('');
  const [sourceId, setSourceId] = useState('');
  const [detail, setDetail] = useState<Row | null>(null);
  const [detailTitle, setDetailTitle] = useState('');
  const [metric, setMetric] = useState('status');
  const [groupBy, setGroupBy] = useState('');
  const [area, setArea] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('2026-10-16');
  const [queryResult, setQueryResult] = useState<Row | null>(null);
  const [memoryScope, setMemoryScope] = useState('shared');
  const [memoryUser, setMemoryUser] = useState('');

  const request = useCallback(async (path: string, options?: RequestInit) => {
    const response = await fetch(baseAPI.replace(/\/$/, '') + path, { ...options, headers: { 'Content-Type': 'application/json', ...(localAdmin ? { 'X-Local-Admin': '1' } : {}), ...(connectedToken ? { 'X-Admin-Token': connectedToken } : {}), ...options?.headers } });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail?.message || body.detail || body.message || `Backend returned ${response.status}`);
    return body;
  }, [baseAPI, connectedToken, localAdmin]);

  const openDetail = useCallback(async (path: string, title: string) => {
    setLoading(true); setError('');
    try { setDetail(await request(path)); setDetailTitle(title); }
    catch (e) { setError(String((e as Error).message)); }
    finally { setLoading(false); }
  }, [request]);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    const params = new URLSearchParams({ limit: '20', offset: String((pageNumber - 1) * 20) });
    if (asset) params.set('asset_id', asset);
    if (sourceId) params.set('source_id', sourceId);
    if (appliedSearch) params.set('q', appliedSearch);
    try {
      if (tab === 'overview') { setOverview(await request('/retrieval/overview')); return; }
      if (tab === 'query' || tab === 'walkthrough') return;
      let path = `/retrieval/${tab}`;
      if (tab === 'records') path += '/' + collection;
      if (tab === 'memory') { params.set('scope', memoryScope); if (memoryUser) params.set('user_id', memoryUser); path = '/admin/memory'; }
      if (tab === 'changes') path = '/admin/memory/changes';
      if (tab === 'capsules') { path = '/admin/memory/status'; if (memoryUser) params.set('user_id', memoryUser); }
      const data = await request(path + '?' + params);
      if (tab === 'capsules') { setDetail(data); setDetailTitle('Memory capsules, pending deltas and compaction'); }
      else setPage({ items: data.items || [], total: data.total || 0 });
    } catch (e) { setError(String((e as Error).message)); setPage({ items: [], total: 0 }); }
    finally { setLoading(false); }
  }, [tab, pageNumber, asset, sourceId, appliedSearch, collection, memoryScope, memoryUser, request]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { setPageNumber(1); setPage({ items: [], total: 0 }); }, [tab, appliedSearch, collection, memoryScope, memoryUser]);

  const sourceLink = (id: string, label: string) => <Button type="link" size="small" onClick={() => void openDetail('/retrieval/sources/' + encodeURIComponent(id), label)}>{short(label, 68)}</Button>;
  const evidenceLink = (id: string) => <Button type="link" size="small" onClick={() => void openDetail('/retrieval/evidence/' + encodeURIComponent(id), 'Original evidence and source location')}>Inspect evidence</Button>;
  const columns = (): Row[] => {
    if (tab === 'sources') return [
      { title: 'Original source / path', dataIndex: 'path', width: 390, render: (v: string, r: Row) => sourceLink(r.id, v) },
      { title: 'Kind', dataIndex: 'kind', render: (v: string) => <Tag>{v}</Tag> },
      { title: 'Records', dataIndex: 'record_count' }, { title: 'Bytes', dataIndex: 'byte_count', render: (v: number) => v.toLocaleString() },
      { title: 'Method / state', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text>{r.enrichment_method}</Text><Tag color={r.status === 'indexed' ? 'green' : 'orange'}>{r.status}</Tag></Space> },
      { title: 'Drill down', render: (_: unknown, r: Row) => <Space><Button size="small" onClick={() => { setSourceId(r.id); setTab('records'); }}>Parsed</Button><Button size="small" onClick={() => { setSourceId(r.id); setTab('chunks'); }}>Index</Button></Space> },
    ];
    if (tab === 'records') return [
      { title: 'Record ID', dataIndex: 'id', width: 180 },
      { title: 'Original → effective / provenance', render: (_: unknown, r: Row) => <Space direction="vertical" size={2}><Text>{short(r.original, 200)}</Text>{r.corrections.length ? <Tag color="gold">{r.corrections.length} attributed correction(s)</Tag> : <Text type="secondary">No effective field change in supplied authority snapshot</Text>}</Space> },
      { title: 'Source', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text type="secondary">line {r.line}</Text>{sourceLink(r.source_id, r.source_id)}</Space> },
      { title: 'Inspect', render: (_: unknown, r: Row) => <Button size="small" onClick={() => { setDetail(r); setDetailTitle('Original and effective record'); }}>Compare fields</Button> },
    ];
    if (tab === 'chunks') return [
      { title: 'Source / section', width: 300, render: (_: unknown, r: Row) => <Space direction="vertical" size={0}>{sourceLink(r.source_id, r.path)}<Text strong>{r.section}</Text></Space> },
      { title: 'Indexed content (bounded preview)', dataIndex: 'preview', render: (v: string) => <Text>{v}</Text> },
      { title: 'Original UTF-8 span', render: (_: unknown, r: Row) => <Text code>{r.byte_start}…{r.byte_end}</Text> },
      { title: 'Method / verification', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Tag>{r.method}</Tag><Text type="secondary">{r.version}</Text><Tag color="green">{r.status}</Tag>{evidenceLink(r.id)}</Space> },
    ];
    if (tab === 'enrichments') return [
      { title: 'Subject / extracted fact', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text strong>{r.subject_id}</Text><Text>{r.predicate}</Text></Space> },
      { title: 'Value / qualifier', render: (_: unknown, r: Row) => <Text>{r.qualifier || ''} {r.value} {r.unit}</Text> },
      { title: 'Source', render: (_: unknown, r: Row) => sourceLink(r.source_id, r.path) },
      { title: 'Enrichment status', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Tag>{r.method}</Tag><Text>{r.version}</Text><Badge status="success" text={r.status}/>{evidenceLink(r.id)}</Space> },
    ];
    if (tab === 'traces') return [
      { title: 'When / operation', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text strong>{r.operation}</Text><Text type="secondary">{r.created_at}</Text></Space> },
      { title: 'Input text', dataIndex: 'input_text', render: (v: string) => short(v || 'Typed provider query', 180) },
      { title: 'Coverage', render: (_: unknown, r: Row) => <Tag color={r.coverage?.status === 'complete' ? 'green' : 'orange'}>{r.coverage?.status}</Tag> },
      { title: 'Time', dataIndex: 'elapsed_ms', render: (v: number) => `${v ?? '—'} ms` },
      { title: 'Inspect execution', render: (_: unknown, r: Row) => <Button onClick={() => void openDetail('/retrieval/traces/' + r.trace_id, 'Actual retrieval execution — parameters redacted')}>Plan → SQL → evidence</Button> },
    ];
    if (tab === 'memory') return [
      { title: 'Scope / owner', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Tag color={r.scope === 'private' ? 'purple' : 'cyan'}>{r.scope}</Tag><Text>{r.owner_user_id || 'All authorized users'}</Text></Space> },
      { title: 'Kind / remembered content', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text strong>{r.kind}</Text><Text>{short(r.preview, 240)}</Text></Space> },
      { title: 'Created / updated', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Text>{r.created_at}</Text><Text type="secondary">{r.updated_at || 'No later update'}</Text></Space> },
      { title: 'State / revision', render: (_: unknown, r: Row) => <Space direction="vertical" size={0}><Tag>{r.status}</Tag><Text>revision {r.knowledge_revision ?? '—'}</Text></Space> },
      { title: 'Provenance', render: (_: unknown, r: Row) => <Button onClick={() => void openDetail('/admin/memory/' + encodeURIComponent(r.id), 'Canonical memory, provenance and validity')}>Inspect</Button> },
    ];
    return [{ title: 'Kind / ID', render: (_: unknown, r: Row) => <Text>{r.kind || r.event_type || r.id}</Text> }, { title: 'Bounded diagnostic record', render: (_: unknown, r: Row) => <Text>{short(r, 550)}</Text> }, { title: 'Details', render: (_: unknown, r: Row) => <Button onClick={() => { setDetail(r); setDetailTitle('Diagnostic detail'); }}>Inspect</Button> }];
  };

  const runQuery = async (lexical = false) => {
    if (!lexical && searchText.trim()) { setError('Text is present in the report-search box. Use Search maintenance report text, or clear that box before executing a manual plan. No status query was executed.'); return; }
    setLoading(true); setError('');
    try {
      const result = lexical
        ? await request('/retrieval/search', { method: 'POST', body: JSON.stringify({ terms: searchText, kind: 'report', ...(asset ? { asset_id: asset } : {}), limit: 8, budget: 2000 }) })
        : await request('/retrieval/query', { method: 'POST', body: JSON.stringify({ collection, metric, group_by: groupBy ? [groupBy] : [], filters: { ...(asset ? { asset_id: asset } : {}), ...(area ? { area_id: area } : {}) }, ...(start ? { start } : {}), end, limit: 50, input_text: 'Manual typed builder: ' + metric + ' on ' + collection }) });
      setQueryResult(result);
    } catch (e) { setError(String((e as Error).message)); }
    finally { setLoading(false); }
  };

  const filters = <div className="rv-filters"><Input.Search placeholder="Filter source paths / memory text" value={searchText} onChange={e => setSearchText(e.target.value)} onSearch={setAppliedSearch} enterButton="Filter" allowClear/><Input placeholder="Optional well ID" value={asset} onChange={e => setAsset(e.target.value)} allowClear/>{sourceId && <Tag closable onClose={() => setSourceId('')}>Source filter {short(sourceId, 24)}</Tag>}{tab === 'records' && <Select value={collection} onChange={setCollection} options={['assets', 'inspections', 'maintenance', 'regulatory_events', 'context_notes', 'areas', 'teams', 'users'].map(value => ({ value, label: value }))}/>}</div>;
  const list = <>{filters}<Table<Row> rowKey={r => r.id || r.trace_id || JSON.stringify(r)} columns={columns()} dataSource={page.items} loading={loading} size="middle" scroll={{ x: 1050 }} pagination={{ current: pageNumber, pageSize: 20, total: page.total, showSizeChanger: false, showTotal: total => `${total.toLocaleString()} records · 20 per page`, onChange: setPageNumber }}/></>;
  const query = <><Alert type="info" showIcon message="Two separate operations: report text search OR explicit manual plan" description="Natural-language report requests must use the report-search action. The manual controls never interpret the search text. Actual Gemma planning is not run here; provider errors in connected chat remain visible."/><div className="rv-query-grid"><Input.TextArea aria-label="Report text search" placeholder="Report content terms, for example: found crude oil on the pad. This text is ONLY used by Search maintenance reports below." value={searchText} onChange={e => setSearchText(e.target.value)} rows={2}/><Card size="small" title="Manual typed query builder — execute only these explicit controls"><Paragraph type="secondary">The report-search text above is not a natural-language planner and is not used by this manual operation.</Paragraph><Space wrap><Select aria-label="Collection" value={collection} onChange={setCollection} options={['assets', 'inspections', 'maintenance', 'regulatory_events', 'context_notes'].map(value => ({ value }))}/><Select aria-label="Metric" value={metric} onChange={setMetric} options={['records', 'status', 'temperature_series', 'spills', 'downtime_days', 'spill_count', 'spill_volume_bbl', 'maintenance_cost_usd', 'corrective_count', 'rca', 'containment', 'compliance', 'count'].map(value => ({ value }))}/><Select aria-label="Group by" value={groupBy} onChange={setGroupBy} options={['', 'asset_id', 'area_id', 'month', 'well_type', 'equipment_kind'].map(value => ({ value, label: value || 'Default grouping' }))}/></Space><Space wrap><Input aria-label="Well ID" placeholder="Well ID (optional)" value={asset} onChange={e => setAsset(e.target.value)}/><Input aria-label="Area ID" placeholder="Area ID (optional)" value={area} onChange={e => setArea(e.target.value)}/><Input aria-label="Start date" type="date" value={start} onChange={e => setStart(e.target.value)}/><Input aria-label="End date" type="date" value={end} onChange={e => setEnd(e.target.value)}/></Space><Space><Button type="primary" loading={loading} disabled={Boolean(searchText.trim())} onClick={() => void runQuery()}>Run explicit manual plan</Button></Space></Card><Space><Button type="primary" loading={loading} disabled={!searchText.trim()} onClick={() => void runQuery(true)}>Search maintenance report text</Button><Text type="secondary">Lexical ranked subset only; no claim of a complete matching asset list. Gemma planning is not invoked.</Text></Space></div>{queryResult && <><Space className="rv-result-heading"><Tag color={queryResult.coverage?.status === 'complete' ? 'green' : 'orange'}>{queryResult.coverage?.status}</Tag><Text>{queryResult.coverage?.exhaustive_factual_scope === false ? 'Lexical matching chunks (not matching assets): ' : 'Matched population: '}{queryResult.coverage?.matching ?? 'unknown'}</Text><Button onClick={() => void openDetail('/retrieval/traces/' + queryResult.trace_id, 'Query plan, tables, redacted SQL and selected/omitted evidence')}>Inspect real execution trace</Button></Space><Table<Row> rowKey={r => r.row_id || r.id} scroll={{ x: 1000 }} size="small" dataSource={queryResult.rows || queryResult.items || []} columns={(queryResult.items ? ['asset_id', 'path', 'section', 'excerpt', 'score', 'evidence_id'] : Object.keys((queryResult.rows || [])[0] || {}).filter(k => !['text', 'evidence_refs'].includes(k)).slice(0, 12)).map(key => ({ title: key, dataIndex: key, render: (v: unknown) => key === 'evidence_id' && typeof v === 'string' ? evidenceLink(v) : short(v, key === 'excerpt' ? 500 : 120) }))} pagination={{ pageSize: 10, showSizeChanger: false }}/><Json value={{ coverage: queryResult.coverage, warnings: queryResult.warnings, token_accounting: queryResult.token_accounting, omitted_evidence: queryResult.omitted_evidence }}/></>}</>;
  const overviewContent = overview ? <><RowGutter counts={overview.counts || {}}/><Card title="Where source content is stored"><Table<Row> rowKey="folder" pagination={false} size="small" dataSource={overview.mappings || []} columns={[{ title: 'Original folder / file', dataIndex: 'folder', width: 300 }, { title: 'Derived table / store', dataIndex: 'tables', render: (v: string[]) => v.map(x => <Tag key={x}>{x}</Tag>) }, { title: 'Saved content and purpose', dataIndex: 'content' }, { title: 'How it is produced', dataIndex: 'method' }]} scroll={{ x: 950 }}/></Card><div className="rv-overview-grid"><Card title="Stores and authority"><Json value={overview.storage}/></Card><Card title="Relations and cardinalities"><Table pagination={false} size="small" rowKey={r => r[0]} dataSource={overview.relations || []} columns={[{ title: 'From', render: (_: unknown, r: string[]) => r[0] }, { title: 'To', render: (_: unknown, r: string[]) => r[1] }, { title: 'Relationship', render: (_: unknown, r: string[]) => r[2] }]}/></Card><Card title="Actual schema fields"><Json value={overview.schemas}/></Card><Card title="Index build and enrichment manifest"><Json value={overview.manifest}/></Card></div></> : <Empty description={loading ? 'Reading index manifest…' : 'Connect to the backend to inspect actual indexed data'}/>;

  return <section className="retrieval-viewer"><div className="rv-header"><div><Text className="rv-eyebrow">DATA & MEMORY OBSERVATORY</Text><Title level={2}>Inspect the evidence pipeline</Title><Paragraph type="secondary">Original files → parsed records → deterministic enrichment → exact queries and cited passages.</Paragraph></div><Tag color="gold">Replaceable candidate · pending review</Tag></div><Card className="rv-access" size="small">{localAdmin ? <Space><Badge status="processing"/><Text>Explicit loopback administrator diagnostics · token remains server-side</Text><Button onClick={() => void load()}>Refresh</Button></Space> : <Space wrap><Input.Password aria-label="Local administrator token" placeholder="Local administrator token (never stored)" value={adminToken} onChange={e => setAdminToken(e.target.value)} autoComplete="off"/><Button onClick={() => { setConnectedToken(adminToken); setError(''); }}>Connect diagnostic access</Button><Button onClick={() => void load()}>Refresh</Button><Text type="secondary">Explicit local admin capability; a chat user ID grants no admin access.</Text></Space>}</Card>{error && <Alert className="rv-alert" type="error" showIcon closable onClose={() => setError('')} message="Diagnostic request unavailable" description={error}/>}<Spin spinning={loading && !page.items.length}><Tabs activeKey={tab} onChange={setTab} items={[{ key: 'walkthrough', label: 'Asset walkthrough', children: <Walkthrough request={request} initialAssetId={initialAssetId}/> }, { key: 'overview', label: 'Storage map', children: overviewContent }, { key: 'sources', label: 'Sources', children: list }, { key: 'records', label: 'Parsed / effective', children: list }, { key: 'chunks', label: 'Chunks & index', children: list }, { key: 'enrichments', label: 'Enrichment', children: <><Alert type="info" showIcon message="Deterministic enrichment only" description="Containment facts, source spans, entities/protocol tags and supported rules are parsed locally. Gemma enrichment is an injected seam and has not run here."/>{list}</> }, { key: 'query', label: 'Query inspector', children: query }, { key: 'traces', label: 'Execution traces', children: list }, { key: 'memory', label: 'Saved memory', children: <><Space className="rv-memory-filters"><Select value={memoryScope} onChange={setMemoryScope} options={[{ value: 'shared', label: 'Shared operational facts' }, { value: 'private', label: 'Private facts (admin only)' }]}/><Input placeholder="Owner user ID (optional)" value={memoryUser} onChange={e => setMemoryUser(e.target.value)}/></Space>{list}</> }, { key: 'changes', label: 'Memory changes', children: list }, { key: 'capsules', label: 'Capsules / compaction', children: <><Paragraph>Inspect loaded-memory capsule versions, pending deltas and summary jobs through the backend's admin API.</Paragraph><Input placeholder="User ID (optional)" value={memoryUser} onChange={e => setMemoryUser(e.target.value)}/><Button onClick={() => void load()}>Inspect capsule state</Button></> }, { key: 'issues', label: 'Errors & unknowns', children: list }]}/></Spin><Drawer open={Boolean(detail)} width={Math.min(900, window.innerWidth - 32)} title={detailTitle} onClose={() => setDetail(null)}><Alert type="info" showIcon message="Bounded source / diagnostic detail" description="Original source content and assertions remain separate from effective corrections and independently verified behavior."/>{detail?.path && <Descriptions className="rv-details" column={1} items={[{ key: 'path', label: 'Source path', children: detail.path }, { key: 'hash', label: 'Content hash', children: <Text code>{detail.content_hash}</Text> }, { key: 'span', label: 'Source span', children: detail.byte_start != null ? `${detail.byte_start}–${detail.byte_end} UTF-8 bytes` : detail.line ? `JSONL line ${detail.line}` : 'Bounded file preview' }]}/>}<Json value={detail}/></Drawer></section>;
}

function RowGutter({ counts }: { counts: Row }) { return <div className="rv-stats">{['sources', 'assets', 'inspections', 'maintenance', 'chunks', 'facts'].map(key => <Card key={key} size="small"><Statistic title={key === 'facts' ? 'Extracted assertions' : key} value={counts[key] ?? 0}/></Card>)}</div>; }
export function AdminViewer(props: Props) { return <RetrievalViewer {...props} initialTab={props.initialTab || 'memory'}/>; }
export default RetrievalViewer;
