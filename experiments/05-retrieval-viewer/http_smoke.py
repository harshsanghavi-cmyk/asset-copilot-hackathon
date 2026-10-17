"""In-process real-provider HTTP diagnostics smoke; no model/network/secret access."""
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from backend.retrieval import create_provider
from backend.retrieval.router import create_router

root = Path(__file__).resolve().parents[2]
provider = create_provider([root / "dataset/sample-data"], root / "backend/retrieval/.cache/dataset.sqlite")
def guard(token):
    if token != "synthetic-test-admin-capability":
        raise HTTPException(403, "Denied")
    return True

app = FastAPI()
app.include_router(create_router(provider, context_resolver={"admin": guard, "authority": lambda reference: {"knowledge_revision": 0}}), prefix="/api")
client = TestClient(app)
headers = {"X-Admin-Token": "synthetic-test-admin-capability"}
checks = []
for path in ["overview", "sources?limit=5", "chunks?limit=5", "enrichments?limit=5", "walkthrough?asset_id=WELL-0001"]:
    response = client.get("/api/retrieval/" + path, headers=headers)
    checks.append({"path": path, "status": response.status_code, "passed": response.status_code == 200, "returned_items": len(response.json().get("items", []))})
checks.append({"path": "overview without admin", "status": client.get("/api/retrieval/overview").status_code, "passed": client.get("/api/retrieval/overview").status_code == 403})
denied_app = FastAPI()
denied_app.include_router(create_router(provider, context_resolver={"admin": lambda token: False}), prefix="/api")
false_guard_status = TestClient(denied_app).get("/api/retrieval/overview").status_code
checks.append({"path": "explicit false admin guard", "status": false_guard_status, "passed": false_guard_status == 403})
response = client.post("/api/retrieval/query", headers=headers, json={"collection": "assets", "metric": "count"})
checks.append({"path": "typed assets count", "status": response.status_code, "passed": response.status_code == 200 and response.json()["rows"][0]["count"] == 200})
response = client.post("/api/retrieval/query", headers=headers, json={"sql": "SELECT * FROM users"})
checks.append({"path": "raw SQL rejection", "status": response.status_code, "passed": response.status_code == 422})
response = client.post("/api/retrieval/search", headers=headers, json={"terms": "find assets whose maintaince report has found crude oil on the pad", "kind": "report"})
body = response.json()
checks.append({"path": "actual user report-text search", "status": response.status_code, "passed": response.status_code == 200 and body["coverage"]["status"] == "ranked_subset" and bool(body["items"]) and all(r["kind"] == "report" and r["asset_id"] and r["excerpt"] for r in body["items"]), "coverage": body.get("coverage")})
output = {"kind": "in_process_real_provider_http_smoke", "not_live_model_quality": True, "passed": sum(c["passed"] for c in checks), "total": len(checks), "checks": checks, "counts": provider.overview()["counts"]}
(Path(__file__).parent / "http-smoke-results.json").write_text(json.dumps(output, indent=2))
print(json.dumps({"passed": output["passed"], "total": output["total"]}))
provider.close()
assert all(c["passed"] for c in checks)
