from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("INVOICE_REIMBURSEMENT_HOME", Path.home() / ".invoice-reimbursement")).expanduser()
SUPPORTED = {".pdf", ".ofd", ".png", ".jpg", ".jpeg", ".heic", ".webp", ".zip"}

PROVIDERS = {
    "qq": ("imap.qq.com", 993),
    "163": ("imap.163.com", 993),
    "126": ("imap.126.com", 993),
    "gmail": ("imap.gmail.com", 993),
    "outlook": ("outlook.office365.com", 993),
}


def ensure_dirs() -> None:
    for name in ["profiles", "inbox", "batches", "templates", "state", "logs", "output"]:
        (DATA_ROOT / name).mkdir(parents=True, exist_ok=True)


def profile_path(name: str) -> Path:
    return DATA_ROOT / "profiles" / f"{safe_name(name)}.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def safe_name(value: str, max_len: int = 120) -> str:
    value = unicodedata.normalize("NFKC", str(value))
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" ._")
    return (value or "default")[:max_len]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_company(value: str) -> str:
    return re.sub(r"[\s()（）]", "", unicodedata.normalize("NFKC", value)).lower()


def infer_provider(address: str) -> str:
    domain = address.lower().split("@")[-1]
    if domain in {"qq.com", "foxmail.com"}: return "qq"
    if domain == "163.com": return "163"
    if domain == "126.com": return "126"
    if domain in {"gmail.com", "googlemail.com"}: return "gmail"
    if domain in {"outlook.com", "hotmail.com", "live.com"}: return "outlook"
    return "custom"


def imap_utf7(value: str) -> str:
    result, buffer = [], []
    def flush() -> None:
        if buffer:
            raw = "".join(buffer).encode("utf-16-be")
            result.append("&" + base64.b64encode(raw).decode().rstrip("=").replace("/", ",") + "-")
            buffer.clear()
    for char in value:
        if 0x20 <= ord(char) <= 0x7E:
            flush(); result.append("&-" if char == "&" else char)
        else:
            buffer.append(char)
    flush()
    return "".join(result)


def secret_service(profile: str, account_id: str) -> str:
    return f"invoice-reimbursement:{safe_name(profile)}:{safe_name(account_id)}"


def set_secret(profile: str, account_id: str, secret: str) -> None:
    service = secret_service(profile, account_id)
    if sys.platform == "darwin" and shutil.which("security"):
        subprocess.run(["security", "add-generic-password", "-U", "-a", "authorization-code", "-s", service, "-w", secret], check=True, capture_output=True)
        return
    try:
        import keyring
        keyring.set_password(service, "authorization-code", secret)
        return
    except Exception as exc:
        raise RuntimeError("No supported credential store. Set INVOICE_REIMBURSEMENT_AUTH_CODE only for the current run.") from exc


def get_secret(profile: str, account_id: str) -> str | None:
    env = os.environ.get("INVOICE_REIMBURSEMENT_AUTH_CODE")
    if env: return env
    service = secret_service(profile, account_id)
    if sys.platform == "darwin" and shutil.which("security"):
        result = subprocess.run(["security", "find-generic-password", "-a", "authorization-code", "-s", service, "-w"], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    try:
        import keyring
        return keyring.get_password(service, "authorization-code")
    except Exception:
        return None
