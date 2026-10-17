"""Real dataset/provider + actual workflow with FIXED model proposals, not LLM quality."""
from pathlib import Path
import pytest

from backend.chains.gemma import ModelReply
from backend.chains.service import CopilotService
from backend.memory import MemoryStore


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def dataset_provider(tmp_path_factory):
    data = ROOT / "dataset" / "sample-data"
    if not data.is_dir():
        pytest.skip("Acquire the original dataset clone before real-data integration checks")
    from backend.retrieval.provider import create_provider
    return create_provider([data], tmp_path_factory.mktemp("real-provider") / "index.sqlite")


class ProposalModel:
    configured = True
    def __init__(self, plan):
        self.plan, self.received = plan, []
    async def generate(self, purpose, system, payload, **kwargs):
        self.received.append((purpose, payload))
        if purpose == "planner":
            result = self.plan
        elif purpose == "summary":
            result = {"summary": "Previous source-backed discussion", "covered": payload["target"]}
        else:
            blocks = []
            for item in payload["evidence_pack"]["result_catalog"]:
                if item["evidence_ids"]:
                    blocks.append({"type": "table", "title": "Verified data", "result_set_id": item["id"], "evidence_ids": item["evidence_ids"], "encoding": {}})
            result = {"narrative": "Verified data and attributed source references are displayed.", "blocks": blocks}
        return ModelReply(result, {"fixed_proposal_fixture": True}, live=False)


def user_id(service, name):
    return next(u["user_id"] for u in service.users() if u["name"] == name)


async def ask(service, uid, sid, run, text, plan):
    service.model = ProposalModel(plan)
    service.memory.create_session(uid, sid)
    result = await service.answer(user_id=uid, session_id=sid, run_id=run, message=text)
    assert result["generation"]["live"] is False
    assert result["budget"]["long_term"] <= 2000
    assert result["budget"]["short_term"] <= 1000
    assert result["budget"]["retrieved_context"] <= 2000
    return result


def result_rows(answer):
    return [row for result in answer["results"].values() for row in result["rows"]]


def test_supplied_dataset_bootstrap_through_provider_only(dataset_provider, tmp_path):
    service = CopilotService(dataset_provider, MemoryStore(tmp_path / "memory.sqlite", dataset_provider.namespace), ProposalModel({}))
    assert len(service.users()) == 15  # regression fixture, not runtime assumption
    ready = service.readiness()
    assert ready["data_ready"] is True and ready["asset_count"] == 200


