#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path

from common import DATA_ROOT, ensure_dirs, safe_name


PRESETS = {
    "daily-0900": {"Hour": 9, "Minute": 0},
    "daily-2200": {"Hour": 22, "Minute": 0},
    "every-6-hours": {"StartInterval": 21600},
    "weekly-mon-0900": {"Weekday": 2, "Hour": 9, "Minute": 0},
}


def schedule_value(preset: str, daily_time: str | None) -> dict:
    if daily_time:
        match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", daily_time)
        if not match:
            raise ValueError("--daily-time must use HH:MM in 24-hour local time")
        return {"Hour": int(match.group(1)), "Minute": int(match.group(2))}
    return PRESETS[preset]


def runtime_warning(python_executable: str) -> str | None:
    lowered = python_executable.lower()
    if any(token in lowered for token in ["/tmp/", "/temp/", "/work/", "/var/folders/"]):
        return "Python runtime appears temporary; use a persistent environment before installing the schedule"
    return None


def plist(profile: str, preset: str, daily_time: str | None, python_executable: str):
    label = f"io.agent.invoice-reimbursement.{safe_name(profile)}"
    script = Path(__file__).with_name("mail_fetch.py")
    logs = DATA_ROOT / "logs"
    timing = schedule_value(preset, daily_time)
    data = {
        "Label": label,
        "ProgramArguments": [python_executable, str(script), "fetch", "--profile", profile],
        "RunAtLoad": False,
        "StandardOutPath": str(logs / f"{safe_name(profile)}.out.log"),
        "StandardErrorPath": str(logs / f"{safe_name(profile)}.err.log"),
    }
    if "StartInterval" in timing:
        data.update(timing)
    else:
        data["StartCalendarInterval"] = timing
    return label, data


def main() -> int:
    ensure_dirs()
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["preview", "install", "status", "uninstall"])
    parser.add_argument("--profile", required=True)
    parser.add_argument("--preset", choices=PRESETS, default="daily-0900")
    parser.add_argument("--daily-time")
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        print(json.dumps({"supported": False, "reason": "Automatic scheduler installation is currently supported on macOS only"}))
        return 2
    python_executable = str(Path(args.python_executable).expanduser().resolve())
    label, data = plist(args.profile, args.preset, args.daily_time, python_executable)
    path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    warning = runtime_warning(python_executable)
    if args.command == "preview":
        print(json.dumps({"profile": args.profile, "local_schedule": schedule_value(args.preset, args.daily_time), "python": python_executable, "warning": warning, "plist": plistlib.dumps(data).decode()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps({"installed": path.exists(), "path": str(path), "python": python_executable, "warning": warning}, ensure_ascii=False))
        return 0
    if not args.confirm:
        raise SystemExit("Refusing scheduler change without --confirm")
    if args.command == "install":
        if warning:
            raise SystemExit(warning)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(data))
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)], capture_output=True)
        subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(path)], check=True)
        print(json.dumps({"installed": str(path), "python": python_executable}, ensure_ascii=False))
    else:
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)], capture_output=True)
        path.unlink(missing_ok=True)
        print(json.dumps({"removed": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
