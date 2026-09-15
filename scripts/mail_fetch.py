#!/usr/bin/env python3
from __future__ import annotations

import argparse, datetime as dt, email, imaplib, json, codecs
from email.header import decode_header
from pathlib import Path
from common import DATA_ROOT, PROVIDERS, SUPPORTED, ensure_dirs, get_secret, imap_utf7, infer_provider, load_json, profile_path, safe_name, save_json

def decode(value):
    out=[]
    for part, enc in decode_header(value or ""):
        if isinstance(part, bytes):
            encoding = enc or "utf-8"
            try:
                codecs.lookup(encoding)
            except (LookupError, TypeError):
                encoding = "utf-8"
            out.append(part.decode(encoding, "replace"))
        else:
            out.append(part)
    return "".join(out)


def account_settings(profile_name: str, account_id: str | None = None):
    profile = load_json(profile_path(profile_name))
    if not profile:
        raise RuntimeError("Profile not found")
    accounts = [a for a in profile.get("email_accounts", []) if a.get("enabled", True)]
    if account_id:
        accounts = [a for a in accounts if a.get("id") == account_id]
    if not accounts:
        raise RuntimeError("Email account not found or disabled")
    return profile, accounts


def connect(profile_name: str, account: dict):
    provider = account.get("provider") or infer_provider(account["address"])
    if provider == "auto":
        provider = infer_provider(account["address"])
    if provider == "outlook":
        raise RuntimeError("Outlook/Microsoft 365 requires OAuth. Use a supported Microsoft email connector or upload invoices; do not enter a login password or app password.")
    default = PROVIDERS.get(provider)
    host = default[0] if default else account.get("imap_host")
    port = default[1] if default else int(account.get("imap_port", 993))
    if not host:
        raise RuntimeError(f"Custom IMAP host missing for {account['id']}")
    secret = get_secret(profile_name, account["id"])
    if not secret:
        raise RuntimeError(f"Authorization code missing for {account['id']}")
    client = imaplib.IMAP4_SSL(host, port)
    client.login(account["address"], secret)
    # 163/126 邮箱要求客户端登录后发送 ID 命令，否则会话被判定为不安全登录（Unsafe Login）
    if provider in ("163", "126"):
        try:
            imaplib.Commands.setdefault("ID", ("NONAUTH", "AUTH", "SELECTED"))
            client._simple_command("ID", '("name" "invoice-reimbursement" "version" "1.0")')
        except Exception:
            pass
    status, _ = client.select(imap_utf7(account.get("folder", "INBOX")), readonly=True)
    if status != "OK":
        client.logout()
        raise RuntimeError("Cannot open mailbox folder")
    return client, provider, host


def test_connection(profile_name: str, account_id: str | None = None) -> dict:
    ensure_dirs()
    _, accounts = account_settings(profile_name, account_id)
    results = []
    for account in accounts:
        client = None
        try:
            client, provider, host = connect(profile_name, account)
            results.append({"account": account["id"], "ok": True, "provider": provider, "host": host, "readonly": True})
        finally:
            if client:
                try: client.logout()
                except Exception: pass
    return {"tested": len(results), "accounts": results}

def parse_since(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise RuntimeError("--since must use YYYY-MM-DD") from exc
    return parsed.strftime("%d-%b-%Y")


def fetch(profile_name: str, since: str | None = None, account_id: str | None = None) -> dict:
    ensure_dirs(); profile, accounts = account_settings(profile_name, account_id)
    since_imap = parse_since(since)
    total=0; results=[]
    for account in accounts:
        inbox = DATA_ROOT / "inbox" / safe_name(profile_name) / safe_name(account.get("company_id") or "unassigned"); inbox.mkdir(parents=True, exist_ok=True)
        state_path = DATA_ROOT / "state" / f"mail-{safe_name(profile_name)}-{safe_name(account['id'])}.json"
        state = load_json(state_path, {}) or {}; last_uid=int(state.get("last_uid", 0))
        client = None
        try:
            client, _, _ = connect(profile_name, account)
            criteria = []
            if last_uid:
                criteria.extend(["UID", f"{last_uid+1}:*"])
            if since_imap:
                criteria.extend(["SINCE", since_imap])
            if not criteria:
                criteria.append("ALL")
            status,data=client.uid("search",None,*criteria)
            if status != "OK": raise RuntimeError("IMAP search failed")
            for raw_uid in data[0].split():
                uid=int(raw_uid); status,parts=client.uid("fetch",str(uid),"(RFC822)")
                if status != "OK" or not parts or not isinstance(parts[0],tuple): continue
                msg=email.message_from_bytes(parts[0][1]); subject=decode(msg.get("Subject"))
                for part in msg.walk():
                    if part.get_content_disposition() != "attachment": continue
                    name=safe_name(decode(part.get_filename())); suffix=Path(name).suffix.lower()
                    if suffix not in SUPPORTED: continue
                    payload=part.get_payload(decode=True)
                    if not payload: continue
                    target=inbox/name
                    if target.exists(): target=inbox/f"{target.stem}-{uid}{target.suffix}"
                    target.write_bytes(payload); total+=1
                    save_json(target.with_suffix(target.suffix+".source.json"), {"uid":uid,"account":account["id"],"subject":subject,"from":decode(msg.get("From")),"date":decode(msg.get("Date"))})
                last_uid=max(last_uid,uid)
            save_json(state_path,{"last_uid":last_uid})
            results.append({"account":account["id"],"ok":True})
        finally:
            try:
                if client: client.logout()
            except Exception: pass
    return {"downloaded":total,"accounts":results,"since":since}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("command",choices=["fetch", "test"]); p.add_argument("--profile",required=True); p.add_argument("--account-id"); p.add_argument("--since",help="Only fetch messages on or after YYYY-MM-DD (IMAP internal date)"); a=p.parse_args()
    result = fetch(a.profile, a.since, a.account_id) if a.command == "fetch" else test_connection(a.profile, a.account_id)
    print(json.dumps(result,ensure_ascii=False,indent=2))
