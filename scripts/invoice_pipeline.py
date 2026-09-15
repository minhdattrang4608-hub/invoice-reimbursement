#!/usr/bin/env python3
from __future__ import annotations

import argparse, copy, datetime as dt, json, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from common import DATA_ROOT, SUPPORTED, ensure_dirs, file_hash, load_json, normalize_company, profile_path, safe_name, save_json, SKILL_ROOT

def extract(path: Path) -> str:
    if path.suffix.lower() != ".pdf": return ""
    if shutil.which("pdftotext"):
        r=subprocess.run(["pdftotext","-layout",str(path),"-"],capture_output=True,text=True,timeout=120)
        if r.returncode==0 and len(re.sub(r"\s","",r.stdout))>50: return r.stdout
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    except Exception: return ""

def amount(text):
    compact=re.sub(r"[ \t]","",text)
    for pat in [r"价税合计.*?小写.*?[¥￥]?(-?[0-9][0-9,]*\.\d{2})",r"\(小写\).*?[¥￥]?(-?[0-9][0-9,]*\.\d{2})"]:
        m=re.search(pat,compact,re.S)
        if m:return float(m.group(1).replace(",",""))
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if "合计" in line:
            nums=re.findall(r"(?:CNY|[¥￥])\s*(-?[0-9][0-9,]*\.\d{2})"," ".join(lines[i:i+3]),re.I)
            if nums:return float(nums[-1].replace(",",""))
    return None

def date(text):
    m=re.search(r"开票\s*日期\s*[：:]\s*(20\d{2})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})",text)
    if not m:
        all_dates=re.findall(r"(20\d{2})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})",text); m=all_dates[-1] if all_dates else None
        return f"{int(m[0]):04d}-{int(m[1]):02d}-{int(m[2]):02d}" if m else ""
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

def invoice_no(text):
    compact=re.sub(r"[ \t]","",text); m=re.search(r"发票号码[：:]([0-9]{8,24})",compact)
    return m.group(1) if m else ""

def category(text,name):
    h=(text+name).lower()
    if any(x in h for x in ["航空运输电子客票","机票","民航发展基金","退票服务"]):return "机票"
    if any(x in h for x in ["客运服务费","出租车","滴滴","高德打车","旅客运输服务"]):return "打车"
    if any(x in h for x in ["住宿费","宾馆","酒店"]):return "住宿"
    if any(x in h for x in ["餐饮服务","餐费","餐饮管理"]):return "餐饮"
    return "其他"

def seller(text):
    for line in text.splitlines():
        line=re.sub(r"\s+"," ",line)
        m=re.search(r"(?:销|售)\s*名称\s*[：:]\s*(.+)$",line)
        if m:return re.split(r"\s{2,}|统一社会信用代码",m.group(1))[0].strip()
    return ""

def unpack_zips(root:Path):
    for z in list(root.rglob("*.zip")):
        out=DATA_ROOT/"state"/"unzipped"/file_hash(z)[:12]; out.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(z) as arc:
            for item in arc.infolist():
                name=safe_name(Path(item.filename).name)
                if item.is_dir() or Path(name).suffix.lower() not in SUPPORTED-{".zip"}:continue
                target=out/name
                with arc.open(item) as src,target.open("wb") as dst:shutil.copyfileobj(src,dst)
        yield from out.iterdir()

def scan(args):
    ensure_dirs(); profile=load_json(profile_path(args.profile)); company=next(c for c in profile["companies"] if c["id"]==args.company)
    inbox=Path(args.input).expanduser() if args.input else DATA_ROOT/"inbox"/safe_name(args.profile)/safe_name(args.company)
    files=[p for p in inbox.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED-{".zip"}]+list(unpack_zips(inbox))
    items=[]; seen_h=set(); seen_n=set()
    for p in sorted(files):
        text=extract(p); num=invoice_no(text); total=amount(text); cat=category(text,p.name); tax=company.get("tax_id","")
        issues=[]; pdf=p.suffix.lower()==".pdf"; buyer_ok=normalize_company(company["name"]) in normalize_company(text) if text else False
        if not pdf and profile.get("rules",{}).get("require_original_pdf",True):issues.append("缺少原始PDF")
        if not text:issues.append("需Agent直接查看原文件识别")
        if not num:issues.append("未识别发票号码")
        if total is None:issues.append("未识别价税合计")
        if text and not buyer_ok:issues.append("购买方名称不匹配或未识别")
        if text and tax and tax not in text:issues.append("购买方税号不匹配或未识别")
        h=file_hash(p); duplicate=h in seen_h or bool(num and num in seen_n)
        if duplicate:issues.append("重复发票或文件")
        red="红字发票" in text or "负数" in text or (total is not None and total<0)
        if red:issues.append("红字或负数发票需匹配蓝票")
        desc=(seller(text) or cat)+(("｜开票日 "+date(text)) if date(text) else "")
        if cat in {"机票","打车","餐饮"}:desc=f"{cat}｜{desc}"
        items.append({"source_path":str(p.resolve()),"source_name":p.name,"source_type":p.suffix.lower().lstrip("."),"sha256":h,"invoice_no":num,"invoice_date":date(text),"seller":seller(text),"buyer_name":company["name"] if buyer_ok else "","buyer_tax_id":tax if text and tax in text else "","category":cat,"amount":total or 0,"description":desc,"is_red":red,"include":bool(pdf and num and total is not None and buyer_ok and not duplicate),"issues":issues})
        seen_h.add(h); seen_n.add(num)
    batch=DATA_ROOT/"batches"/safe_name(args.profile)/f"{dt.datetime.now():%Y%m%d-%H%M%S}-{safe_name(args.project)}"; batch.mkdir(parents=True,exist_ok=True)
    manifest={"version":1,"profile":args.profile,"project":args.project,"person":args.person,"company_id":args.company,"company":company,"output_root":profile["output_root"],"rules":profile.get("rules",{}),"invoices":items}
    path=batch/"manifest.json"; save_json(path,manifest); print(json.dumps({"manifest":str(path),"files":len(items),"needs_review":sum(bool(x["issues"]) for x in items)},ensure_ascii=False)); return path

