#!/usr/bin/env python3
"""Run final scenarios against the serving API; all history is persisted by the app."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NAMESPACE = "asset-field-test-2027-01-15"
TITLES = {
    1: "Reservoir pressure", 2: "Best producer", 3: "Gas reports",
    4: "Temporary bypasses", 5: "Regulator letter", 6: "Conflicting status",
    7: "Repair priorities", 8: "Recall and attribution", 9: "Several topics",
    10: "Repair waiting time", 11: "Hotter regions",
}
# Question offsets refer only to the organizer's published final-question file.
SCENARIOS = {
    1: [(0, "Michael Turner", "main")],
    2: [(1, "Robert Hayes", "main")],
    3: [(2, "Laura Simmons", "main")],
    4: [(3, "Chris Dalton", "main")],
    5: [(4, "Michael Turner", "main")],
    6: [(5, "Nathan Pierce", "main")],
    7: [(6, "Robert Hayes", "main"), (7, "Robert Hayes", "main")],
    8: [(8, "Nathan Pierce", "nathan-1"), (9, "Nathan Pierce", "nathan-1"),
        (10, "Robert Hayes", "robert"), (11, "Olivia Grant", "olivia"),
        (12, "Nathan Pierce", "nathan-2")],
    9: [(i, "Robert Hayes", "main") for i in range(13, 19)],
    10: [(19, "Michael Turner", "main")],
    11: [(20, "Olivia Grant", "main")],
}


def now():
    return datetime.now(timezone.utc).isoformat()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--parallel", type=int, choices=[1, 2], default=2)
    parser.add_argument("--run-tag", default=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--expected-model", default="gemini-3.5-flash-lite")
    parser.add_argument("--only", type=int, nargs="*", choices=range(1,12))
    parser.add_argument("--label", default="Gemini")
    args = parser.parse_args()
    selected = set(args.only or SCENARIOS)
    if 9 in selected:
        selected.add(8)
    cases = {q: SCENARIOS[q] for q in SCENARIOS if q in selected}
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.run_tag):
        parser.error("Use a short alphanumeric run tag")
    questions = [" ".join(q.split()) for q in re.findall(r'\*"(.*?)"\*', (ROOT / "dataset/test-data/final-questions.md").read_text(), re.S)]
    if len(questions) != 21:
        raise RuntimeError("The final-question format changed; verify all turns before running")
    out = ROOT / "experiments/06-evaluation/final-sessions" / args.run_tag
    if out.exists():
        raise RuntimeError("This batch directory exists; choose a fresh run tag rather than duplicate writes")
    out.mkdir(parents=True)
    manifest = {"run_tag": args.run_tag, "started_at": now(), "status": "prepared",
                "dataset_namespace": EXPECTED_NAMESPACE, "reference_date": "2027-01-15",
                "expected_model": args.expected_model,
                "parallel_chains": args.parallel, "sessions": [], "turns": [],
                "boundary": "Actual serving API and app database; delivery is separate from semantic correctness."}

    def save():
        target = out / "manifest.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        temporary.replace(target)
        lines = ["# Final scenario sessions", "", f"Batch: `{args.run_tag}` · {manifest['status']}", "",
                 "Open http://localhost:5192, select the named profile, and open the session title below.", "",
                 "| Scenario | Profile | Session title | Session ID |", "|---|---|---|---|"]
        for s in manifest["sessions"]:
            lines.append(f"| Q{s['scenario']:02d} | {s['user']} | {s['title']} | `{s['session_id']}` |")
        lines += ["", "| Turn | Delivery | Panels | Result file |", "|---|---|---|---|"]
        for t in sorted(manifest["turns"], key=lambda t: (t["scenario"], t["turn"])):
            lines.append(f"| Q{t['scenario']:02d}.{t['turn']} | {t['status']} | {', '.join(t.get('panels', [])) or '—'} | [{t['file']}]({t['file']}) |")
        (out / "RESULTS.md").write_text("\n".join(lines) + "\n")

    save()
    if args.prepare_only:
        print(json.dumps({"prepared": True, "scenarios": len(SCENARIOS), "turns": len(questions), "directory": str(out)}), flush=True)
        return
    timeout = httpx.Timeout(connect=15, read=600, write=30, pool=30)
    async with httpx.AsyncClient(base_url=args.base_url, timeout=timeout) as client:
        health_response = await client.get("/api/health")
        health_response.raise_for_status()
        health = health_response.json()
        if health.get("asset_count") != 600 or health.get("reference_date") != "2027-01-15" or health.get("dataset_namespace") != EXPECTED_NAMESPACE:
            manifest.update(status="blocked_dataset", observed_health={k: health.get(k) for k in ("asset_count", "reference_date", "dataset_namespace")})
            save()
            raise RuntimeError("Serving API is not wired to the final 600-well snapshot")
        if health.get("model") != args.expected_model:
            manifest.update(status="blocked_model", observed_model=health.get("model"))
            save()
            raise RuntimeError("The serving model does not match the user-selected evaluation model")
        manifest["model"] = health["model"]
        manifest["dataset_revision"] = health.get("provider", {}).get("dataset_revision")
        users_response = await client.get("/api/users")
        users_response.raise_for_status()
        users = {u["name"]: u["user_id"] for u in users_response.json()["users"]}
        required = {name for specs in cases.values() for _, name, _ in specs}
        if required - users.keys():
            raise RuntimeError("Final dataset profiles are missing: " + ", ".join(sorted(required - users.keys())))
        sessions = {}
        # Create all reviewable sessions before generation starts.
        for case, specs in cases.items():
            for _, name, key in specs:
                group = (case, name, key)
                if group in sessions:
                    continue
                sid = str(uuid.uuid4())
                suffix = "" if key == "main" else " · " + key
                title = f"{args.label} Q{case:02d} · {TITLES[case]}{suffix}"
                response = await client.post("/api/sessions", headers={"X-User-Id": users[name]}, json={"id": sid, "title": title})
                response.raise_for_status()
                sessions[group] = sid
                manifest["sessions"].append({"scenario": case, "user": name, "user_id": users[name], "title": title, "session_id": sid})
                save()
        manifest["status"] = "running"
        save()
        semaphore = asyncio.Semaphore(args.parallel)

        async def scenario(case):
            async with semaphore:
                for turn, (offset, name, key) in enumerate(SCENARIOS[case], 1):
                    sid, uid = sessions[(case, name, key)], users[name]
                    run_id, message_id = str(uuid.uuid4()), str(uuid.uuid4())
                    headers = {"X-User-Id": uid, "X-Session-Id": sid, "Accept": "text/event-stream"}
                    record = {"scenario": case, "turn": turn, "user": name, "user_id": uid,
                              "session_id": sid, "run_id": run_id, "message_id": message_id, "question": questions[offset], "started_at": now(), "status": "running"}
                    manifest["turns"].append(record)
                    record["file"] = f"Q{case:02d}-{turn:02d}.json"
                    save()
                    error = None
                    stages = []
                    try:
                        async with client.stream("POST", "/api/agent", headers=headers,
                                                 json={"threadId": sid, "runId": run_id, "message_id": message_id,
                                                       "message": questions[offset], "reference_date": "2027-01-15"}) as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if not line.startswith("data:"):
                                    continue
                                event = json.loads(line[5:].strip())
                                if event.get("type") == "RUN_ERROR":
                                    error = {"code": event.get("code"), "message": event.get("message")}
                                elif event.get("type") == "CUSTOM" and event.get("name") == "asset_progress":
                                    stages.append(event.get("value", {}))
                        history_response = await client.get(f"/api/sessions/{sid}/messages", headers=headers)
                        history_response.raise_for_status()
                        history = history_response.json()["messages"]
                        user_message = next((m for m in history if m.get("role") == "user" and (m.get("client_message_id") == message_id or m.get("run_id") == run_id)), None)
                        canonical = user_message.get("run_id", run_id) if user_message else run_id
                        assistant = next((m for m in reversed(history) if m.get("role") == "assistant" and m.get("run_id") == canonical), None)
                        answer = assistant.get("envelope") if assistant else None
                        record.update(answer_id=canonical, status=assistant.get("status", "error") if assistant else "error", error=error,
                                      panels=[b["type"] for b in (answer or {}).get("blocks", [])],
                                      narrative=(assistant or {}).get("content", ""), answer=answer,
                                      saved_user_message=bool(user_message), saved_assistant_message=bool(assistant))
                    except Exception as exc:
                        record.update(status="transport_error", error={"code": type(exc).__name__, "message": str(exc)[:300]})
                    record.update(finished_at=now(), stages=stages)
                    (out / record["file"]).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
                    # Keep the manifest small; full persisted envelope is in the per-turn file.
                    record.pop("answer", None)
                    record.pop("stages", None)
                    save()
                    print(f"Q{case:02d}.{turn} {record['status']} · {name} · {sid}", flush=True)

        async def recall_chain():
            if 8 in selected:
                await scenario(8)
            if 9 in selected:
                await scenario(9)

        chains = [scenario(q) for q in [1, 2, 3, 4, 5, 6, 7, 10, 11] if q in selected]
        if selected & {8, 9}:
            chains.append(recall_chain())
        await asyncio.gather(*chains)
        for saved in manifest["sessions"]:
            renamed = await client.patch("/api/sessions/" + saved["session_id"], headers={"X-User-Id": saved["user_id"]}, json={"title": saved["title"]})
            renamed.raise_for_status()
        manifest.update(status="finished", finished_at=now())
        save()
        print(str(out / "RESULTS.md"), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
