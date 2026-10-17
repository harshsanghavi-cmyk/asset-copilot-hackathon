SCHEMA_VERSION = "asset-source-v2"
PARSER_VERSION = "deterministic-sections-v1"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE sources(id TEXT PRIMARY KEY, path TEXT, kind TEXT, asset_id TEXT,
 root_alias TEXT, content_hash TEXT, byte_count INTEGER, record_count INTEGER DEFAULT 0,
 status TEXT DEFAULT 'indexed', preview TEXT, enrichment_method TEXT DEFAULT 'deterministic',
 enrichment_version TEXT, enrichment_status TEXT DEFAULT 'complete');
CREATE TABLE records(id TEXT PRIMARY KEY, collection TEXT, source_id TEXT, line INTEGER,
 content_hash TEXT, raw_json TEXT, FOREIGN KEY(source_id) REFERENCES sources(id));
CREATE TABLE evidence_map(handle TEXT PRIMARY KEY,record_id TEXT);
CREATE TABLE record_origins(record_id TEXT,source_id TEXT,line INTEGER,
 UNIQUE(record_id,source_id,line));
CREATE TABLE assets(asset_id TEXT PRIMARY KEY,name TEXT,well_type TEXT,area_id TEXT,team_id TEXT,
 in_charge_user_id TEXT,lat REAL,lon REAL,installed_on TEXT,recorded_status TEXT);
CREATE TABLE areas(area_id TEXT PRIMARY KEY,name TEXT,team_id TEXT);
CREATE TABLE teams(team_id TEXT PRIMARY KEY,name TEXT,lead_user_id TEXT);
CREATE TABLE users(user_id TEXT PRIMARY KEY,name TEXT,role TEXT,team_id TEXT);
CREATE TABLE equipment(equipment_id TEXT PRIMARY KEY,asset_id TEXT,kind TEXT,model TEXT);
CREATE TABLE inspections(inspection_id TEXT PRIMARY KEY,asset_id TEXT,inspected_at TEXT,
 inspector_user_id TEXT,method TEXT,ambient_milli INTEGER,wellhead_milli INTEGER,
 spill_detected INTEGER,spill_area_milli INTEGER,volume_milli INTEGER,notes TEXT);
CREATE TABLE maintenance(maintenance_id TEXT PRIMARY KEY,asset_id TEXT,started_at TEXT,
 completed_at TEXT,maintenance_type TEXT,equipment_kind TEXT,technician_user_id TEXT,
 cost_cents INTEGER,downtime_milli INTEGER,inspection_id TEXT,report_path TEXT,report_source_id TEXT);
CREATE TABLE regulatory_events(event_id TEXT PRIMARY KEY,asset_id TEXT,date TEXT,
 event_type TEXT,protocol_id TEXT,inspection_id TEXT,hours_milli INTEGER,fine_cents INTEGER,status TEXT);
CREATE TABLE context_notes(note_id TEXT PRIMARY KEY,asset_id TEXT,author_user_id TEXT,
 created_at TEXT,note_type TEXT,inspection_id TEXT,text TEXT,valid_from TEXT,valid_to TEXT);
CREATE TABLE baseline_corrections(id TEXT PRIMARY KEY,record_id TEXT,field TEXT,
 value_json TEXT,author_user_id TEXT,created_at TEXT,reason TEXT);
CREATE TABLE chunks(id TEXT PRIMARY KEY,source_id TEXT,section TEXT,ordinal INTEGER,
 byte_start INTEGER,byte_end INTEGER,text TEXT,protocols_json TEXT,entities_json TEXT,
 method TEXT,version TEXT,status TEXT);
CREATE VIRTUAL TABLE chunk_fts USING fts5(chunk_id UNINDEXED,title,body,tokenize='porter unicode61');
CREATE TABLE facts(id TEXT PRIMARY KEY,source_id TEXT,subject_id TEXT,predicate TEXT,
 value_json TEXT,unit TEXT,byte_start INTEGER,byte_end INTEGER,qualifier TEXT,
 method TEXT,version TEXT,status TEXT);
