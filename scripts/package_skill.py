#!/usr/bin/env python3
"""把這個 repo 打包成 Claude 可以安裝的 skill 檔（mock-exam-workbook.skill）。

一般使用者不用執行：repo 根目錄已經放了打包好的 mock-exam-workbook.skill，直接下載安裝即可。
這個腳本是給維護的人用的：改了 SKILL.md、assets/、references/ 或 scripts/build.py 之後，
在 repo 的根目錄執行，重新產生 mock-exam-workbook.skill，和改動一起 commit。

用法：
  python3 scripts/package_skill.py               # 重新產生根目錄的 mock-exam-workbook.skill
  python3 scripts/package_skill.py --check       # 只檢查根目錄的 .skill 是否和目前的檔案一致
  python3 scripts/package_skill.py --out 路徑.skill

只放 skill 需要的檔案：SKILL.md、assets/、references/、scripts/build.py。
README、操作說明、PROMPT.md 這些給人看的文件不會打包進去。
.skill 其實就是 zip，裡面最上層是 mock-exam-workbook/ 資料夾。
檔案的時間戳記固定，內容沒變時重新打包會得到一模一樣的檔案。
"""
import argparse, io, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "mock-exam-workbook"
DEFAULT_OUT = ROOT / f"{NAME}.skill"
INCLUDE = ["SKILL.md", "assets", "references", "scripts/build.py"]
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def files():
    out = []
    for item in INCLUDE:
        p = ROOT / item
        if not p.exists():
            sys.exit(f"找不到 {item}，請在完整的 repo 裡執行。")
        out += sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p]
    return [f for f in out if f.name != ".DS_Store" and "__pycache__" not in f.parts]


def build(fs):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in fs:
            info = zipfile.ZipInfo(f"{NAME}/{f.relative_to(ROOT).as_posix()}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            # 統一成 LF 換行，Windows 上 git 轉成 CRLF 時打包結果也不會變
            data = f.read_bytes()
            if f.suffix in (".md", ".html", ".json", ".py", ".svg"):
                data = data.replace(b"\r\n", b"\n")
            z.writestr(info, data, compresslevel=9)
    return buf.getvalue()


def contents(blob):
    z = zipfile.ZipFile(io.BytesIO(blob))
    return {n: z.read(n) for n in z.namelist()}


def main():
    ap = argparse.ArgumentParser(description="打包 mock-exam-workbook skill")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="輸出的 .skill 檔（預設是 repo 根目錄的 mock-exam-workbook.skill）")
    ap.add_argument("--check", action="store_true", help="只檢查 --out 指到的 .skill 是否和目前的檔案一致，不寫檔")
    args = ap.parse_args()

    head = (ROOT / "SKILL.md").read_text(encoding="utf-8").split("---")
    m = re.search(r"^name:\s*(\S+)\s*$", head[1] if len(head) > 2 else "", re.M)
    if not m or m.group(1) != NAME:
        sys.exit(f"SKILL.md 開頭的 name 要是 {NAME}。")

    fs = files()
    blob = build(fs)
    out = Path(args.out)
    if args.check:
        if not out.exists():
            sys.exit(f"找不到 {out}，請先執行 python3 scripts/package_skill.py。")
        old, new = contents(out.read_bytes()), contents(blob)
        stale = sorted(n for n in set(old) | set(new) if old.get(n) != new.get(n))
        if stale:
            print(f"{out.name} 和目前的檔案不一致，請重新執行 python3 scripts/package_skill.py 再 commit：")
            for n in stale:
                print(f"  {n}")
            sys.exit(1)
        print(f"{out.name} 和目前的檔案一致。")
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    ver = re.search(r"引擎版本：(\d{4}-\d{2}-\d{2}[a-z]?)",(ROOT / "assets" / "template.html").read_text(encoding="utf-8"))
    print(f"已產生 {out}（{len(fs)} 個檔案，引擎版本 {ver.group(1) if ver else '未知'}）")
    for f in fs:
        print(f"  {NAME}/{f.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