@pytest.mark.asyncio
async def test_real_q12_q13_q15_runtime_authority_reaches_other_users(dataset_provider, tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite", dataset_provider.namespace)
    service = CopilotService(dataset_provider, store, ProposalModel({}))
    michael, jessica = [user_id(service, n) for n in ("Michael Turner", "Jessica Reed")]
    correction = {"kind": "correction", "scope": "shared", "subject_ids": ["WELL-0164"], "statement": "The wellhead reading was corrected to 41.0 C after a faulty instrument.",
                  "source_quote": "The field crew re-measured the wellhead at 41.0", "target_record_id": "INS-0164-0205", "field": "wellhead_temp_c", "value": 41.0, "reason": "Faulty instrument"}
    await ask(service, michael, "q12", "q12-write", "The field crew re-measured the wellhead at 41.0; the instrument was faulty.",
              {"queries": [{"collection": "assets", "metric": "status", "filters": {"asset_id": "WELL-0164"}}], "memory_proposals": [correction]})
    original = store.authority()["corrections"][0]
    assert original["original_value"] == 24.0
    answer = await ask(service, jessica, "q15", "q15-status", "Is WELL-0164 producing?", {"queries": [{"collection": "assets", "metric": "status", "filters": {"asset_id": "WELL-0164"}}]})
    row = result_rows(answer)[0]
    assert row["wellhead_temp_c"] == 41.0 and row["producing"] is True
    assert any(e.get("author") == "Michael Turner" for e in answer["evidence"].values())
    assert "Pump jack not moving" in row["notes"]
    query = {"collection": "inspections", "metric": "spills", "filters": {"asset_id": "WELL-0151"}, "start": "2026-09-24", "end": "2026-09-24"}
    volume = {"kind": "correction", "scope": "shared", "subject_ids": ["WELL-0151"], "statement": "Field measured spill volume is 5.4 bbl.", "source_quote": "The field crew measured 5.4 bbl", "target_record_id": "INS-0151-0201", "field": "spill_est_volume_bbl", "value": 5.4}
    await ask(service, michael, "q13", "q13-write", "The field crew measured 5.4 bbl; the old reading was wrong.", {"queries": [query], "memory_proposals": [volume]})
    after = await ask(service, jessica, "q15", "q15-volume", "Show the measured spill at WELL-0151 on 24 Sep", {"queries": [query]})
    assert result_rows(after)[0]["spill_est_volume_bbl"] == 5.4
    assert any(c["original_value"] == 4.5 for c in store.authority()["corrections"])


@pytest.mark.asyncio
async def test_real_q14_type_override_and_new_session(dataset_provider, tmp_path):
    service = CopilotService(dataset_provider, MemoryStore(tmp_path / "memory.sqlite", dataset_provider.namespace), ProposalModel({}))
    uid = user_id(service, "Michael Turner")
    area = next(row["area_id"] for row in dataset_provider.query({"collection": "areas", "metric": "records"}, service.context(uid), {})["rows"] if row["name"] == "Northeast Block 7")
    query = {"collection": "maintenance", "metric": "rca", "filters": {"area_id": area, "equipment_kind": "pump_jack"}, "group_by": ["asset_id"], "limit": 100}
    before = await ask(service, uid, "q14", "q14-before", "Which wells need pump jack root-cause analysis?", {"queries": [query]})
    assert {r["asset_id"] for r in result_rows(before) if r["rca_required"]} == {"WELL-0108", "WELL-0121", "WELL-0138"}
    rule = {"kind": "rule", "scope": "shared", "subject_kind": "type", "subject_ids": ["T350"], "statement": "T350 pump jack RCA after 2 repairs.", "source_quote": "For all T350 use a pump jack RCA threshold of 2 repairs", "well_type": "T350", "equipment_kind": "pump_jack", "threshold": 2, "valid_from": "2026-10-16"}
    await ask(service, uid, "q14", "q14-rule", rule["source_quote"], {"memory_proposals": [rule]})
    after = await ask(service, uid, "q14-new", "q14-after", "Which wells need pump jack root-cause analysis?", {"queries": [query]})
    assert {r["asset_id"] for r in result_rows(after) if r["rca_required"]} == {"WELL-0108", "WELL-0120", "WELL-0121", "WELL-0138"}


@pytest.mark.asyncio
async def test_real_q16_shared_plan_private_reference_negative(dataset_provider, tmp_path):
    service = CopilotService(dataset_provider, MemoryStore(tmp_path / "memory.sqlite", dataset_provider.namespace), ProposalModel({}))
    jake, michael, jessica = [user_id(service, n) for n in ("Jake Morales", "Michael Turner", "Jessica Reed")]
    text = "FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover."
    plan = {"kind": "plan", "scope": "shared", "subject_ids": ["WELL-0007"], "statement": "WELL-0007 planned workover from 17 Oct for about ten days.", "source_quote": text, "planned_start": "2026-10-17", "planned_end": "2026-10-27"}
    await ask(service, jake, "q16-jake", "q16-save", text, {"memory_proposals": [plan]})
    other = await ask(service, michael, "q16-michael", "q16-read", "Is any downtime planned for WELL-0007?", {"queries": []})
    assert any(e.get("author") == "Jake Morales" for e in other["evidence"].values())
    assert "workover" in str(service.model.received)
    area = next(row["area_id"] for row in dataset_provider.query({"collection": "areas", "metric": "records"}, service.context(michael), service.memory.authority())["rows"] if row["name"] == "Northeast Block 7")
    prior = await ask(service, michael, "q11-day1", "q11-rank", "Which 3 wells had most downtime?", {"queries": [{"collection": "inspections", "metric": "downtime_days", "filters": {"area_id": area}, "start": "2026-06-16", "end": "2026-10-16", "limit": 3}]})
    assert {r["asset_id"] for r in result_rows(prior)} == {"WELL-0121", "WELL-0138", "WELL-0107"}
    from datetime import datetime, timezone, timedelta
    with service.memory.connect() as db:
        db.execute("UPDATE episodes SET created_at=? WHERE user_id=?", ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), michael))
    costs = await ask(service, michael, "q11-day2", "q11-costs", "For the three wells we discussed yesterday, what have repairs cost this year?", {"queries": [{"collection": "maintenance", "metric": "maintenance_cost_usd", "start": "2026-01-01", "end": "2026-10-16", "group_by": ["asset_id"]}]})
    assert {r["asset_id"]: r["maintenance_cost_usd"] for r in result_rows(costs)} == {"WELL-0121": 25794.0, "WELL-0138": 46942.0, "WELL-0107": 5176.0}
    service.memory.create_session(jessica, "q16-jessica")
    missing = await service.answer(user_id=jessica, session_id="q16-jessica", run_id="q16-negative", message="For the three wells we discussed yesterday, what have repairs cost this year?")
    assert not missing["results"] and "do not have" in missing["narrative"]
