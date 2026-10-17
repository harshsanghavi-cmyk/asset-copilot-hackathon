"""Official scenario evaluation only: goldens never enter the runtime/provider.

Runs real Gemma through CopilotService with isolated memory fixtures and the SAME
persistent global request limiter as the serving API. Preserves each result and
failure; generation limits stop the run, rather than substituting fixed answers.
"""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
import hashlib
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv

from backend.chains.gemma import GemmaClient, GlobalLimiter, MODEL
from backend.chains.service import CopilotService
from backend.contracts import ModelUnavailable
from backend.memory import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = {
 "Q1": "Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card.",
 "Q2": "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.",
 "Q3": "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.",
 "Q4": "How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.",
 "Q5": "How many days was WELL-0001 down in 2025?",
 "Q6": "Which 3 wells in Northeast Block 7 had the most downtime from 16 Jun to 16 Oct 2026? Show a bar chart.",
 "Q7": "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.",
 "Q8": "Show a heatmap of 2026 spills by geographic area and month.",
 "Q9": "Which rules has WELL-0001 broken in the last 12 months, and what is still open?",
 "Q10": "In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?",
 "Q11": "For the three wells we discussed yesterday, what have repairs cost this year?",
 "Q12": "The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.",
 "Q13": "The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.",
 "Q14": "Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?",
 "Q15": "Is WELL-0164 producing oil right now?",
 "Q16": "FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.",
 "Q17": "WELL-0175 has been shut in for planned work since 14 Oct.",
 "Q18": "Was the 20 Aug spill at WELL-0101 real oil?",
}


def rows(answer):
    return [r for result in answer.get("results", {}).values() for r in result.get("rows", [])]


def inspection_rows(answer):
    unique = {}
    for row in rows(answer):
        if row.get("inspection_id") and "wellhead_temp_c" in row and "ambient_temp_c" in row:
            unique[row["inspection_id"]] = row
    return list(unique.values())


def scalar(answer, key, expected, tolerance=0.001):
    return any(isinstance(r.get(key), (int, float)) and abs(r[key] - expected) <= tolerance for r in rows(answer))


def assets(answer):
    return {r.get("asset_id") for r in rows(answer) if r.get("asset_id")}


def evidence_text(answer):
    return json.dumps(answer.get("evidence", {}), ensure_ascii=False)