def fill_excel(manifest, output: Path, include_audit_materials: bool = False):
    try: from openpyxl import load_workbook
    except Exception as exc: raise RuntimeError("openpyxl is required or use the host spreadsheet tool") from exc
    cfg=manifest["company"].get("template",{}); source=Path(cfg.get("path") or SKILL_ROOT/"assets"/"generic-reimbursement.xlsx")
    wb=load_workbook(source); ws=wb[cfg.get("sheet") or wb.sheetnames[0]]; start=int(cfg.get("start_row",3)); cols=cfg.get("columns",{"category":"A","description":"B","unit_price":"C","unit":"D","quantity":"E","total":"F","has_invoice":"G","file_name":"H"})
    included=[x for x in manifest["invoices"] if x.get("include")]
    if cfg.get("title_cell"):ws[cfg["title_cell"]]=f"{manifest['person']} {manifest['project']} 报销表"
    for i,item in enumerate(included,start):
        if i>start:
            for cell in ws[start]:
                ws.cell(i,cell.column)._style=copy.copy(cell._style); ws.cell(i,cell.column).number_format=cell.number_format
        values={"category":item["category"],"description":item["description"],"unit_price":item["amount"],"unit":"张","quantity":1,"total":item["amount"],"has_invoice":"是" if item["source_type"]=="pdf" else "否","file_name":item.get("archived_name",item["source_name"])}
        for key,col in cols.items():ws[f"{col}{i}"]=values.get(key,"")
    total_row=start+len(included); col=cfg.get("total_column",cols.get("total","F")); ws[f"{col}{total_row}"]=f"=SUM({col}{start}:{col}{total_row-1})" if included else 0
    if include_audit_materials:
        if "核对报告" in wb.sheetnames: checks=wb["核对报告"]
        else: checks=wb.create_sheet("核对报告")
        checks.delete_rows(1,checks.max_row); checks.append(["文件","问题","是否计入","金额"])
        for x in manifest["invoices"]:
            if x["issues"]: checks.append([x["source_name"],"；".join(x["issues"]),"是" if x["include"] else "否",x["amount"]])
    elif "核对报告" in wb.sheetnames and (cfg.get("mode") == "generic" or not cfg.get("path")):
        del wb["核对报告"]
    wb.save(output)

def unique_delivery_root(base: Path) -> Path:
    if not base.exists() or not any(base.iterdir()):
        return base
    index = 2
    while True:
        candidate = base.with_name(f"{base.name}-{index}")
        if not candidate.exists():
            return candidate
        index += 1


def package(args):
    m=load_json(Path(args.manifest)); requested=Path(m["output_root"]).expanduser()/safe_name(f"{m['person']} {m['project']} {m['company']['name']}报销"); root=unique_delivery_root(requested); inv=root/"发票"; inv.mkdir(parents=True,exist_ok=True)
    pending = root / "待补原始PDF"
    if args.include_audit_materials: pending.mkdir(parents=True, exist_ok=True)
    used=set()
    for x in m["invoices"]:
        if not x.get("include") and not args.include_audit_materials:
            continue
        src=Path(x["source_path"]); name=safe_name(f"{x['description']}｜{abs(float(x['amount'])):.2f}元｜{x['invoice_no'] or x['sha256'][:8]}")+src.suffix.lower(); n=2; base=name
        while name in used:name=f"{Path(base).stem}-{n}{Path(base).suffix}";n+=1
        used.add(name);x["archived_name"]=name
        if src.exists():
            target = inv if x.get("include") else pending
            shutil.copy2(src,target/name)
    if args.include_audit_materials: save_json(root/"发票台账.json",m)
    workbook = root/f"{safe_name(m['person']+' '+m['project'])} 报销.xlsx"
    fill_excel(m,workbook,args.include_audit_materials)
    print(json.dumps({"output":str(root),"default_items":[workbook.name,"发票"],"audit_materials":args.include_audit_materials},ensure_ascii=False))

if __name__=="__main__":
    p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True);a=s.add_parser("scan");a.add_argument("--profile",required=True);a.add_argument("--company",required=True);a.add_argument("--project",required=True);a.add_argument("--person",required=True);a.add_argument("--input");b=s.add_parser("package");b.add_argument("--manifest",required=True);b.add_argument("--include-audit-materials",action="store_true");args=p.parse_args();scan(args) if args.cmd=="scan" else package(args)
