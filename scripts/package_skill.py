#!/usr/bin/env python3
"""把這個 repo 打包成 Claude 可以安裝的 skill 檔（mock-exam-workbook.skill）。

用法（在 repo 的根目錄執行）：
  python3 scripts/package_skill.py               # 產生 dist/mock-exam-workbook.skill
  python3 scripts/package_skill.py --out 路徑.skill

只放 skill 需要的檔案：SKILL.md、assets/、references/、scripts/build.py。
README、操作說明、PROMPT.md 這些給人看的文件不會打包進去。
.skill 其實就是 zip，裡面最上層是 mock-exam-workbook/ 資料夾。
"""
import argparse, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "mock-exam-workbook"
INCLUDE = ["SKILL.md", "assets", "references", "scripts/build.py"]


def files():
    out = []
    for item in INCLUDE:
        p = ROOT / item
        if not p.exists():
            sys.exit(f"找不到 {item}，請在完整的 repo 裡執行。")
        out += sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p]
    return [f for f in out if f.name != ".DS_Store" and "__pycache__" not in f.parts]


def main():
    ap = argparse.ArgumentParser(description="打包 mock-exam-workbook skill")
    ap.add_argument("--out", default=str(ROOT / "dist" / f"{NAME}.skill"), help="輸出的 .skill 檔")
    args = ap.parse_args()

    head = (ROOT / "SKILL.md").read_text(encoding="utf-8").split("---")
    m = re.search(r"^name:\s*(\S+)\s*$", head[1] if len(head) > 2 else "", re.M)
    if not m or m.group(1) != NAME:
        sys.exit(f"SKILL.md 開頭的 name 要是 {NAME}。")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fs = files()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in fs:
            z.write(f, f"{NAME}/{f.relative_to(ROOT).as_posix()}")
    ver = re.search(r"引擎版本：(\d{4}-\d{2}-\d{2})", (ROOT / "assets" / "template.html").read_text(encoding="utf-8"))
    print(f"已產生 {out}（{len(fs)} 個檔案，引擎版本 {ver.group(1) if ver else '未知'}）")
    for f in fs:
        print(f"  {NAME}/{f.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
