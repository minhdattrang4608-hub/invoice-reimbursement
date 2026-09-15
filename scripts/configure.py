#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path

from common import DATA_ROOT, ensure_dirs, load_json, profile_path, safe_name, save_json, set_secret


def validate(data: dict) -> list[str]:
    missing = []
    if not data.get("profile_name"): missing.append("profile_name")
    if not data.get("output_root"): missing.append("output_root")
    if not data.get("reimbursement_people") and not data.get("ask_person_each_batch"): missing.append("reimbursement_people")
    companies = data.get("companies") or []
    if not companies: missing.append("companies")
    for index, company in enumerate(companies):
        for key in ["id", "name", "tax_id", "template"]:
            if not company.get(key): missing.append(f"companies[{index}].{key}")
    if "monitoring" not in data: missing.append("monitoring")
    return missing


def next_action(data: dict | None) -> dict:
    if not data:
        return {"step": "email_provider", "prompt": "请选择邮箱：QQ / 163或126 / Gmail / Outlook / 企业邮箱 / 暂不绑定"}
    sources = data.get("collection_sources") or (["email"] if data.get("email_accounts") else [])
    if "email" in sources and not data.get("email_accounts"):
        return {"step": "email_address", "prompt": "请输入要收集发票的邮箱地址"}
    if "monitoring" not in data:
        return {"step": "monitoring", "prompt": "请选择定时扫描时间"}
    if not data.get("reimbursement_people") and not data.get("ask_person_each_batch"):
        return {"step": "reimbursement_person", "prompt": "请选择报销人设置：填写姓名 / 每次询问"}
    if not data.get("companies"):
        return {"step": "company", "prompt": "请上传一张公司抬头发票，或粘贴开票信息"}
    missing = validate(data)
    if missing:
        return {"step": "profile_details", "prompt": "继续补全报销配置", "missing": missing}
    return {"step": "complete", "prompt": "配置已完成，可以抓取并整理发票"}


def main() -> int:
    ensure_dirs()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    status = sub.add_parser("status"); status.add_argument("--profile", required=True)
    show = sub.add_parser("show"); show.add_argument("--profile", required=True)
    save = sub.add_parser("save"); save.add_argument("--profile", required=True); save.add_argument("--answers", required=True)
    secret = sub.add_parser("secret-set"); secret.add_argument("--profile", required=True); secret.add_argument("--account-id", required=True); secret.add_argument("--value")
    args = parser.parse_args()
    if args.cmd == "list":
        print(json.dumps([p.stem for p in sorted((DATA_ROOT / "profiles").glob("*.json"))], ensure_ascii=False)); return 0
    if args.cmd in {"status", "show"}:
        data = load_json(profile_path(args.profile))
        if not data:
            print(json.dumps({"exists": False, "complete": False, "missing": ["profile"], "next_action": next_action(None)}, ensure_ascii=False)); return 1
        if args.cmd == "show": print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            missing = validate(data); print(json.dumps({"exists": True, "complete": not missing, "missing": missing, "next_action": next_action(data)}, ensure_ascii=False))
        return 0 if not validate(data) else 1
    if args.cmd == "save":
        data = load_json(Path(args.answers))
        data["version"] = 2; data["profile_name"] = safe_name(args.profile)
        save_json(profile_path(args.profile), data)
        missing = validate(data)
        print(json.dumps({"saved": str(profile_path(args.profile)), "complete": not missing, "missing": missing, "next_action": next_action(data)}, ensure_ascii=False)); return 0
    value = args.value or getpass.getpass("Authorization code (not saved in profile JSON): ")
    set_secret(args.profile, args.account_id, value)
    print(json.dumps({"stored": True, "service": f"invoice-reimbursement:{safe_name(args.profile)}:{safe_name(args.account_id)}"})); return 0


if __name__ == "__main__": raise SystemExit(main())
