"""Explicit local developer launch; generates a local diagnostic capability file."""
from pathlib import Path
import os
import secrets
import uvicorn

root = Path(__file__).resolve().parents[1]
runtime = Path(os.environ.get("ASSET_RUNTIME_DIR", root / "runtime"))
runtime.mkdir(exist_ok=True, parents=True)
token_file = runtime / "admin-token"
if not token_file.exists():
    token_file.write_text(secrets.token_urlsafe(32))
    token_file.chmod(0o600)
os.environ.setdefault("ASSET_ADMIN_ENABLED", "1")
os.environ.setdefault("ASSET_ADMIN_TOKEN_FILE", str(token_file))
uvicorn.run("backend.app:get_app", factory=True, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