def check(number, answer):
    text = answer.get("narrative", "")
    data = rows(answer)
    visuals = {b["type"] for b in answer.get("blocks", [])}
    checks = {}
    if number == "Q1":
        checks = {"not_producing": any(r.get("producing") in (False, 0) for r in data), "delta_3_2": scalar(answer, "delta_c", 3.2), "inspection_evidence": "INS-0001-0203" in evidence_text(answer), "status_card": "status" in visuals}
    elif number == "Q2":
        checks = {"four_wells": assets(answer) == {"WELL-0164", "WELL-0170", "WELL-0172", "WELL-0175"}, "table": "table" in visuals}
    elif number == "Q3":
        observations = inspection_rows(answer)
        checks = {"13_observations": len(observations) == 13, "two_nonproducing": sum(r.get("producing") in (0, False) for r in observations) == 2, "line": "line" in visuals}
    elif number == "Q4":
        spills = [r for r in data if r.get("spill_detected") in (True, 1)]
        checks = {"six_effective_spills": len(spills) == 6 or scalar(answer, "spill_count", 6),
                  "volume_15_1": scalar(answer, "spill_volume_bbl", 15.1) or abs(sum(r.get("spill_est_volume_bbl") or 0 for r in spills) - 15.1) < 0.001,
                  "table": "table" in visuals}
    elif number == "Q5":
        checks = {"downtime_21": scalar(answer, "downtime_days", 21)}
    elif number == "Q6":
        values = {r.get("asset_id"): r.get("downtime_days") for r in data}
        checks = {"ranking_values": all(values.get(a) == v for a, v in {"WELL-0121": 49, "WELL-0138": 42, "WELL-0107": 42}.items()), "exactly_three_wells": set(values) == {"WELL-0121", "WELL-0138", "WELL-0107"}, "bar": "bar" in visuals}
    elif number == "Q7":
        checks = {"four_matching_wells": assets(answer) == {"WELL-0151", "WELL-0165", "WELL-0175", "WELL-0186"}, "map": "map" in visuals}
    elif number == "Q8":
        totals = {}
        for r in data:
            k = r.get("area_id") or r.get("area_name")
            if k:
                totals[k] = totals.get(k, 0) + (r.get("spill_count") or 0)
        checks = {"four_area_totals": sorted(totals.values()) == [26, 35, 37, 43], "heatmap": "heatmap" in visuals}
    elif number == "Q9":
        checks = {"four_protocols_in_answer": all(p in text for p in ["SR-01", "SR-02", "SR-03", "RC-04"]), "fine_5000_supported": scalar(answer, "fine_usd", 5000) or "5000" in evidence_text(answer) or "5,000" in evidence_text(answer)}
    elif number == "Q10":
        late = {r.get("asset_id") for r in data if isinstance(r.get("containment_hours"), (int, float)) and r["containment_hours"] > 4}
        checks = {"two_late_wells": late == {"WELL-0082", "WELL-0100"}, "table": "table" in visuals}
    elif number == "Q11":
        values = {r.get("asset_id"): r.get("maintenance_cost_usd") for r in data}
        checks = {"private_set_costs": all(values.get(a) == v for a, v in {"WELL-0121": 25794, "WELL-0138": 46942, "WELL-0107": 5176}.items())}
    elif number == "Q12":
        checks = {"three_wells_after_correction": assets(answer) == {"WELL-0170", "WELL-0172", "WELL-0175"}}
    elif number == "Q13":
        checks = {"corrected_volume": scalar(answer, "spill_est_volume_bbl", 5.4) or "5.4" in evidence_text(answer), "reportability_discussed": bool(__import__('re').search(r"reportable|report.*regulat", text, __import__('re').I))}
    elif number == "Q14":
        required = {r.get("asset_id") for r in data if r.get("rca_required") in (True, 1)}
        checks = {"type_override_membership": required == {"WELL-0108", "WELL-0120", "WELL-0121", "WELL-0138"}}
    elif number == "Q15":
        checks = {"cross_user_corrected_status": scalar(answer, "wellhead_temp_c", 41.0) and any(r.get("producing") in (True, 1) for r in data), "attribution_source": "memory:" in evidence_text(answer)}
    elif number == "Q16":
        checks = {"no_other_user_private_reference": not assets(answer) and bool(__import__('re').search(r"do not have|provide.*well|absent|earlier.*discussion", text, __import__('re').I))}
    elif number == "Q17":
        checks = {"inspection_still_not_producing": any(r.get("producing") in (False, 0) for r in data), "disagreement_visible": bool(__import__('re').search(r"unconfirmed|disagree|conflict|claim|reported", text, __import__('re').I))}
    elif number == "Q18":
        checks = {"detection_retained": any(r.get("spill_detected") in (True, 1) for r in data), "both_disagreeing_notes": all(x in evidence_text(answer) + text for x in ["CTX-0101-002", "CTX-0101-003"])}
    checks["has_source_evidence"] = bool(answer.get("evidence")) if number != "Q16" else True
    return checks


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=list(QUESTIONS))
    parser.add_argument("--output", default=str(ROOT / "runtime" / "live-evaluation.json"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--run-tag", help="Isolated fixture/checkpoint namespace; reuse only with --resume")
    parser.add_argument("--generation-limit", type=int, help="Bounded shared generation guard for this controlled evaluation")
    parser.add_argument("--dataset-root", default=str(ROOT / "dataset" / "sample-data"), help="The original 18 goldens apply to sample-data only")
    parser.add_argument("--index-db", default=str(ROOT / "runtime" / "retrieval.sqlite"))
    parser.add_argument("--reference-date", default="2026-10-16")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    from backend.retrieval.provider import create_provider  # composition root only
    if Path(args.dataset_root).resolve() != (ROOT / "dataset" / "sample-data").resolve() or args.reference_date != "2026-10-16":
        parser.error("The 18-case sample oracle requires sample-data and 2026-10-16; use a separate final-data evaluation for the 600-well release")
    provider = create_provider([Path(args.dataset_root)], Path(args.index_db))
    limiter = GlobalLimiter(ROOT / "runtime" / "model-requests.sqlite", max_generations=args.generation_limit or int(os.environ.get("ASSET_GENERATION_LIMIT", "20")))
    model = GemmaClient(os.environ.get("GOOGLE_API_KEY"), limiter, streaming=os.environ.get("ASSET_GEMMA_STREAM") == "1", priority=10)
    class EvaluationRecorder:
        """Synthetic evaluation replies only; never wraps serving conversations."""
        configured = model.configured
        model_id = MODEL
        provider = "google"
        async def count_tokens(self, *args, **kwargs):
            return await model.count_tokens(*args, **kwargs)
        async def generate(self, purpose, system, payload, **kwargs):
            reply = await model.generate(purpose, system, payload, **kwargs)
            with (ROOT / "runtime" / "evaluation-model-replies.jsonl").open("a") as stream:
                stream.write(json.dumps({"model": MODEL, "purpose": purpose, "data": reply.data, "usage": reply.usage, "call_id": reply.call_id}, ensure_ascii=False) + "\n")
            return reply
    recorded_model = EvaluationRecorder()
    output = Path(args.output)
    report = json.loads(output.read_text()) if output.exists() else {"model": MODEL, "results": {}, "boundary": "Actual model workflow on synthetic official dataset; independent memory fixtures, no goldens in runtime"}
    run_tag = args.run_tag or (report.get("run_tag") if args.resume else None) or uuid.uuid4().hex[:12]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_tag):
        parser.error("--run-tag must contain 1..64 letters, digits, underscores or hyphens")
    if output.exists() and (not args.resume or report.get("run_tag") != run_tag):
        archive = output.with_name(output.stem + "-prior-" + uuid.uuid4().hex[:8] + output.suffix)
        archive.write_text(output.read_text())
        report = {"model": MODEL, "results": {}, "prior_report": str(archive)}
    fixture_dir = ROOT / "runtime" / "evaluation-memory" / run_tag
    if fixture_dir.exists() and not args.resume:
        parser.error("This run tag already has fixtures; choose a fresh --run-tag or explicitly --resume")
    fixture_dir.mkdir(parents=True, exist_ok=True)
    report["run_tag"] = run_tag
    report["dataset_root"] = str(Path(args.dataset_root).resolve())
    report["dataset_revision"] = provider.catalog().get("dataset_revision")
    report["reference_date"] = args.reference_date
    report["fixture_dir"] = str(fixture_dir)
    report["assessment_boundary"] = "Automated checks only; semantic acceptance requires independent review. Fresh namespace does not reuse previous runs."
    fingerprint = hashlib.sha256()
    for source in sorted((ROOT / "backend").rglob("*")):
        if source.is_file() and source.suffix in {".py", ".md", ".yaml"} and not any(p in {".venv", "__pycache__"} for p in source.parts):
            fingerprint.update(str(source.relative_to(ROOT)).encode())
            fingerprint.update(source.read_bytes())
    report["code_fingerprint"] = fingerprint.hexdigest()
    report["model"] = MODEL
    services = {}
    def service_for(case):
        group = "corrections" if case in {"Q12", "Q13", "Q15"} else "continuity" if case in {"Q11", "Q16"} else case
        if group not in services:
            memory = MemoryStore(fixture_dir / (group + ".sqlite"), provider.namespace)
            services[group] = CopilotService(provider, memory, recorded_model)
        return services[group]
    users = CopilotService(provider, MemoryStore(fixture_dir / "bootstrap.sqlite", provider.namespace), model).users()
    by_name = {u["name"]: u["user_id"] for u in users}
    michael, jessica, jake = [by_name[n] for n in ("Michael Turner", "Jessica Reed", "Jake Morales")]
    async def ask(service, case, phase, text, user=michael, new_chat=False):
        sid = "eval-" + run_tag + "-" + case + ("-" + phase if new_chat else "")
        service.memory.create_session(user, sid)
        return await service.answer(user_id=user, session_id=sid, run_id="eval-" + run_tag + "-" + case + "-" + phase,
                                    message=text, reference_date=args.reference_date)
    blocked = False
    selected = set(args.only)
    if "Q15" in selected:
        selected.update({"Q12", "Q13"})
    if "Q16" in selected:
        selected.add("Q11")
    unknown = selected - QUESTIONS.keys()
    if unknown:
        parser.error("Unknown scenarios: " + ", ".join(sorted(unknown)))
    for case in [q for q in QUESTIONS if q in selected]:
        if args.resume and report["results"].get(case, {}).get("status") == "passed":
            continue
        if report["results"].get(case, {}).get("status") not in {None, "not_run"}:
            report.setdefault("attempt_history", []).append({"case": case, "previous": report["results"][case], "replaced_at": datetime.now(timezone.utc).isoformat()})
        if blocked:
            report["results"][case] = {"status": "blocked", "reason": "Initial generation-attempt allowance exhausted; coordinator review required"}
            continue
        service = service_for(case)
        before = limiter.stats()["generation_attempts"]
        try:
            if case == "Q11":
                await ask(service, case, "day1", QUESTIONS["Q6"])
                # Isolated test-fixture conversation date only, never original data.
                with service.memory.connect() as db:
                    db.execute("UPDATE episodes SET created_at=?", ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),))
                answer = await ask(service, case, "day2", QUESTIONS[case], new_chat=True)
            elif case == "Q12":
                correction = await ask(service, case, "write", QUESTIONS[case])
                report.setdefault("extra_checks", {})[case] = {"correction_answer": correction}
                answer = await ask(service, case, "after", QUESTIONS["Q2"])
            elif case == "Q14":
                await ask(service, case, "baseline", QUESTIONS[case])
                await ask(service, case, "override", "Note for all T350 wells: our team now wants a pump jack root-cause analysis after 2 repairs, not 3.")
                answer = await ask(service, case, "after", QUESTIONS[case], new_chat=True)
            elif case == "Q15":
                # Explicit dependencies: fixture is shared with Q12/Q13.
                # Validate actual effective values, rather than assuming earlier delivery committed a correction.
                snapshot = service.memory.authority()
                context = {"dataset_namespace":provider.namespace, "reference_date":"2026-10-16", "user_id":jessica}
                effective = provider.query({"collection":"assets", "metric":"status", "filters":{"asset_id":"WELL-0164"}}, context, snapshot)
                if not any(r.get("wellhead_temp_c") == 41.0 for r in effective.get("rows", [])):
                    raise RuntimeError("Q15_DEPENDENCY_Q12")
                corrected_spill = provider.query({"collection":"inspections", "metric":"spills", "filters":{"asset_id":"WELL-0151"}, "start":"2026-09-24", "end":"2026-09-24"}, context, snapshot)
                if not any(r.get("spill_est_volume_bbl") == 5.4 for r in corrected_spill.get("rows", [])):
                    raise RuntimeError("Q15_DEPENDENCY_Q13")
                answer = await ask(service, case, "jessica", QUESTIONS[case], user=jessica, new_chat=True)
                laura = by_name["Laura Simmons"]
                laura_answer = await ask(service, case, "laura", "Which spills in Northeast Block 8 in the last 90 days needed a report to the regulator?", user=laura, new_chat=True)
                report.setdefault("extra_checks", {})[case] = {"laura_answer":laura_answer}
            elif case == "Q16":
                await ask(service, case, "jake", QUESTIONS[case], user=jake, new_chat=True)
                shared = await ask(service, case, "michael", "Is any downtime planned for WELL-0007?", new_chat=True)
                answer = await ask(service, case, "private-negative", QUESTIONS["Q11"], user=jessica, new_chat=True)
                report.setdefault("extra_checks", {})[case] = {"shared_fact_answer": shared, "shared_fact_retrieved": "Jake" in evidence_text(shared) or "workover" in shared["narrative"].lower()}
            elif case == "Q17":
                await ask(service, case, "michael", QUESTIONS[case])
                tyler = by_name["Tyler Hughes"]
                answer = await ask(service, case, "tyler", "WELL-0175 is running fine.", user=tyler, new_chat=True)
                jake_answer = await ask(service, case, "jake", "WELL-0001 is back online since 14 Oct.", user=jake, new_chat=True)
                report.setdefault("extra_checks", {})[case] = {"jake_answer": jake_answer}
            else:
                answer = await ask(service, case, "answer", QUESTIONS[case])
            checks = check(case, answer)
            if case == "Q15":
                laura_text = laura_answer.get("narrative", "")
                checks["laura_corrected_reportability"] = "WELL-0151" in assets(laura_answer) and (scalar(laura_answer, "spill_est_volume_bbl", 5.4) or "5.4" in evidence_text(laura_answer)) and bool(re.search(r"notice|report|SR-01", laura_text, re.I))
            if case == "Q16":
                checks["shared_plan_recalled"] = bool(report["extra_checks"][case]["shared_fact_retrieved"]) and shared.get("generation", {}).get("status") != "partial"
            if case == "Q17":
                checks["jake_claim_unconfirmed"] = bool(re.search(r"unconfirmed|conflict|disagree|confirm", jake_answer.get("narrative", ""), re.I))
            report["results"][case] = {"status": "passed" if all(checks.values()) else "failed", "checks": checks,
                                      "generation_attempts": limiter.stats()["generation_attempts"] - before, "answer": answer}
        except Exception as exc:
            code = getattr(exc, "code", type(exc).__name__)
            report["results"][case] = {"status": "blocked_dependency" if str(exc).startswith("Q15_DEPENDENCY_") else "blocked" if code == "integration_generation_limit" else "failed",
                                      "error_code": code, "reason": str(exc), "generation_attempts": limiter.stats()["generation_attempts"] - before}
            blocked = code == "integration_generation_limit"
        report["updated_at"] = datetime.now(timezone.utc).isoformat()
        report["usage"] = limiter.stats()
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
        print(case, report["results"][case]["status"], "attempts", report["results"][case].get("generation_attempts", 0), flush=True)
    for case in QUESTIONS:
        report["results"].setdefault(case, {"status": "not_run", "reason": "Not selected in this controlled evaluation pass"})
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
