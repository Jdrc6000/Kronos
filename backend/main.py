import json, os, sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from password_manager import PasswordManager

VAULT_FILE = Path(os.getenv("KRONOS_VAULT_FILE", "vault.json"))
FRONTEND_DIR = Path(os.getenv("KRONOS_FRONTEND_DIR", Path(__file__).resolve().parent.parent / "frontend"))

app = FastAPI(title="Kronos", docs_url="/docs")
pm = PasswordManager()

@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail=f"Frontend not found at {index.resolve()}")
    return FileResponse(index)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

class UnlockPayload(BaseModel):
    password: str

@app.post("/unlock")
def unlock(payload: UnlockPayload) -> dict:
    if not VAULT_FILE.exists():
        raise HTTPException(status_code=404, detail="No vault found. Create one first.")
    try:
        raw = json.loads(VAULT_FILE.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail="Failed to read vault.") from exc

    data = pm.decrypt_vault(payload.password, raw)
    if data is None:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    return {"vault": data}

class SavePayload(BaseModel):
    password: str
    vault: dict

@app.put("/save", status_code=204)
def save(payload: SavePayload) -> Response:
    try:
        encrypted = pm.encrypt_vault(payload.password, payload.vault)
        tmp = VAULT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(encrypted))
        tmp.replace(VAULT_FILE)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to write vault.") from exc
    
    return Response(status_code=204)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")