CREATE TABLE rules(id TEXT PRIMARY KEY,well_type TEXT,predicate TEXT,value_milli INTEGER,
 source_id TEXT,section TEXT,inherit_from TEXT,version TEXT,status TEXT);
CREATE TABLE issues(id INTEGER PRIMARY KEY,kind TEXT,source_id TEXT,record_id TEXT,detail TEXT);
CREATE TABLE manifest(key TEXT PRIMARY KEY,value_json TEXT);
CREATE INDEX inspection_asset_time ON inspections(asset_id,inspected_at);
CREATE INDEX maintenance_asset_time ON maintenance(asset_id,started_at);
CREATE INDEX maintenance_trigger ON maintenance(inspection_id);
CREATE INDEX regulator_trigger ON regulatory_events(inspection_id);
CREATE INDEX records_collection ON records(collection,id);
CREATE INDEX records_source ON records(source_id);
CREATE INDEX sources_path_kind ON sources(path,kind);
CREATE INDEX chunks_source ON chunks(source_id,ordinal);
CREATE INDEX facts_subject ON facts(subject_id,predicate);
"""

MAPPINGS = [
    {"folder": "fleet/areas.json", "tables": ["areas", "teams"], "content": "Area/team directory; membership retained in raw source records", "method": "typed JSON"},
    {"folder": "fleet/users.json", "tables": ["users"], "content": "Person display names, roles and teams", "method": "typed JSON"},
    {"folder": "assets/*/metadata.json", "tables": ["assets", "equipment"], "content": "Well ownership, type, location and nested equipment; raw metadata retained", "method": "typed JSON + equipment expansion"},
    {"folder": "assets/*/inspections.jsonl", "tables": ["inspections"], "content": "Observed temperature and spill facts, source line and original JSON", "method": "streamed JSONL; decimal-scaled values"},
    {"folder": "assets/*/maintenance.jsonl", "tables": ["maintenance"], "content": "Jobs/costs and declared inspection/report links", "method": "streamed JSONL + validated links"},
    {"folder": "assets/*/regulatory-events.jsonl", "tables": ["regulatory_events"], "content": "Incident-linked notices, responses, inspections and fines", "method": "streamed JSONL"},
    {"folder": "assets/*/context.jsonl", "tables": ["context_notes", "baseline_corrections"], "content": "Attributed notes; only explicit supported formal corrections affect values", "method": "typed note + bounded negated-crude parser"},
    {"folder": "assets/*/maintenance-reports/*.md", "tables": ["sources", "chunks", "facts", "chunk_fts"], "content": "Original report preview; exact UTF-8 sections and containment facts; searchable lexical index", "method": "deterministic sections/regex; no LLM"},
    {"folder": "fleet/well-types/*.md; fleet/sops/*.md", "tables": ["sources", "chunks", "rules", "chunk_fts"], "content": "Manual/SOP text, protocol tags, source-backed production rules and inheritance", "method": "deterministic sections + supported rule parser"},
]

RELATIONS = [
    ["assets.area_id", "areas.area_id", "many to one"],
    ["assets.well_type", "rules.well_type", "one type to applicable rules"],
    ["inspections.asset_id", "assets.asset_id", "many to one"],
    ["maintenance.inspection_id", "inspections.inspection_id", "optional many to one"],
    ["maintenance.report_source_id", "sources.id", "optional declared report link"],
    ["regulatory_events.inspection_id", "inspections.inspection_id", "optional many to one"],
    ["context_notes.inspection_id", "inspections.inspection_id", "formal correction target when supplied"],
    ["records.source_id", "sources.id", "source line to parsed record"],
    ["chunks.source_id", "sources.id", "exact source spans; rebuildable FTS projection"],
]
