#!/usr/bin/env python3
import json, shutil, sys
from common import DATA_ROOT, ensure_dirs

ensure_dirs()
checks = {
    "python": sys.version.split()[0],
    "data_root": str(DATA_ROOT),
    "pdftotext": bool(shutil.which("pdftotext")),
    "openpyxl": False,
    "pypdf": False,
    "platform": sys.platform,
    "credential_store": bool(shutil.which("security")) if sys.platform == "darwin" else False,
}
for module in ["openpyxl", "pypdf"]:
    try: __import__(module); checks[module] = True
    except Exception: pass
if not checks["credential_store"]:
    try:
        __import__("keyring")
        checks["credential_store"] = True
    except Exception:
        pass
checks["onboarding_ready"] = True
checks["email_ready"] = checks["credential_store"]
checks["package_ready"] = checks["openpyxl"] and (checks["pdftotext"] or checks["pypdf"])
checks["ready"] = checks["package_ready"]
print(json.dumps(checks, ensure_ascii=False, indent=2))
