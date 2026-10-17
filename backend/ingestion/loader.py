"""Streaming, bounded ingestion. Originals are never modified or handed to a model."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from decimal import Decimal
from pathlib import Path
from typing import Iterable
from .schema import SCHEMA, SCHEMA_VERSION, PARSER_VERSION


class IngestionError(ValueError):
    pass


def uid(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(value.encode()).hexdigest()[:24]


def scaled(value, scale=1000):
    if value is None:
        return None
    number = Decimal(str(value)) * scale
    if not number.is_finite() or number != number.to_integral_value():
        raise IngestionError("unsupported numeric precision or non-finite value")
    return int(number)


def issue(db, kind, source_id, record_id, detail):
    db.execute("INSERT INTO issues(kind,source_id,record_id,detail) VALUES(?,?,?,?)", (kind, source_id, record_id, str(detail)[:600]))


def add_record(db, collection, rid, row, source, line):
    raw = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    old = db.execute("SELECT content_hash FROM records WHERE id=?", (rid,)).fetchone()
    if old:
        if old[0] != hashed:
            issue(db, "conflicting_record_id", source, rid, "Same ID has different content; retained original, conflicting version not activated")
        else:
            db.execute("INSERT OR IGNORE INTO record_origins VALUES(?,?,?)", (rid, source, line))
        return False
    db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)", (rid, collection, source, line, hashed, raw))
    db.execute("INSERT INTO evidence_map VALUES(?,?)", (uid("ev_", rid), rid))
    db.execute("INSERT INTO record_origins VALUES(?,?,?)", (rid, source, line))
    return True


def parse_record(db, collection, r, source, line):
    keys = {"assets": "asset_id", "areas": "area_id", "teams": "team_id", "users": "user_id", "inspections": "inspection_id", "maintenance": "maintenance_id", "regulatory_events": "event_id", "context_notes": "note_id"}
    rid = r[keys[collection]]
    if not isinstance(rid, str) or not rid or len(rid) > 128:
        raise IngestionError("invalid record ID")
    if not add_record(db, collection, rid, r, source, line):
        return
    if collection == "assets":
        loc = r.get("location", {})
        db.execute("INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?,?)", (rid, r.get("name"), r["well_type"], r["area_id"], r["team_id"], r.get("in_charge_user_id"), loc.get("lat"), loc.get("lon"), r.get("installed_on"), r.get("recorded_status")))
        for e in r.get("equipment", []):
            db.execute("INSERT OR IGNORE INTO equipment VALUES(?,?,?,?)", (e["equipment_id"], rid, e["kind"], e.get("model")))
    elif collection == "areas":
        db.execute("INSERT INTO areas VALUES(?,?,?)", (rid, r["name"], r["team_id"]))
    elif collection == "teams":
        db.execute("INSERT INTO teams VALUES(?,?,?)", (rid, r["name"], r.get("lead_user_id")))
    elif collection == "users":
        db.execute("INSERT INTO users VALUES(?,?,?,?)", (rid, r["name"], r.get("role"), r.get("team_id")))
    elif collection == "inspections":
        db.execute("INSERT INTO inspections VALUES(?,?,?,?,?,?,?,?,?,?,?)", (rid, r["asset_id"], r["inspected_at"], r["inspector_user_id"], r["method"], scaled(r["ambient_temp_c"]), scaled(r["wellhead_temp_c"]), int(r["spill_detected"]), scaled(r.get("spill_area_pct")), scaled(r.get("spill_est_volume_bbl")), r.get("notes")))
    elif collection == "maintenance":
        db.execute("INSERT INTO maintenance VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (rid, r["asset_id"], r["started_at"], r["completed_at"], r["maintenance_type"], r["equipment_kind"], r["technician_user_id"], scaled(r["cost_usd"]["total"], 100), scaled(r["downtime_hours"]), r.get("triggered_by_inspection_id"), r.get("report_file"), None))
    elif collection == "regulatory_events":
        db.execute("INSERT INTO regulatory_events VALUES(?,?,?,?,?,?,?,?,?)", (rid, r["asset_id"], r["date"], r["event_type"], r.get("protocol_id"), r.get("related_inspection_id"), scaled(r.get("hours_to_report")), scaled(r.get("fine_usd"), 100), r.get("status")))
    elif collection == "context_notes":
        db.execute("INSERT INTO context_notes VALUES(?,?,?,?,?,?,?,?,?)", (rid, r["asset_id"], r["author_user_id"], r["created_at"], r["note_type"], r.get("inspection_id"), r["text"], r.get("valid_from"), r.get("valid_to")))
        if r["note_type"] == "data_correction":
            field, value = r.get("field"), r.get("corrected_value")
            supported = field in {"wellhead_temp_c", "ambient_temp_c", "spill_detected", "spill_est_volume_bbl"}
            valid_value = isinstance(value, bool) if field == "spill_detected" else isinstance(value, (int, float)) and not isinstance(value, bool)
            if r.get("inspection_id") and supported and valid_value:
                if field != "spill_detected":
                    scaled(value)
                db.execute("INSERT INTO baseline_corrections VALUES(?,?,?,?,?,?,?)", (rid, r["inspection_id"], field, json.dumps(value), r["author_user_id"], r["created_at"], r["text"]))
            else:
                issue(db, "unresolved_correction", source, rid, "Unsupported typed correction target/field/value retained without activation")
        elif r["note_type"] == "correction":
            if r.get("inspection_id") and re.search(r"\b(?:not a (?:crude )?spill|no crude)\b", r["text"], re.I):
                db.execute("INSERT INTO baseline_corrections VALUES(?,?,?,?,?,?,?)", (rid, r["inspection_id"], "spill_detected", "false", r["author_user_id"], r["created_at"], r["text"]))
            else:
                issue(db, "unresolved_correction", source, rid, "Formal correction retained but unsupported prose requires typed review")


def parse_markdown(db, source, path, text, chunk_words=120):
    raw = text.encode()
    headings = list(re.finditer(r"^#{1,3} .+$", text, re.M))
    if not headings:
        headings = [None]
    for i, heading in enumerate(headings):
        section = heading.group().lstrip("# ") if heading else "Document"
        start = heading.end() if heading else 0
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        words = list(re.finditer(r"\S+", text[start:end]))
        for offset in range(0, len(words), chunk_words):
            group = words[offset:offset + chunk_words]
            lo, hi = start + group[0].start(), start + group[-1].end()
            b0, b1 = len(text[:lo].encode()), len(text[:hi].encode())
            body = raw[b0:b1].decode()
            cid = uid("chunk_", f"{source}:{b0}:{b1}")
            protocols = sorted(set(re.findall(r"\b(?:(?:SR|RC|WS)-\d{2}|OPS-\d+|MOC-\d{4}-\d+)\b", body)))
            entities = sorted(set(re.findall(r"\b(?:WELL-\d+|INS-\d+-\d+|MNT-\d+-\d+)\b", body)))
            db.execute("INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (cid, source, section, i * 10000 + offset, b0, b1, body, json.dumps(protocols), json.dumps(entities), "deterministic_section_split", PARSER_VERSION, "span_verified"))
            db.execute("INSERT INTO chunk_fts VALUES(?,?,?)", (cid, section, body))
        if "/well-types/" in "/" + path and "production temperature rule" in section.lower():
            plain = re.sub(r"[*_]", "", text[start:end])
            match = re.search(r"at least\s+(\d+(?:\.\d+)?)\s*°C above\s+ambient", plain, re.I)
            well_type = Path(path).stem
            if match:
                db.execute("INSERT OR IGNORE INTO rules VALUES(?,?,?,?,?,?,?,?,?)", (uid("rule_", source + section), well_type, "production_delta_c", scaled(match.group(1)), source, section, None, PARSER_VERSION, "source_span_checked"))
            else:
                issue(db, "unsupported_rule", source, None, "Production section could not be parsed; no default threshold applied")
    if "/maintenance-reports/" in "/" + path:
        subject = re.search(r"^# Maintenance Report[^\n]*?(MNT-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)", text)
        subject_id = subject[1] if subject else None
        pattern = re.compile(r"contained (?:about )?(\d+(?:\.\d+)?) hours after (?:discovery|the inspection)", re.I)
        for match in pattern.finditer(text):
            lo, hi = len(text[:match.start()].encode()), len(text[:match.end()].encode())
            db.execute("INSERT INTO facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (uid("fact_", source + str(lo)), source, subject_id, "containment_hours", json.dumps(str(Decimal(match[1]))), "hour", lo, hi, "about" if "about" in match[0].lower() else None, "deterministic_pattern", PARSER_VERSION, "span_verified"))


def _files(root: Path):
    for p in sorted((root / "fleet").glob("**/*")):
        if p.is_file() and p.suffix in (".json", ".md") and not any(x.startswith(".") for x in p.relative_to(root).parts):
            yield p
    for asset in sorted((root / "assets").iterdir()):
        if not asset.is_dir() or asset.name.startswith("."):
            continue
        for name in ("metadata.json", "inspections.jsonl", "maintenance.jsonl", "regulatory-events.jsonl", "context.jsonl"):
            if (asset / name).is_file():
                yield asset / name
        yield from sorted((asset / "maintenance-reports").glob("*.md"))


def build_index(dataset_roots: Iterable[Path], db_path: Path, namespace="asset-field"):
    """Build a replacement index into a sibling staging DB, then publish atomically."""
    start = time.perf_counter()
    roots = [Path(r).resolve() for r in dataset_roots]
    roots = [r / "sample-data" if (r / "sample-data/fleet").is_dir() else r for r in roots]
    if not roots or any(not (r / "fleet").is_dir() or not (r / "assets").is_dir() for r in roots):
        raise IngestionError("Each dataset root requires fleet/ and assets/; originals remain untouched")
    db_path = Path(db_path).resolve()
    if any(db_path.is_relative_to(r) for r in roots):
        raise IngestionError("Index cannot be created inside immutable dataset roots")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    staging = db_path.with_suffix(".building.sqlite")
    if staging.exists():
        staging.unlink()
    db = sqlite3.connect(staging)
    db.executescript(SCHEMA)
    manifest = []
    paths = {}
    try:
        for root_index, root in enumerate(roots):
            for path in _files(root):
                if not path.resolve().is_relative_to(root):
                    continue
                rel = path.relative_to(root).as_posix()
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    while block := stream.read(65536):
                        digest.update(block)
                hashed = digest.hexdigest()
                sid = uid("src_", namespace + rel + hashed)
                manifest.append((rel, hashed))
                paths[(root_index, rel)] = sid
                if db.execute("SELECT 1 FROM sources WHERE id=?", (sid,)).fetchone():
                    continue
                asset = path.parent.parent.name if path.parent.name == "maintenance-reports" else path.parent.name if path.parent.parent.name == "assets" else None
                kind = "report" if path.parent.name == "maintenance-reports" else "manual" if path.parent.name == "well-types" else "sop" if path.parent.name == "sops" else path.stem.replace("-", "_")
                with path.open("rb") as f:
                    preview = f.read(8192).decode("utf-8", errors="replace")
                db.execute("INSERT INTO sources(id,path,kind,asset_id,root_alias,content_hash,byte_count,preview,enrichment_version) VALUES(?,?,?,?,?,?,?,?,?)", (sid, rel, kind, asset, f"root-{root_index + 1}", hashed, path.stat().st_size, preview, PARSER_VERSION))
                try:
                    if path.suffix == ".md":
                        if path.stat().st_size > 1048576:
                            raise IngestionError("Markdown exceeds 1 MiB bounded parser limit")
                        parse_markdown(db, sid, rel, path.read_text())
                    elif path.suffix == ".jsonl":
                        collection = {"inspections": "inspections", "maintenance": "maintenance", "regulatory-events": "regulatory_events", "context": "context_notes"}[path.stem]
                        with path.open("rb") as f:
                            line = 0
                            while raw := f.readline(1048577):
                                line += 1
                                if len(raw) > 1048576:
                                    while raw and not raw.endswith(b"\n"):
                                        raw = f.readline(1048577)
                                    issue(db, "oversized_line", sid, None, f"JSONL line {line} exceeds 1 MiB")
                                    continue
                                if not raw.strip():
                                    continue
                                db.execute("SAVEPOINT record_parse")
                                try:
                                    r = json.loads(raw)
                                    if r.get("asset_id") != asset:
                                        raise IngestionError("asset_id disagrees with source folder")
                                    parse_record(db, collection, r, sid, line)
                                    db.execute("RELEASE record_parse")
                                except (ValueError, KeyError, TypeError, sqlite3.Error) as error:
                                    db.execute("ROLLBACK TO record_parse")
                                    db.execute("RELEASE record_parse")
                                    issue(db, "record_parse_error", sid, None, f"line {line}: {type(error).__name__}: {error}")
                    else:
                        if path.stat().st_size > 1048576:
                            raise IngestionError("JSON exceeds bounded parser limit")
                        r = json.loads(path.read_text())
                        if path.name == "metadata.json":
                            parse_record(db, "assets", r, sid, 1)
                        elif path.name == "areas.json":
                            for collection in ("areas", "teams"):
                                for row in r.get(collection, []):
                                    parse_record(db, collection, row, sid, 1)
                        elif path.name == "users.json":
                            for row in r.get("users", []):
                                parse_record(db, "users", row, sid, 1)
                    db.execute("UPDATE sources SET record_count=(SELECT count(*) FROM records WHERE source_id=?) WHERE id=?", (sid, sid))
                except (ValueError, KeyError, TypeError, sqlite3.Error) as error:
                    issue(db, "source_parse_error", sid, None, f"{type(error).__name__}: {error}")
                    db.execute("UPDATE sources SET status='partial',enrichment_status='partial' WHERE id=?", (sid,))
                if len(manifest) % 100 == 0:
                    db.commit()
        # Explicit report links, never fabricated filenames. Multiple roots retain source origins.
        for mid, asset, link in db.execute("SELECT maintenance_id,asset_id,report_path FROM maintenance WHERE report_path IS NOT NULL").fetchall():
            rel = (Path("assets") / asset / link).as_posix()
            if Path(link).is_absolute() or ".." in Path(link).parts:
                issue(db, "unsafe_report_link", None, mid, "Rejected path outside asset directory")
                continue
            matches = db.execute("SELECT id FROM sources WHERE path=? AND kind='report'", (rel,)).fetchall()
            if len(matches) == 1:
                db.execute("UPDATE maintenance SET report_source_id=? WHERE maintenance_id=?", (matches[0][0], mid))
            else:
                issue(db, "missing_or_conflicting_report", None, mid, "Declared report link has zero or conflicting source versions")
        checks = [
            ("inspection_asset", "SELECT i.inspection_id FROM inspections i LEFT JOIN assets a ON a.asset_id=i.asset_id WHERE a.asset_id IS NULL"),
            ("maintenance_trigger", "SELECT m.maintenance_id FROM maintenance m LEFT JOIN inspections i ON i.inspection_id=m.inspection_id WHERE m.inspection_id IS NOT NULL AND (i.inspection_id IS NULL OR i.asset_id!=m.asset_id)"),
            ("regulator_trigger", "SELECT e.event_id FROM regulatory_events e LEFT JOIN inspections i ON i.inspection_id=e.inspection_id WHERE e.inspection_id IS NOT NULL AND (i.inspection_id IS NULL OR e.asset_id!=i.asset_id)"),
            ("correction_target", "SELECT c.id FROM baseline_corrections c JOIN context_notes n ON n.note_id=c.id LEFT JOIN inspections i ON i.inspection_id=c.record_id WHERE i.inspection_id IS NULL OR i.asset_id!=n.asset_id"),
        ]
        for kind, query in checks:
            for (rid,) in db.execute(query).fetchall():
                issue(db, kind, None, rid, "Broken or cross-asset reference")
                if kind == "correction_target":
                    db.execute("DELETE FROM baseline_corrections WHERE id=?", (rid,))
        db.execute("UPDATE sources SET status='partial' WHERE id IN(SELECT source_id FROM issues WHERE source_id IS NOT NULL)")
        revision = hashlib.sha256(json.dumps(sorted(set(manifest))).encode()).hexdigest()
        details = {"namespace": namespace, "dataset_revision": revision, "schema_version": SCHEMA_VERSION, "parser_version": PARSER_VERSION, "source_count": db.execute("SELECT count(*) FROM sources").fetchone()[0], "build_seconds": round(time.perf_counter() - start, 3), "roots": [f"root-{i + 1}" for i in range(len(roots))], "model_enrichment": {"status": "not_configured", "method": "injected Gemma-only interface; no model calls performed"}}
        for key, value in details.items():
            db.execute("INSERT INTO manifest VALUES(?,?)", (key, json.dumps(value)))
        db.commit()
        db.execute("PRAGMA optimize")
        db.close()
        staging.replace(db_path)
        return details
    except BaseException:
        db.close()
        raise
