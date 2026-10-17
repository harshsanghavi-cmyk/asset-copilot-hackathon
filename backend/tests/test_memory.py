import pytest

from backend.contracts import MemoryDraft
from backend.memory import MemoryStore
from backend.memory.budget import estimate, make_pack, pack_evidence
from backend.memory.store import ScopeError


def draft(**kwargs):
    values = dict(kind="plan", scope="shared", subject_ids=["WELL-X"], statement="WELL-X planned work", source_quote="WELL-X planned work")
    values.update(kwargs)
    return MemoryDraft(**values)


def test_shared_private_provenance_idempotency_and_conflicts(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    saved = store.commit_draft("A", "run", 0, draft(), "WELL-X planned work")
    assert store.commit_draft("A", "run", 0, draft(), "WELL-X planned work") == saved
    assert store.head() == 1
    assert store.facts("B")[0]["author_user_id"] == "A"
    private = draft(kind="preference", subject_kind="user", subject_ids=[], statement="I prefer tables", source_quote="I prefer tables")
    store.commit_draft("A", "pref", 0, private, "I prefer tables")
    assert any(f["scope"] == "private" for f in store.facts("A"))
    assert all(f["scope"] == "shared" for f in store.facts("B"))
    correction = draft(kind="correction", target_record_id="I-X", field="wellhead_temp_c", value=41.0, source_quote="reading wrong 41.0", statement="Correct reading to 41.0")
    first = store.commit_draft("A", "correct", 0, correction, "reading wrong 41.0", original_value=24.0)
    competing = correction.model_copy(update={"value": 22.0, "source_quote": "reading wrong 22.0"})
    second = store.commit_draft("B", "compete", 0, competing, "reading wrong 22.0", original_value=24.0)
    assert first["status"] == "accepted" and second["status"] == "conflict_pending"
    assert [c["value"] for c in store.authority()["corrections"]] == [41.0]
    superseding = correction.model_copy(update={"value": 42.0, "source_quote": "reading wrong 42.0", "supersedes": first["id"]})
    with pytest.raises(ValueError, match="explicit supersession"):
        store.commit_draft("A", "implicit-replace", 0, superseding, "reading wrong 42.0", original_value=24.0)
    store.commit_draft("A", "replace", 0, superseding, "Replace earlier correction: reading wrong 42.0", original_value=24.0)
    assert [c["value"] for c in store.authority()["corrections"]] == [42.0]
    assert store.admin_detail(first["id"])["data"]["original_value"] == 24.0
    with store.connect() as db:
        import json
        capsule = db.execute("SELECT manifest FROM capsules WHERE user_id='__shared__'").fetchone()
        canonical_ids = {r[0] for r in db.execute("SELECT id FROM facts WHERE scope='shared' AND status NOT IN ('superseded','withdrawn')")}
        assert set(json.loads(capsule[0])) == canonical_ids
        assert first["id"] not in canonical_ids
    with pytest.raises(ValueError, match="source quote"):
        store.commit_draft("A", "bad-number", 0, correction.model_copy(update={"value": 410.0}), "reading wrong 41.0", original_value=24.0)


def test_scope_source_validation_and_type_validity(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    with pytest.raises(ValueError, match="source quote"):
        store.commit_draft("A", "bad", 0, draft(), "Something else")
    rule = draft(kind="rule", subject_kind="type", subject_ids=["T350"], well_type="T350", equipment_kind="pump_jack", threshold=2,
                 source_quote="For all T350 use 2 repairs", statement="T350 pump-jack RCA after two repairs", valid_from="2026-10-16", valid_to="2026-11-01")
    store.commit_draft("A", "rule", 0, rule, "For all T350 use 2 repairs")
    assert store.authority()["rule_overrides"][0]["value"] == 2
    assert store.authority("2026-11-01")["rule_overrides"] == []
    unrelated = rule.model_copy(update={"well_type": "T200", "subject_ids": ["T200"], "source_quote": "For all T200 use 2 repairs"})
    assert store.commit_draft("A", "other-type", 0, unrelated, "For all T200 use 2 repairs")["status"] == "accepted"
    equipment = rule.model_copy(update={"equipment_kind": "flowline"})
    assert store.commit_draft("A", "other-equipment", 0, equipment, "For all T350 use 2 repairs")["status"] == "accepted"
    with pytest.raises(ValueError):
        draft(valid_from="2026-99-03")
    with pytest.raises(ValueError, match="end must follow"):
        draft(valid_from="2026-11-01", valid_to="2026-10-16")


def test_extractor_cannot_publish_private_conversational_entity_set(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    text = "Remember the three wells we discussed yesterday."
    proposal = draft(scope="shared", subject_ids=["W1", "W2", "W3"], statement="My earlier discussion concerned W1, W2 and W3.", source_quote=text)
    receipt = store.commit_draft("A", "episodic", 0, proposal, text)
    assert receipt["scope"] == "private"
    assert store.head() == 0 and store.private_head("A") == 1
    assert store.facts("B") == []


def test_private_reference_dates_and_ambiguity(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    for i, ids in enumerate([["W1"], ["W2"]]):
        sid, run = "thread" + str(i), "run" + str(i)
        store.create_session("A", sid)
        store.begin(run, sid, "A", "Show well")
        store.finish(run, sid, "A", {"narrative": "Well", "reference_date": "2026-10-16", "results": {"r": {"rows": [{"asset_id": x} for x in ids]}}})
    assert store.resolve_reference("A", "that well")["status"] == "ambiguous"
    assert store.resolve_reference("A", "that well", session_id="thread0")["entity_ids"] == ["W1"]
    with store.connect() as db:
        db.execute("UPDATE episodes SET created_at='2026-10-15T12:00:00Z' WHERE run_id='run0'")
        db.execute("UPDATE episodes SET created_at='2026-10-16T12:00:00Z' WHERE run_id='run1'")
    dated = store.resolve_reference("A", "that well yesterday", conversation_date="2026-10-16")
    assert dated["entity_ids"] == ["W1"]
    assert store.resolve_reference("A", "yesterday", conversation_date="2026-10-18")["status"] == "absent"
    assert store.resolve_reference("B", "that well")["status"] == "absent"


def test_session_ownership_delete_and_exact_episode(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    sid = store.create_session("A", "thread")["id"]
    with pytest.raises(ScopeError):
        store.history(sid, "B")
    store.begin("r1", sid, "A", "Show the three wells")
    answer = {"narrative": "Three wells", "reference_date": "2026-10-16", "results": {"r": {"rows": [{"asset_id": "W1"}, {"asset_id": "W2"}, {"asset_id": "W3"}]}}}
    assert store.finish("r1", sid, "A", answer) == 1
    assert store.finish("r1", sid, "A", answer) == 1
    assert store.resolve_reference("A", "three wells")["entity_ids"] == ["W1", "W2", "W3"]
    assert store.resolve_reference("B", "three wells")["status"] == "absent"
    assert store.list_sessions("A", "three")["total"] == 1
    store.rename_session(sid, "A", "Custom name")
    store.rename_session(sid, "A", "Generated name", manual=False)
    assert store.session(sid, "A")["title"] == "Custom name"
    store.delete_session(sid, "A")
    with pytest.raises(ScopeError):
        store.history(sid, "A")


def test_durable_error_and_client_message_retry_aliases(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.create_session("A", "thread")
    store.begin("first-run", "thread", "A", "hello", "original-client-id")
    assert store.history("thread", "A")["messages"][0]["run_status"] == "running"
    store.fail("first-run", "A", "Gemma provider returned HTTP 500: Internal error", "provider_error")
    history = store.history("thread", "A")["messages"]
    assert history[0]["client_message_id"] == "original-client-id"
    assert history[0]["run_id"] == "first-run" and history[0]["run_status"] == "error"
    assert history[1]["status"] == "error" and history[1]["error_code"] == "provider_error"
    assert store.begin("second-run", "thread", "A", "hello", "original-client-id")["id"] == "first-run"
    assert store.begin("third-run", "thread", "A", "hello", "first-run:user")["id"] == "first-run"
    assert len([m for m in store.history("thread", "A")["messages"] if m["role"] == "user"]) == 1
    with pytest.raises(ValueError):
        store.begin("different-text", "thread", "A", "another question", "original-client-id")


def test_summary_ten_exchange_overflow_and_retry(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    sid = store.create_session("A", "thread")["id"]
    for i in range(1, 21):
        run = "r" + str(i)
        store.begin(run, sid, "A", "Explain this well " * 20)
        answer = {"narrative": "A supported response " * 20, "reference_date": "2026-10-16", "results": {}}
        store.finish(run, sid, "A", answer)
        store.finish(run, sid, "A", answer)
    with store.connect() as db:
        periodic = [r[0] for r in db.execute("SELECT target FROM jobs WHERE kind='periodic' ORDER BY target")]
        assert periodic == [7, 17]
        assert db.execute("SELECT count(*) FROM jobs WHERE kind='overflow'").fetchone()[0] > 0
        assert db.execute("SELECT completed FROM sessions").fetchone()[0] == 20
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 40


def test_budget_caps_hold_and_evidence_does_not_mutate_full_results():
    facts = [{"id": str(i), "statement": "évidence " * 100, "kind": "plan"} for i in range(30)]
    pack = make_pack(private_facts=facts, shared_facts=facts, summary="long summary " * 1000,
                     recent=[{"role": "user", "text": "long " * 1000}], episodes=[{"id": "episode:x"}],
                     private_revision=1, knowledge_revision=2)
    assert estimate(pack["long_term"]) <= 2000
    assert estimate(pack["short_term"]) <= 1000
    results = {"r": {"result_set_id": "r", "columns": [{"key": "x"}], "rows": [{"x": i} for i in range(200)], "evidence_ids": ["e"]}}
    packed, accounting = pack_evidence(results, {"e": {"id": "e", "excerpt": "very large " * 1000}})
    assert estimate(packed) <= 2000
    assert len(results["r"]["rows"]) == 200
    assert accounting["partial_evidence"] is True


def test_private_lexical_expansion_is_scoped_before_ranking(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.create_session("A", "thread-A")
    store.create_session("B", "thread-B")
    selected = draft(kind="work_context", scope="private", subject_kind="user", subject_ids=[],
                     statement="My supervisor is Morgan.", source_quote="My supervisor is Morgan.")
    store.commit_draft("A", "original", 0, selected, selected.source_quote)
    for i in range(12):
        other = draft(kind="preference", scope="private", subject_kind="user", subject_ids=[],
                      statement=f"Preference distractor {i}: concise operational updates.", source_quote=f"Preference distractor {i}: concise operational updates.")
        store.commit_draft("A", "distractor-" + str(i), 0, other, other.source_quote)
    a = store.context("A", "thread-A", "Who is my supervisor?")
    b = store.context("B", "thread-B", "Who is my supervisor?")
    assert "Morgan" in json_text(a["long_term"])
    assert "Morgan" not in json_text(b)
    assert estimate(a["long_term"]) <= 2000


def json_text(value):
    import json
    return json.dumps(value)


def test_authority_fact_set_and_revision_share_one_snapshot(tmp_path, monkeypatch):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.commit_draft("A", "initial", 0, draft(), "WELL-X planned work")
    original = store._facts_in
    def interleaved(db, user_id, *args, **kwargs):
        facts = original(db, user_id, *args, **kwargs)
        next_fact = draft(statement="WELL-X another attributed plan", source_quote="WELL-X another attributed plan")
        store.commit_draft("B", "concurrent", 0, next_fact, next_fact.source_quote)
        return facts
    monkeypatch.setattr(store, "_facts_in", interleaved)
    snapshot = store.authority()
    assert snapshot["knowledge_revision"] == 1
    assert len(snapshot["shared_claims"]) == 1
    assert store.head() == 2


def test_ordinal_reference_uses_first_own_question_not_latest_topic(tmp_path):
    store=MemoryStore(tmp_path/'memory.sqlite');store.create_session('A','topics')
    for run,question,ids in [('pumps','Which pumps need work?',['W1','W2']),('gas','Inspect another gas incident',['W3'])]:
        store.begin(run,'topics','A',question)
        store.finish(run,'topics','A',{'narrative':'Actual records','reference_date':'2027-01-15','results':{'r':{'rows':[{'asset_id':i} for i in ids]}}})
    assert store.resolve_reference('A','Back to the pumps from the first question',session_id='topics')['entity_ids']==['W1','W2']
    assert store.resolve_reference('B','Back to the first question',session_id='topics')['status']=='absent'


def test_asset_hearsay_work_context_is_shared_but_personal_privacy_wins(tmp_path):
    store=MemoryStore(tmp_path/'memory.sqlite')
    text='Kevin told me WELL-0577 had its pump swapped.'
    fact=draft(kind='work_context',scope='private',subject_kind='user',subject_ids=['U-X'],statement=text,source_quote=text)
    receipt=store.commit_draft('A','hearsay',0,fact,text)
    assert receipt['scope']=='shared'
    visible=store.facts('B')[0]
    assert visible['kind']=='observation' and visible['status']=='unconfirmed'
    assert store.public_fact(visible)['attribution_basis']=='hearsay'
    private=store.commit_draft('A','private-hearsay',0,fact,text+' Keep this just for me.')
    assert private['scope']=='private'
