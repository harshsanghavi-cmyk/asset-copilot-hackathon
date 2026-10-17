"""Application-owned durable memory and sessions. Never reads retrieval storage."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid
from typing import Any

from backend.contracts import MemoryDraft
from .budget import estimate, make_pack, select


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def js(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


class ScopeError(PermissionError):
    pass


class MemoryStore:
    @staticmethod
    def compatible_claims(left, right):
        if left.get("author_user_id") != right.get("author_user_id") or set(left.get("subject_ids",[])) != set(right.get("subject_ids",[])):
            return False
        a,b=left.get("valid_from"),right.get("valid_from")
        if a and b and a!=b:return False
        normalize=lambda text:re.sub(r"[^a-z0-9]+"," ",text.casefold()).strip()
        lq,rq=left.get("source_quote", ""),right.get("source_quote", "")
        if lq and normalize(lq)==normalize(rq):return True
        def action(f):
            text=f.get("source_quote","")+" "+f.get("statement","")
            if not re.search(r"replac|swapp|\bchanged\b",text,re.I):return None
            negative=bool(re.search(r"\b(?:not|never)\s+(?:been\s+)?(?:replaced|swapped|changed)|\bdidn.t\s+(?:replace|swap|change)",text,re.I))
            return ('replacement',negative)
        temporal=lambda text:re.findall(r"last night|yesterday|\d{4}-\d{2}-\d{2}|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*",text,re.I)
        return bool(action(left) and action(left)==action(right) and ((a and b and a==b) or temporal(lq) and [x.casefold() for x in temporal(lq)]==[x.casefold() for x in temporal(rq)]))
    def __init__(self, path: str | Path, namespace: str = "asset-field"):
        self.path, self.namespace = Path(path), namespace
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
              CREATE TABLE IF NOT EXISTS heads(namespace TEXT PRIMARY KEY, revision INTEGER);
              CREATE TABLE IF NOT EXISTS private_heads(namespace TEXT,user_id TEXT,revision INTEGER,
                PRIMARY KEY(namespace,user_id));
              CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,namespace TEXT,user_id TEXT,
                title TEXT,title_manual INTEGER DEFAULT 0,created_at TEXT,updated_at TEXT,
                completed INTEGER DEFAULT 0);
              CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,namespace TEXT,user_id TEXT,
                session_id TEXT,run_id TEXT,role TEXT,content TEXT,envelope TEXT,status TEXT,created_at TEXT);
              CREATE INDEX IF NOT EXISTS messages_session ON messages(session_id,created_at);
              CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,namespace TEXT,user_id TEXT,
                session_id TEXT,status TEXT,response TEXT,error TEXT,created_at TEXT);
              CREATE TABLE IF NOT EXISTS facts(id TEXT PRIMARY KEY,namespace TEXT,scope TEXT,
                owner_user_id TEXT,author_user_id TEXT,kind TEXT,subject_kind TEXT,subject_ids TEXT,
                statement TEXT,data TEXT,source_quote TEXT,source_message_id TEXT,status TEXT,
                valid_from TEXT,valid_to TEXT,supersedes TEXT,conflict_ids TEXT,
                created_at TEXT,updated_at TEXT,revision INTEGER);
              CREATE INDEX IF NOT EXISTS facts_scope ON facts(namespace,scope,owner_user_id,status);
              CREATE TABLE IF NOT EXISTS receipts(namespace TEXT,request_id TEXT,source_hash TEXT,
                payload TEXT,PRIMARY KEY(namespace,request_id));
              CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,namespace TEXT,
                fact_id TEXT,action TEXT,author_user_id TEXT,revision INTEGER,created_at TEXT,detail TEXT);
              CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,namespace TEXT,
                revision INTEGER,payload TEXT,created_at TEXT);
              CREATE TABLE IF NOT EXISTS episodes(id TEXT PRIMARY KEY,namespace TEXT,user_id TEXT,
                session_id TEXT,run_id TEXT,entity_ids TEXT,event_ids TEXT,intent TEXT,
                created_at TEXT,reference_date TEXT);
              CREATE TABLE IF NOT EXISTS summaries(session_id TEXT PRIMARY KEY,user_id TEXT,
                version INTEGER,covered INTEGER,text TEXT,manifest TEXT,updated_at TEXT);
              CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,session_id TEXT,user_id TEXT,
                kind TEXT,target INTEGER,status TEXT,attempts INTEGER DEFAULT 0,error TEXT,
                created_at TEXT,updated_at TEXT);
              CREATE TABLE IF NOT EXISTS capsules(namespace TEXT,user_id TEXT,version INTEGER,
                source_revision TEXT,manifest TEXT,status TEXT,updated_at TEXT,
                PRIMARY KEY(namespace,user_id));
              CREATE TABLE IF NOT EXISTS run_events(id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT,user_id TEXT,run_id TEXT,event TEXT,created_at TEXT);
              CREATE TABLE IF NOT EXISTS stage_results(namespace TEXT,user_id TEXT,run_id TEXT,
                stage TEXT,input_hash TEXT,result TEXT,PRIMARY KEY(namespace,user_id,run_id,stage,input_hash));
              CREATE TABLE IF NOT EXISTS answer_revisions(id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT,user_id TEXT,run_id TEXT,previous_envelope TEXT,reason TEXT,created_at TEXT);
              CREATE TABLE IF NOT EXISTS session_focus(namespace TEXT,user_id TEXT,session_id TEXT,
                asset_ids TEXT,pending_intent TEXT,source_run_id TEXT,updated_at TEXT,
                PRIMARY KEY(namespace,user_id,session_id));
              CREATE TABLE IF NOT EXISTS session_branches(session_id TEXT PRIMARY KEY,namespace TEXT,user_id TEXT,
                parent_session_id TEXT,source_message_id TEXT,source_run_id TEXT,source_text TEXT,mode TEXT);
              CREATE TABLE IF NOT EXISTS answer_suggestions(namespace TEXT,user_id TEXT,answer_id TEXT,version TEXT,
                status TEXT,suggestions TEXT,error_code TEXT,updated_at TEXT,
                PRIMARY KEY(namespace,user_id,answer_id,version));
              CREATE TABLE IF NOT EXISTS validation_receipts(id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT,user_id TEXT,run_id TEXT,purpose TEXT,code TEXT,details TEXT,invalid_output TEXT,created_at TEXT);
            """)
            if "client_message_id" not in {r[1] for r in db.execute("PRAGMA table_info(runs)")}:
                db.execute("ALTER TABLE runs ADD COLUMN client_message_id TEXT")
            if "error_code" not in {r[1] for r in db.execute("PRAGMA table_info(runs)")}:
                db.execute("ALTER TABLE runs ADD COLUMN error_code TEXT")
            for field, sqltype in {"error_at":"TEXT", "retry_after_seconds":"REAL", "retry_at":"TEXT"}.items():
                if field not in {r[1] for r in db.execute("PRAGMA table_info(runs)")}:
                    db.execute("ALTER TABLE runs ADD COLUMN " + field + " " + sqltype)
            db.execute("INSERT OR IGNORE INTO heads VALUES(?,0)", (namespace,))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def head(self) -> int:
        with self.connect() as db:
            return db.execute("SELECT revision FROM heads WHERE namespace=?", (self.namespace,)).fetchone()[0]

    def private_head(self, user_id) -> int:
        with self.connect() as db:
            row = db.execute("SELECT revision FROM private_heads WHERE namespace=? AND user_id=?",
                             (self.namespace, user_id)).fetchone()
            return row[0] if row else 0

    def _session(self, db, session_id, user_id):
        row = db.execute("SELECT * FROM sessions WHERE id=? AND namespace=? AND user_id=?",
                         (session_id, self.namespace, user_id)).fetchone()
        if not row:
            raise ScopeError("Conversation not found for this user")
        result = dict(row)
        branch = db.execute("SELECT parent_session_id,mode,source_message_id FROM session_branches WHERE session_id=? AND namespace=? AND user_id=?", (session_id,self.namespace,user_id)).fetchone()
        if branch:
            result.update(parent_session_id=branch["parent_session_id"],branch_mode=branch["mode"],source_message_id=branch["source_message_id"])
        return result

    def create_session(self, user_id, session_id=None, title="New conversation"):
        sid, timestamp = session_id or str(uuid.uuid4()), now()
        if len(sid) > 160 or not re.fullmatch(r"[A-Za-z0-9_.:-]+", sid):
            raise ValueError("Invalid conversation ID")
        with self.connect() as db:
            existing = db.execute("SELECT 1 FROM sessions WHERE id=?", (sid,)).fetchone()
            if existing:
                return self._session(db, sid, user_id)
            db.execute("INSERT INTO sessions(id,namespace,user_id,title,title_manual,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       (sid, self.namespace, user_id, title[:90], int(title != "New conversation"), timestamp, timestamp))
            return self._session(db, sid, user_id)

    def session(self, session_id, user_id):
        with self.connect() as db:
            return self._session(db, session_id, user_id)

    def list_sessions(self, user_id, query="", limit=50, offset=0):
        with self.connect() as db:
            args = (self.namespace, user_id, f"%{query}%", f"%{query}%")
            where = "s.namespace=? AND s.user_id=? AND (s.title LIKE ? OR EXISTS(SELECT 1 FROM messages m WHERE m.session_id=s.id AND m.content LIKE ?))"
            total = db.execute("SELECT count(*) FROM sessions s WHERE " + where, args).fetchone()[0]
            rows = db.execute("SELECT s.*,(SELECT count(*) FROM messages m WHERE m.session_id=s.id) message_count "
                              "FROM sessions s WHERE " + where + " ORDER BY s.updated_at DESC LIMIT ? OFFSET ?",
                              args + (min(limit, 100), offset)).fetchall()
            return {"sessions": [{**dict(r), **{k:v for k,v in self._session(db,r["id"],user_id).items() if k in {"parent_session_id","branch_mode","source_message_id"}}} for r in rows], "total": total}

    def rename_session(self, session_id, user_id, title, manual=True):
        with self.connect() as db:
            current = self._session(db, session_id, user_id)
            if manual or not current["title_manual"]:
                db.execute("UPDATE sessions SET title=?,title_manual=?,updated_at=? WHERE id=?",
                           (title.strip()[:90] or "Conversation", int(manual), now(), session_id))
            return self._session(db, session_id, user_id)

    def delete_session(self, session_id, user_id):
        with self.connect() as db:
            self._session(db, session_id, user_id)
            for table in ("messages", "jobs", "summaries"):
                db.execute(f"DELETE FROM {table} WHERE session_id=?", (session_id,))
            db.execute("DELETE FROM run_events WHERE run_id IN (SELECT id FROM runs WHERE session_id=?)", (session_id,))
            # Retain only run identity/ownership tombstones: a reused public run
            # ID must never reopen an old checkpoint after conversation deletion.
            db.execute("UPDATE runs SET status='deleted',response=NULL,error=NULL,error_code=NULL,client_message_id=NULL WHERE session_id=?", (session_id,))
            db.execute("DELETE FROM sessions WHERE id=?", (session_id,))

    def history(self, session_id, user_id):
        with self.connect() as db:
            session = self._session(db, session_id, user_id)
            rows = db.execute("SELECT * FROM messages WHERE session_id=? ORDER BY created_at,id", (session_id,)).fetchall()
            runs = {r["id"]: dict(r) for r in db.execute("SELECT * FROM runs WHERE session_id=? AND user_id=?", (session_id, user_id))}
            answered = {r["run_id"] for r in rows if r["role"] == "assistant"}
            messages = []
            for row in rows:
                item = dict(row)
                item["envelope"] = json.loads(item["envelope"]) if item["envelope"] else None
                run = runs.get(item["run_id"], {})
                if item["role"] == "user":
                    item["client_message_id"] = run.get("client_message_id") or item["id"]
                    item["run_status"] = run.get("status", "unknown")
                    item["stages"] = [json.loads(e[0]) for e in db.execute("SELECT event FROM run_events WHERE namespace=? AND user_id=? AND run_id=? ORDER BY id", (self.namespace, user_id, item["run_id"]))]
                messages.append(item)
                if item["role"] == "user" and run.get("status") == "error" and item["run_id"] not in answered:
                    messages.append({"id": item["run_id"] + ":error", "run_id": item["run_id"], "session_id": session_id,
                                     "role": "assistant", "content": run.get("error") or "The run failed", "status": "error",
                                     "error_code": run.get("error_code") or ("provider_error" if "provider returned HTTP" in (run.get("error") or "") else "run_failed"), "error_message": run.get("error"),
                                     "created_at": run.get("error_at") or item["created_at"], "envelope": None,
                                     "retry_after_seconds": run.get("retry_after_seconds"), "retry_at": run.get("retry_at")})
            return {"session": session, "messages": messages}

    def begin(self, run_id, session_id, user_id, message, client_message_id=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            session = self._session(db, session_id, user_id)
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None and client_message_id:
                row = db.execute("SELECT * FROM runs WHERE namespace=? AND user_id=? AND session_id=? AND client_message_id=?",
                                 (self.namespace, user_id, session_id, client_message_id)).fetchone()
                if row is None:
                    row = db.execute("SELECT r.* FROM runs r JOIN messages m ON m.run_id=r.id WHERE m.id=? AND r.namespace=? AND r.user_id=? AND r.session_id=?",
                                     (client_message_id, self.namespace, user_id, session_id)).fetchone()
            if row:
                if (row["user_id"], row["session_id"], row["namespace"]) != (user_id, session_id, self.namespace):
                    raise ScopeError("Run belongs to another conversation")
                if row["status"] == "deleted":
                    raise ScopeError("Run belongs to a deleted conversation; use a new run ID")
                prior = db.execute("SELECT content FROM messages WHERE id=?", (row["id"] + ":user",)).fetchone()
                if prior and prior[0] != message:
                    raise ValueError("Run ID reused with different text")
                return dict(row)
            timestamp = now()
            db.execute("INSERT INTO runs(id,namespace,user_id,session_id,status,response,error,created_at,client_message_id) VALUES(?,?,?,?,?,?,?,?,?)",
                       (run_id, self.namespace, user_id, session_id, "running", None, None, timestamp, client_message_id))
            db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (run_id + ":user", self.namespace, user_id, session_id, run_id, "user", message, None, "received", timestamp))
            title = session["title"]
            if session["completed"] == 0 and title == "New conversation":
                title = re.sub(r"\s+", " ", message).strip()[:70]
            db.execute("UPDATE sessions SET title=?,updated_at=? WHERE id=?", (title, timestamp, session_id))
            return {"id": run_id, "status": "running", "response": None}

    def previous_answer(self, session_id, user_id, run_id):
        with self.connect() as db:
            self._session(db, session_id, user_id)
            current = db.execute("SELECT created_at FROM runs WHERE id=? AND user_id=?", (run_id, user_id)).fetchone()
            rows = db.execute("SELECT envelope FROM messages WHERE namespace=? AND user_id=? AND session_id=? AND role='assistant' AND run_id!=? AND created_at<=? ORDER BY created_at DESC LIMIT 20", (self.namespace, user_id, session_id, run_id, current[0])).fetchall()
            for row in rows:
                answer = json.loads(row[0]) if row[0] else {}
                if any(r.get("rows") for r in answer.get("results", {}).values()):
                    return answer
            return None

    def focus(self, session_id, user_id, asset_ids=None, pending_intent=None, run_id=None):
        with self.connect() as db:
            self._session(db, session_id, user_id)
            old = db.execute("SELECT * FROM session_focus WHERE namespace=? AND user_id=? AND session_id=?", (self.namespace, user_id, session_id)).fetchone()
            if asset_ids is not None or pending_intent is not None:
                ids = asset_ids if asset_ids is not None else json.loads(old["asset_ids"]) if old else []
                intent = pending_intent if pending_intent is not None else old["pending_intent"] if old else None
                db.execute("INSERT OR REPLACE INTO session_focus VALUES(?,?,?,?,?,?,?)", (self.namespace, user_id, session_id, js(ids), intent[:400] if intent else None, run_id, now()))
                old = db.execute("SELECT * FROM session_focus WHERE namespace=? AND user_id=? AND session_id=?", (self.namespace, user_id, session_id)).fetchone()
            return {"asset_ids": json.loads(old["asset_ids"]), "pending_intent": old["pending_intent"], "source_run_id": old["source_run_id"]} if old else {"asset_ids": [], "pending_intent": None}

    def recent_user_texts(self, session_id, user_id, exclude_run):
        with self.connect() as db:
            self._session(db, session_id, user_id)
            return [dict(r) for r in db.execute("SELECT run_id,content FROM messages WHERE namespace=? AND user_id=? AND session_id=? AND role='user' AND run_id!=? ORDER BY created_at DESC LIMIT 12", (self.namespace, user_id, session_id, exclude_run))]

    def create_branch(self, session_id, user_id, message_id, mode):
        if mode not in {"edit", "regenerate"}:
            raise ValueError("Branch mode must be edit or regenerate")
        with self.connect() as db:
            parent = self._session(db, session_id, user_id)
            target = db.execute("SELECT m.* FROM messages m JOIN runs r ON r.id=m.run_id WHERE m.session_id=? AND m.user_id=? AND m.role='user' AND (m.id=? OR r.client_message_id=?)", (session_id, user_id, message_id, message_id)).fetchone()
            if not target:
                raise ScopeError("User message not found in this conversation")
            prefix = db.execute("SELECT * FROM messages WHERE session_id=? AND created_at<? ORDER BY created_at,id", (session_id, target["created_at"])).fetchall()
            new_id, timestamp = str(uuid.uuid4()), now()
            db.execute("INSERT INTO sessions(id,namespace,user_id,title,created_at,updated_at,completed) VALUES(?,?,?,?,?,?,?)", (new_id, self.namespace, user_id, parent["title"][:75] + " (" + mode + ")", timestamp, timestamp, sum(r["role"] == "assistant" for r in prefix)))
            for source in prefix:
                cloned_run = new_id + ":" + source["run_id"]
                db.execute("INSERT OR IGNORE INTO runs(id,namespace,user_id,session_id,status,created_at) VALUES(?,?,?,?,?,?)", (cloned_run, self.namespace, user_id, new_id, "complete", source["created_at"]))
                envelope = json.loads(source["envelope"]) if source["envelope"] else None
                if envelope:
                    envelope.update(answer_id=cloned_run, thread_id=new_id, source_answer_id=envelope.get("source_answer_id", source["run_id"]))
                    db.execute("UPDATE runs SET response=? WHERE id=?", (js(envelope), cloned_run))
                db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?)", (new_id + ":" + source["id"], self.namespace, user_id, new_id, cloned_run, source["role"], source["content"], js(envelope) if envelope else None, source["status"], source["created_at"]))
            db.execute("INSERT INTO session_branches VALUES(?,?,?,?,?,?,?,?)", (new_id, self.namespace, user_id, session_id, target["id"], target["run_id"], target["content"], mode))
        return {"session": self.session(new_id, user_id), "messages": self.history(new_id, user_id)["messages"], "source_message": {"id": target["id"], "content": target["content"]}, "branch_mode": mode, "parent_session_id": session_id}

    def branch(self, session_id, user_id):
        with self.connect() as db:
            self._session(db, session_id, user_id)
            row = db.execute("SELECT * FROM session_branches WHERE session_id=? AND user_id=? AND namespace=?", (session_id, user_id, self.namespace)).fetchone()
            return dict(row) if row else None

    def receipts_for_run(self, user_id, run_id):
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM receipts WHERE namespace=? AND request_id LIKE ?", (self.namespace, run_id + ":memory:%")).fetchall()
            return [json.loads(r[0]) for r in rows if json.loads(r[0]).get("author_user_id") == user_id]

    def suggestions(self, user_id, answer_id, version, status=None, questions=None, error=None):
        self.answer(answer_id, user_id)
        with self.connect() as db:
            if status:
                db.execute("INSERT INTO answer_suggestions VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(namespace,user_id,answer_id,version) DO UPDATE SET status=excluded.status,suggestions=excluded.suggestions,error_code=excluded.error_code,updated_at=excluded.updated_at", (self.namespace, user_id, answer_id, version, status, js(questions or []), error, now()))
            row = db.execute("SELECT * FROM answer_suggestions WHERE namespace=? AND user_id=? AND answer_id=? AND version=?", (self.namespace, user_id, answer_id, version)).fetchone()
            return {"answer_id": answer_id, "version": version, "status": row["status"] if row else "pending", "suggestions": json.loads(row["suggestions"]) if row else [], "error_code": row["error_code"] if row else None, "updated_at":row["updated_at"] if row else None, "requested_at":row["updated_at"] if row and row["status"]=="pending" else None, "exists": bool(row)}

    def finish(self, run_id, session_id, user_id, envelope, intent="answer", status="complete", replace_existing=False):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            session = self._session(db, session_id, user_id)
            timestamp = now()
            inserted = db.execute("INSERT OR IGNORE INTO messages VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (run_id + ":assistant", self.namespace, user_id, session_id, run_id, "assistant",
                        envelope["narrative"], js(envelope), status, timestamp)).rowcount
            if not inserted:
                if replace_existing:
                    old = db.execute("SELECT envelope FROM messages WHERE id=?", (run_id + ":assistant",)).fetchone()
                    if old and old[0] != js(envelope):
                        db.execute("INSERT INTO answer_revisions(namespace,user_id,run_id,previous_envelope,reason,created_at) VALUES(?,?,?,?,?,?)", (self.namespace, user_id, run_id, old[0], "Scoped presentation repair", timestamp))
                db.execute("UPDATE messages SET content=?,envelope=?,status=? WHERE id=? AND (status='partial' OR ?)", (envelope["narrative"], js(envelope), status, run_id + ":assistant", int(replace_existing)))
            db.execute("UPDATE runs SET status=?,response=?,error=NULL,error_code=NULL,error_at=NULL,retry_after_seconds=NULL,retry_at=NULL WHERE id=? AND user_id=?", (status, js(envelope), run_id, user_id))
            if not inserted:
                return session["completed"]
            count = session["completed"] + 1
            db.execute("UPDATE sessions SET completed=?,updated_at=? WHERE id=?", (count, timestamp, session_id))
            entity_ids, event_ids = [], []
            for result in envelope.get("results", {}).values():
                for row in result.get("rows", []):
                    for key, value in row.items():
                        if key in {"asset_id", "well_id"} and isinstance(value, str) and value not in entity_ids:
                            entity_ids.append(value)
                        if key in {"inspection_id", "maintenance_id", "event_id"} and isinstance(value, str) and value not in event_ids:
                            event_ids.append(value)
            if entity_ids:
                db.execute("INSERT OR IGNORE INTO episodes VALUES(?,?,?,?,?,?,?,?,?,?)",
                           ("episode:" + run_id, self.namespace, user_id, session_id, run_id, js(entity_ids),
                            js(event_ids), intent, timestamp, envelope["reference_date"]))
            if count % 10 == 0:
                self._enqueue(db, session_id, user_id, "periodic", count - 3)
            history_bytes = db.execute("SELECT coalesce(sum(length(content)),0) FROM messages WHERE session_id=?", (session_id,)).fetchone()[0]
            summary = db.execute("SELECT covered FROM summaries WHERE session_id=?", (session_id,)).fetchone()
            if history_bytes > 1000 and count > 3 and (not summary or summary[0] < count - 3):
                self._enqueue(db, session_id, user_id, "overflow", count - 3)
            return count

    def fail(self, run_id, user_id, message, code="run_failed", retry_after=None):
        with self.connect() as db:
            retry_at = (datetime.now(timezone.utc) + timedelta(seconds=retry_after)).isoformat() if retry_after else None
            db.execute("UPDATE runs SET status=CASE WHEN json_extract(response,'$.generation.status')='partial' THEN 'partial' ELSE 'error' END,error=?,error_code=?,error_at=?,retry_after_seconds=?,retry_at=? WHERE id=? AND user_id=?", (message[:1000], code, now(), retry_after, retry_at, run_id, user_id))

    def append_stage(self, run_id, user_id, event):
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM runs WHERE id=? AND namespace=? AND user_id=? AND status!='deleted'", (run_id, self.namespace, user_id)).fetchone():
                raise ScopeError("Run not found for stage event")
            db.execute("INSERT INTO run_events(namespace,user_id,run_id,event,created_at) VALUES(?,?,?,?,?)", (self.namespace, user_id, run_id, js(event), event["timestamp"]))
            db.execute("DELETE FROM run_events WHERE run_id=? AND id NOT IN (SELECT id FROM run_events WHERE run_id=? ORDER BY id DESC LIMIT 80)", (run_id, run_id))

    def stage_result(self, user_id, run_id, stage, fingerprint, result=None):
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM runs WHERE namespace=? AND user_id=? AND id=? AND status!='deleted'", (self.namespace, user_id, run_id)).fetchone():
                raise ScopeError("Run not found for stage receipt")
            if result is not None:
                db.execute("INSERT OR REPLACE INTO stage_results VALUES(?,?,?,?,?,?)", (self.namespace, user_id, run_id, stage, fingerprint, js(result)))
                return result
            row = db.execute("SELECT result FROM stage_results WHERE namespace=? AND user_id=? AND run_id=? AND stage=? AND input_hash=?", (self.namespace, user_id, run_id, stage, fingerprint)).fetchone()
            return json.loads(row[0]) if row else None

    def record_validation(self, user_id, run_id, purpose, code, details, invalid_output):
        raw = js(invalid_output)
        if len(raw.encode()) > 16000:
            raw = js({"omitted":True,"byte_count":len(raw.encode()),"sha256":hashlib.sha256(raw.encode()).hexdigest()})
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM runs WHERE namespace=? AND user_id=? AND id=?", (self.namespace,user_id,run_id)).fetchone():
                raise ScopeError("Run not found for validation receipt")
            db.execute("INSERT INTO validation_receipts(namespace,user_id,run_id,purpose,code,details,invalid_output,created_at) VALUES(?,?,?,?,?,?,?,?)", (self.namespace,user_id,run_id,purpose,code,js(details),raw,now()))

    def validation_history(self, run_id):
        with self.connect() as db:
            return [dict(r,details=json.loads(r["details"]),invalid_output=json.loads(r["invalid_output"])) for r in db.execute("SELECT * FROM validation_receipts WHERE namespace=? AND run_id=? ORDER BY id DESC LIMIT 20", (self.namespace,run_id))]

    def _enqueue(self, db, sid, uid, kind, target):
        identifier = f"{sid}:{kind}:{target}"
        db.execute("INSERT OR IGNORE INTO jobs VALUES(?,?,?,?,?,?,0,NULL,?,?)",
                   (identifier, sid, uid, kind, target, "pending", now(), now()))

    def _fact(self, row):
        d = dict(row)
        for key in ("subject_ids", "data", "conflict_ids"):
            d[key] = json.loads(d[key])
        d["knowledge_revision"] = d["revision"] if d["scope"] == "shared" else None
        return d

    def facts(self, user_id, subjects=None, reference_date="2026-10-16", include_candidates=False):
        with self.connect() as db:
            return self._facts_in(db, user_id, subjects, reference_date, include_candidates)

    def _facts_in(self, db, user_id, subjects=None, reference_date="2026-10-16", include_candidates=False):
        rows = db.execute("SELECT * FROM facts WHERE namespace=? AND (scope='shared' OR owner_user_id=?) "
                          "AND status NOT IN ('withdrawn','superseded') ORDER BY revision DESC,created_at DESC",
                          (self.namespace, user_id)).fetchall()
        result = []
        for row in rows:
            fact = self._fact(row)
            if not include_candidates and fact["status"] == "candidate":
                continue
            # Corrections target historical observations, independent of receipt date.
            if fact["kind"] != "correction" and fact["valid_to"] and reference_date >= fact["valid_to"]:
                continue
            if fact["kind"] == "rule" and fact["valid_from"] and reference_date < fact["valid_from"]:
                continue
            if subjects and fact["scope"] == "shared" and fact["subject_ids"] and not set(subjects).intersection(fact["subject_ids"]):
                continue
            result.append(fact)
        return result

    def commit_draft(self, user_id, run_id, index, draft: MemoryDraft, message: str, *, original_value=None):
        private_requested = bool(re.search(r"keep (?:this|it) private|don.t share|between us|only for me|just for me", message, re.I))
        asset_claim = bool(re.search(r"\b(?:well[\s-]*\d+|asset)\b", draft.source_quote + " " + draft.statement, re.I) and re.search(r"replac|swapp|install|removed|shut.?in|running|broken|leak|gas", draft.source_quote + " " + draft.statement, re.I))
        if draft.kind == "work_context" and asset_claim and not private_requested:
            subjects = [s for s in draft.subject_ids if re.fullmatch(r"WELL-\d+", s, re.I)]
            draft = draft.model_copy(update={"kind":"observation", "scope":"shared", "subject_kind":"asset" if subjects else "organization", "subject_ids":subjects})
        data_observation = draft.kind in {"observation", "guidance", "hypothesis"} and bool(re.search(r"\b(?:data|dataset|value|reading|measurement|record|well|asset)s?\b", draft.source_quote + " " + draft.statement, re.I))
        if data_observation and not private_requested:
            changes = {"scope": "shared"}
            if draft.subject_kind == "user" or not draft.subject_ids:
                changes.update(subject_kind="organization", subject_ids=[])
            draft = draft.model_copy(update=changes)
        p = draft.model_dump()
        normalized = lambda s: " ".join(str(s).split()).casefold()
        if normalized(draft.source_quote) not in normalized(message):
            raise ValueError("Memory source quote does not occur in the user's statement")
        if draft.kind in {"preference", "work_context"} or draft.subject_kind == "user":
            p["scope"] = "private"
        if (draft.kind not in {"correction", "rule"}
                and re.search(r"we (?:discussed|talked)|our conversation", message, re.I)
                and not re.search(r"for everyone|share (?:this|it)|publish|team knowledge|organization knowledge", message, re.I)):
            # A conversational entity set is private even if extraction labels
            # it an operational plan. Explicit publication is a separate act.
            p["scope"] = "private"
        if private_requested:
            if draft.kind in {"correction", "rule"}:
                raise ValueError("Formal corrections/rules affect shared knowledge; clarify the private-only restriction")
            p["scope"] = "private"
        if p["scope"] == "shared" and not draft.subject_ids and draft.subject_kind not in {"organization", "team"}:
            raise ValueError("Shared operational memory requires a resolved subject")
        if draft.supersedes and not re.search(r"supersed|replac|withdraw|revise|update.*(?:correct|rule|threshold)", message, re.I):
            raise ValueError("Replacing accepted authority requires an explicit supersession request")
        if draft.kind == "correction":
            if not draft.target_record_id or draft.field not in {"wellhead_temp_c", "ambient_temp_c", "spill_detected", "spill_est_volume_bbl"}:
                raise ValueError("Correction requires a supported field and exact observation")
            if not re.search(r"wrong|correct|measur|actual|real value|faulty", message, re.I):
                raise ValueError("Ordinary claims are not formal corrections")
            if draft.value is None or original_value is None:
                raise ValueError("Original target value and replacement must be established before correction")
            if draft.field == "spill_detected":
                if not isinstance(draft.value, bool):
                    raise ValueError("Spill detection correction must be boolean")
            elif isinstance(draft.value, bool) or not isinstance(draft.value, (int, float)):
                raise ValueError("Numeric correction value required")
            else:
                import math
                from decimal import Decimal
                values = {Decimal(n) for n in re.findall(r"-?\d+(?:\.\d+)?", draft.source_quote)}
                if not math.isfinite(draft.value) or Decimal(str(draft.value)) not in values:
                    raise ValueError("Correction value is not explicitly present in its source quote")
            p["scope"] = "shared"
        if draft.kind == "rule":
            if not draft.well_type or not draft.equipment_kind or draft.threshold is None or draft.threshold <= 0:
                raise ValueError("Rule requires type, equipment and positive threshold")
            from decimal import Decimal
            if Decimal(str(draft.threshold)) not in {Decimal(n) for n in re.findall(r"-?\d+(?:\.\d+)?", draft.source_quote)}:
                raise ValueError("Rule threshold is not explicitly present in its source quote")
            if draft.well_type.casefold() not in message.casefold() or not re.search(r"\ball\b|\bfor\b|\btype\b", message, re.I):
                raise ValueError("Type rule scope must be explicit in user text")
            p["scope"] = "shared"
        key = f"{run_id}:memory:{index}"
        fingerprint = hashlib.sha256(js([user_id, p]).encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM receipts WHERE namespace=? AND request_id=?", (self.namespace, key)).fetchone()
            if prior:
                if prior["source_hash"] != fingerprint:
                    raise ValueError("Write idempotency key reused with different proposal")
                return json.loads(prior["payload"])
            hearsay = bool(re.search(r"told me|I heard|was told|someone said", draft.source_quote, re.I))
            status, conflicts = ("candidate" if draft.qualifier == "inferred" else "unconfirmed" if hearsay or data_observation and not draft.subject_ids else "attributed"), []
            active = db.execute("SELECT * FROM facts WHERE namespace=? AND kind=? AND scope=? "
                                "AND (owner_user_id=? OR owner_user_id IS NULL) AND status NOT IN ('withdrawn','superseded')",
                                (self.namespace, draft.kind, p["scope"], user_id)).fetchall()
            if draft.kind in {"correction", "rule"}:
                target = draft.target_record_id or draft.well_type
                def same_target(r):
                    data = json.loads(r["data"])
                    if draft.kind == "correction":
                        return data.get("target_record_id") == target and data.get("field") == draft.field
                    overlaps = not (draft.valid_to and r["valid_from"] and draft.valid_to <= r["valid_from"] or r["valid_to"] and draft.valid_from and r["valid_to"] <= draft.valid_from)
                    return data.get("well_type") == draft.well_type and data.get("equipment_kind") == draft.equipment_kind and data.get("rule_id") == draft.rule_id and overlaps
                matches = [r for r in active if same_target(r)]
                accepted = [r for r in matches if r["status"] == "accepted"]
                if draft.supersedes and not any(r["id"] == draft.supersedes for r in accepted):
                    raise ValueError("Supersession must reference the accepted matching change")
                conflicts = [r["id"] for r in accepted if r["id"] != draft.supersedes]
                status = "conflict_pending" if conflicts else "accepted"
            else:
                proposed={**p,"author_user_id":user_id,"subject_ids":draft.subject_ids,"source_quote":draft.source_quote,"valid_from":draft.valid_from}
                conflicts = [r["id"] for r in active if json.loads(r["subject_ids"]) == draft.subject_ids
                             and r["statement"] != draft.statement and not self.compatible_claims(proposed,self._fact(r))]
                if conflicts and draft.kind not in {"preference", "work_context"}:
                    status = "unconfirmed"
            if p["scope"] == "shared":
                revision = db.execute("SELECT revision FROM heads WHERE namespace=?", (self.namespace,)).fetchone()[0] + 1
                db.execute("UPDATE heads SET revision=? WHERE namespace=?", (revision, self.namespace))
            else:
                db.execute("INSERT OR IGNORE INTO private_heads VALUES(?,?,0)", (self.namespace, user_id))
                revision = db.execute("SELECT revision FROM private_heads WHERE namespace=? AND user_id=?", (self.namespace, user_id)).fetchone()[0] + 1
                db.execute("UPDATE private_heads SET revision=? WHERE namespace=? AND user_id=?", (revision, self.namespace, user_id))
            identifier, timestamp = "memory:" + str(uuid.uuid4()), now()
            p.update(original_value=original_value, effective_value=draft.value, author_user_id=user_id,
                     status=status, revision=revision, inspection_id=draft.target_record_id,
                     threshold=draft.threshold, repair_threshold=draft.threshold)
            if draft.kind == "rule":
                p["value"] = draft.threshold
                p["predicate"] = "rca_threshold"
            db.execute("INSERT INTO facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (identifier, self.namespace, p["scope"], user_id if p["scope"] == "private" else None,
                        user_id, draft.kind, draft.subject_kind, js(draft.subject_ids), draft.statement, js(p),
                        draft.source_quote, run_id + ":user", status, draft.valid_from, draft.valid_to,
                        draft.supersedes, js(conflicts), timestamp, timestamp, revision))
            if draft.supersedes and status == "accepted":
                db.execute("UPDATE facts SET status='superseded',updated_at=? WHERE id=?", (timestamp, draft.supersedes))
            receipt = {"id": identifier, "scope": p["scope"], "status": status, "revision": revision,
                       "author_user_id": user_id, "statement": draft.statement,
                       "effective_value": draft.value, "original_value": original_value,
                       "conflict_ids": conflicts, "saved": True}
            db.execute("INSERT INTO receipts VALUES(?,?,?,?)", (self.namespace, key, fingerprint, js(receipt)))
            db.execute("INSERT INTO audit(namespace,fact_id,action,author_user_id,revision,created_at,detail) VALUES(?,?,?,?,?,?,?)",
                       (self.namespace, identifier, "append", user_id, revision, timestamp, js(receipt)))
            if p["scope"] == "shared":
                db.execute("INSERT INTO outbox(namespace,revision,payload,created_at) VALUES(?,?,?,?)", (self.namespace, revision, js(receipt), timestamp))
            capsule_owner = user_id if p["scope"] == "private" else "__shared__"
            canonical_manifest = [r[0] for r in db.execute(
                "SELECT id FROM facts WHERE namespace=? AND scope=? AND (owner_user_id=? OR owner_user_id IS NULL) "
                "AND status NOT IN ('withdrawn','superseded') ORDER BY id", (self.namespace, p["scope"], user_id))]
            db.execute("INSERT INTO capsules VALUES(?,?,1,?,?,?,?) ON CONFLICT(namespace,user_id) DO UPDATE SET "
                       "version=version+1,source_revision=excluded.source_revision,manifest=excluded.manifest,status='deterministic_refresh',updated_at=excluded.updated_at",
                       (self.namespace, capsule_owner, str(revision), js(canonical_manifest), "deterministic_refresh", timestamp))
            return receipt

    def authority(self, reference_date="2026-10-16"):
        # One read transaction binds the fact set to its revision. A separate
        # head() read could otherwise label old facts with a concurrent new head.
        with self.connect() as db:
            db.execute("BEGIN")
            revision = db.execute("SELECT revision FROM heads WHERE namespace=?", (self.namespace,)).fetchone()[0]
            shared = self._facts_in(db, "__no_private__", reference_date=reference_date)
            return {"knowledge_revision": revision,
                    "corrections": [{**f["data"], "id": f["id"], "author_user_id": f["author_user_id"]} for f in shared if f["kind"] == "correction" and f["status"] == "accepted"],
                    "rule_overrides": [{**f["data"], "id": f["id"], "author_user_id": f["author_user_id"]} for f in shared if f["kind"] == "rule" and f["status"] == "accepted"],
                    "shared_claims": [self.public_fact(f) for f in shared if f["kind"] not in {"correction", "rule"}]}

    def share_observation(self, identifier, actor, reason):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM facts WHERE namespace=? AND id=?", (self.namespace, identifier)).fetchone()
            if not row or row["author_user_id"] != actor or row["kind"] not in {"observation", "guidance", "hypothesis"}:
                raise ScopeError("Only the author's attributed operational observation can be shared")
            if row["scope"] == "shared":
                return {"id": identifier, "scope": "shared", "namespace": self.namespace, "status": row["status"], "revision": row["revision"]}
            previous = self._fact(row);revision = self.head() + 1;timestamp = now()
            payload = json.loads(row["data"])
            kind = "organization" if row["subject_kind"] == "user" else row["subject_kind"]
            subjects = [] if kind == "organization" else json.loads(row["subject_ids"])
            payload.update(scope="shared",subject_kind=kind,subject_ids=subjects,status="unconfirmed",revision=revision)
            db.execute("UPDATE facts SET scope='shared',owner_user_id=NULL,subject_kind=?,subject_ids=?,status='unconfirmed',data=?,revision=?,updated_at=? WHERE id=?", (kind,js(subjects),js(payload),revision,timestamp,identifier))
            db.execute("UPDATE heads SET revision=? WHERE namespace=?", (revision,self.namespace))
            db.execute("UPDATE private_heads SET revision=revision+1 WHERE namespace=? AND user_id=?", (self.namespace,actor))
            detail={"reason":reason,"before":previous,"after":{"scope":"shared","status":"unconfirmed","revision":revision}}
            db.execute("INSERT INTO audit(namespace,fact_id,action,author_user_id,revision,created_at,detail) VALUES(?,?,?,?,?,?,?)", (self.namespace,identifier,"scope_transition",actor,revision,timestamp,js(detail)))
            db.execute("INSERT INTO outbox(namespace,revision,payload,created_at) VALUES(?,?,?,?)", (self.namespace,revision,js({"id":identifier,"action":"scope_transition"}),timestamp))
            db.execute("UPDATE capsules SET version=version+1,status='needs_refresh',updated_at=? WHERE namespace=? AND user_id IN (?,?)", (timestamp,self.namespace,actor,"__shared__"))
        return {"id":identifier,"scope":"shared","namespace":self.namespace,"status":"unconfirmed","revision":revision,"author_user_id":actor,"created_at":row["created_at"]}

    def public_fact(self, fact):
        quote = fact.get("source_quote", "")
        hearsay = bool(re.search(r"told me|I heard|they said|someone said", quote, re.I))
        firsthand = not hearsay and bool(re.search(r"\b(?:I|we) (?:personally )?(?:replaced|swapped|changed|installed|removed|measured|inspected|saw)\b", quote, re.I))
        public = {"id": fact["id"], "scope": fact["scope"], "kind": fact["kind"],
                "subject_ids": fact["subject_ids"], "statement": fact["statement"],
                "author": fact["author_user_id"], "author_user_id":fact["author_user_id"], "created_at":fact["created_at"], "valid_from": fact["valid_from"],
                "valid_to": fact["valid_to"], "status": fact["status"],
                "conflicts": fact["conflict_ids"], "revision": fact["revision"],
                "qualifier": "hearsay" if hearsay else fact.get("data", {}).get("qualifier", "attributed"),
                "firsthand": firsthand, "attribution_basis": "hearsay" if hearsay else "direct" if firsthand else "attributed"}
        if fact["scope"] == "private":
            for key in ("author_user_id","created_at","qualifier","firsthand","attribution_basis"):
                public.pop(key,None)
        return public

    def reconcile_compatible_conflicts(self):
        changed=[]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            facts={r["id"]:self._fact(r) for r in db.execute("SELECT * FROM facts WHERE namespace=? AND scope='shared' AND kind IN ('observation','guidance','hypothesis')",(self.namespace,))}
            head=db.execute("SELECT revision FROM heads WHERE namespace=?",(self.namespace,)).fetchone()[0]
            for identity,fact in facts.items():
                removed=[other for other in fact['conflict_ids'] if other in facts and self.compatible_claims(fact,facts[other])]
                if not removed:continue
                remaining=[x for x in fact['conflict_ids'] if x not in removed];head+=1;timestamp=now()
                db.execute("UPDATE facts SET conflict_ids=?,revision=?,updated_at=? WHERE id=?",(js(remaining),head,timestamp,identity))
                db.execute("INSERT INTO audit(namespace,fact_id,action,author_user_id,revision,created_at,detail) VALUES(?,?,?,?,?,?,?)",(self.namespace,identity,'compatible_claim_conflicts_reconciled',fact['author_user_id'],head,timestamp,js({'removed_conflicts':removed,'remaining_conflicts':remaining,'reason':'Same author, subject, action polarity and source date agree; provenance and unconfirmed status retained'})))
                db.execute("INSERT INTO outbox(namespace,revision,payload,created_at) VALUES(?,?,?,?)",(self.namespace,head,js({'id':identity,'action':'compatible_claim_conflicts_reconciled'}),timestamp))
                changed.append({'id':identity,'removed_conflicts':removed,'revision':head})
            if changed:
                db.execute("UPDATE heads SET revision=? WHERE namespace=?",(head,self.namespace))
        return changed

    def resolve_reference(self, user_id, text="", session_id=None, conversation_date=None):
        with self.connect() as db:
            ordinal = re.search(r"\b(first|second|third|fourth|fifth)\s+(?:question|turn)\b", text, re.I)
            if ordinal and session_id:
                index = {"first":0,"second":1,"third":2,"fourth":3,"fifth":4}[ordinal[1].casefold()]
                turns = [r for r in db.execute("SELECT run_id,content FROM messages WHERE namespace=? AND user_id=? AND session_id=? AND role='user' ORDER BY created_at,id", (self.namespace,user_id,session_id)) if not re.fullmatch(r"\s*(?:hi|hello|hey)[.!?\s]*", r["content"], re.I)]
                if index >= len(turns):
                    return {"status":"absent","entity_ids":[],"event_ids":[],"candidates":[]}
                episode = db.execute("SELECT * FROM episodes WHERE namespace=? AND user_id=? AND session_id=? AND run_id=?", (self.namespace,user_id,session_id,turns[index]["run_id"])).fetchone()
                if not episode:
                    return {"status":"absent","entity_ids":[],"event_ids":[],"candidates":[],"reason":"No entity set was established for that earlier question"}
                return {"status":"resolved","entity_ids":json.loads(episode["entity_ids"]),"event_ids":json.loads(episode["event_ids"]),"source_receipt":episode["id"],"reference_date":episode["reference_date"]}
            rows = db.execute("SELECT * FROM episodes WHERE namespace=? AND user_id=? ORDER BY created_at DESC LIMIT 30",
                              (self.namespace, user_id)).fetchall()
            if not rows:
                return {"status": "absent", "entity_ids": [], "event_ids": [], "candidates": []}
            candidates = [dict(r, entity_ids=json.loads(r["entity_ids"]), event_ids=json.loads(r["event_ids"])) for r in rows]
            if re.search(r"\byesterday\b", text, re.I):
                from datetime import date, timedelta
                target = (date.fromisoformat(conversation_date) if conversation_date else datetime.now(timezone.utc).date()) - timedelta(days=1)
                candidates = [r for r in candidates if r["created_at"][:10] == target.isoformat()]
            elif session_id and any(r["session_id"] == session_id for r in candidates):
                candidates = [r for r in candidates if r["session_id"] == session_id]
            if re.search(r"three|3 wells", text, re.I):
                candidates = [r for r in candidates if len(r["entity_ids"]) == 3]
            if not candidates:
                return {"status": "absent", "entity_ids": [], "event_ids": [], "candidates": []}
            distinct = {}
            for candidate in candidates:
                distinct.setdefault((tuple(candidate["entity_ids"]), tuple(candidate["event_ids"])), candidate)
            candidates = list(distinct.values())
            latest_in_thread = session_id and candidates[0]["session_id"] == session_id and not re.search(r"yesterday|earlier|last time", text, re.I)
            chosen = candidates[0]
            singular = bool(re.search(r"\b(?:that|this) (?:well|asset)|\bit\b", text, re.I))
            event_reference = bool(re.search(r"that (?:incident|spill|repair|job)", text, re.I))
            if (len(candidates) > 1 and not latest_in_thread) or (singular and len(chosen["entity_ids"]) > 1) or (event_reference and len(chosen["event_ids"]) > 1):
                return {"status": "ambiguous", "entity_ids": [], "event_ids": [],
                        "candidates": [{"receipt_id": r["id"], "entity_ids": r["entity_ids"], "event_ids": r["event_ids"], "date": r["created_at"]} for r in candidates[:5]]}
            return {"status": "resolved", "entity_ids": chosen["entity_ids"], "event_ids": chosen["event_ids"],
                    "source_receipt": chosen["id"], "reference_date": chosen["reference_date"]}

    def context(self, user_id, session_id, message, reference_date="2026-10-16", subjects=None, byte_scale=1):
        history = self.history(session_id, user_id)["messages"]
        visible = self.facts(user_id, subjects, reference_date)
        private = [self.public_fact(f) for f in visible if f["scope"] == "private"]
        # Build the lexical index from already-authorized active facts only.
        # Private rows from other users never enter FTS or influence its ranking.
        ranked = self._rank_visible(visible, message)
        private_selected = [self.public_fact(f) for f in ranked if f["scope"] == "private"]
        ranked_ids = {f["id"] for f in ranked}
        shared = [self.public_fact(f) for f in ranked if f["scope"] == "shared"]
        shared += [self.public_fact(f) for f in visible if f["scope"] == "shared" and f["id"] not in ranked_ids]
        with self.connect() as db:
            summary = db.execute("SELECT * FROM summaries WHERE session_id=? AND user_id=?", (session_id, user_id)).fetchone()
            episodes = db.execute("SELECT id,entity_ids FROM episodes WHERE namespace=? AND user_id=? ORDER BY created_at DESC LIMIT 5", (self.namespace, user_id)).fetchall()
        completed = [m for m in history if m["role"] == "assistant" and m.get("status") != "error"]
        covered_runs = {m["run_id"] for m in completed[:summary["covered"]]} if summary else set()
        recent = [{"role": m["role"], "text": m["content"]} for m in history
                  if m["run_id"] not in covered_runs and m.get("status") != "error"
                  and not (m["role"] == "user" and m["content"] == message)]
        pack = make_pack(private_facts=private, shared_facts=shared, summary=summary["text"] if summary else "",
                         recent=recent,
                         episodes=[{"id": r["id"], "entities": json.loads(r["entity_ids"])} for r in episodes],
                         private_revision=self.private_head(user_id), knowledge_revision=self.head(), private_selected=private_selected, byte_scale=byte_scale)
        return pack

    def _rank_visible(self, facts, message):
        stop = {"the", "what", "which", "that", "this", "from", "with", "have", "about", "please", "remember", "does", "were", "well"}
        terms = [w for w in re.findall(r"[\w-]{2,64}", message.casefold()) if w not in stop][:12]
        if not terms or not facts:
            return []
        query = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)
        with sqlite3.connect(":memory:") as index:
            index.execute("CREATE VIRTUAL TABLE scoped_facts USING fts5(memory_id UNINDEXED,statement,subjects)")
            index.executemany("INSERT INTO scoped_facts VALUES(?,?,?)", [(f["id"], f["statement"], " ".join(f["subject_ids"])) for f in facts])
            matches = index.execute("SELECT memory_id FROM scoped_facts WHERE scoped_facts MATCH ? ORDER BY bm25(scoped_facts) LIMIT 100", (query,)).fetchall()
        lookup = {f["id"]: f for f in facts}
        return [lookup[row[0]] for row in matches]

    def answer(self, answer_id, user_id):
        with self.connect() as db:
            row = db.execute("SELECT envelope FROM messages WHERE namespace=? AND user_id=? AND id=?",
                             (self.namespace, user_id, answer_id + ":assistant")).fetchone()
            if not row:
                raise ScopeError("Answer not found for this user")
            return json.loads(row[0])

    def admin_list(self, scope=None, user_id=None, kind=None, q="", limit=25, offset=0):
        where, params = ["namespace=?"], [self.namespace]
        for key, value in [("scope", scope), ("owner_user_id", user_id), ("kind", kind)]:
            if value:
                where.append(key + "=?"); params.append(value)
        if q:
            where.append("statement LIKE ?"); params.append("%" + q + "%")
        with self.connect() as db:
            total = db.execute("SELECT count(*) FROM facts WHERE " + " AND ".join(where), params).fetchone()[0]
            rows = db.execute("SELECT * FROM facts WHERE " + " AND ".join(where) + " ORDER BY updated_at DESC LIMIT ? OFFSET ?", params + [min(limit, 100), offset]).fetchall()
            return {"items": [{**self.public_fact(self._fact(r)), "owner_user_id": r["owner_user_id"],
                     "author_user_id": r["author_user_id"], "created_at": r["created_at"], "updated_at": r["updated_at"],
                     "preview": r["statement"][:240], "knowledge_revision": r["revision"]} for r in rows], "total": total}

    def admin_detail(self, identifier):
        with self.connect() as db:
            row = db.execute("SELECT * FROM facts WHERE namespace=? AND id=?", (self.namespace, identifier)).fetchone()
            if not row:
                raise KeyError(identifier)
            return self._fact(row)

    def admin_changes(self, limit=25, offset=0):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM audit WHERE namespace=? ORDER BY id DESC LIMIT ? OFFSET ?", (self.namespace, min(limit, 100), offset)).fetchall()
            total = db.execute("SELECT count(*) FROM audit WHERE namespace=?", (self.namespace,)).fetchone()[0]
            return {"items": [dict(r, detail=json.loads(r["detail"])) for r in rows], "total": total}

    def admin_status(self, user_id=None):
        with self.connect() as db:
            suffix, params = (" WHERE user_id=? OR user_id='__shared__'", [user_id]) if user_id else ("", [])
            return {"knowledge_revision": self.head(), "capsules": [dict(r) for r in db.execute("SELECT * FROM capsules" + suffix, params)],
                    "jobs": [dict(r) for r in db.execute("SELECT * FROM jobs" + (" WHERE user_id=?" if user_id else "") + " ORDER BY updated_at DESC LIMIT 50", [user_id] if user_id else [])],
                    "summaries": [dict(r) for r in db.execute("SELECT session_id,user_id,version,covered,updated_at FROM summaries" + (" WHERE user_id=?" if user_id else ""), [user_id] if user_id else [])],
                    "counting_method": "conservative_utf8_bytes_not_exact_tokens"}
