#!/usr/bin/env python3
"""檢查這份 skill 的範本是不是最新版：比對 assets/template.html 的引擎版本和 GitHub 上 main 的版本。

用 skill 出題或修改練習簿之前先執行一次（SKILL.md 的步驟 0）。只讀網路、不改任何檔案。

用法：
  python3 scripts/check_update.py                # 和 GitHub 的 main 比
  python3 scripts/check_update.py --branch dev   # 給維護的人：和 dev 比

輸出第一行是「狀態：…」，可能是：
  已是最新版／比 GitHub 上的版本新／有新版／無法檢查
不管結果如何都以 0 結束，連不到 GitHub 時也不會擋住後面的工作。

GitHub 上的版本先讀 repo 根目錄的 VERSION；那個分支還沒有 VERSION 時，改讀範本最上方說明的引擎版本。
引擎版本的寫法是日期加上可有可無的一個小寫字母（例如 2026-10-20、2026-10-20b），直接比字串就能排先後。
"""
import argparse, re, sys, urllib.error, urllib.request
from pathlib import Path

REPO = "HelloNiHowMa/Mock-Exam"
RAW = "https://raw.githubusercontent.com/" + REPO + "/{branch}/{path}"
DOWNLOAD = "https://github.com/" + REPO + "/raw/main/mock-exam-workbook.skill"
COMMITS = "https://github.com/" + REPO + "/commits/{branch}"
VER_RE = re.compile(r"\d{4}-\d{2}-\d{2}[a-z]?")
HEAD_RE = re.compile(r"引擎版本：(\d{4}-\d{2}-\d{2}[a-z]?)")
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"


def local_version():
    try:
        m = HEAD_RE.search(TEMPLATE.read_text(encoding="utf-8")[:20000])
    except OSError:
        return None
    return m.group(1) if m else None


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "mock-exam-workbook-check", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def remote_version(branch, timeout):
    """回傳 (版本, None) 或 (None, 連不到的原因)。"""
    try:
        text = fetch(RAW.format(branch=branch, path="VERSION"), timeout).strip()
        if VER_RE.fullmatch(text):
            return text, None
        reason = "VERSION 的內容不是引擎版本"
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return None, f"GitHub 回應 HTTP {e.code}"
        reason = None   # 這個分支還沒有 VERSION，改讀範本
    except Exception as e:
        return None, f"連不到 GitHub（{type(e).__name__}）"
    try:
        m = HEAD_RE.search(fetch(RAW.format(branch=branch, path="assets/template.html"), timeout)[:20000])
    except urllib.error.HTTPError as e:
        return None, f"GitHub 回應 HTTP {e.code}"
    except Exception as e:
        return None, f"連不到 GitHub（{type(e).__name__}）"
    if m:
        return m.group(1), None
    return None, reason or "GitHub 上的範本沒有寫引擎版本"


def main():
    ap = argparse.ArgumentParser(description="檢查 skill 的範本是不是 GitHub 上的最新版")
    ap.add_argument("--branch", default="main", help="要比對的分支（預設 main，一般使用者拿到的就是 main）")
    ap.add_argument("--timeout", type=float, default=10, help="每次連線最多等幾秒（預設 10）")
    args = ap.parse_args()

    mine = local_version()
    if not mine:
        print("狀態：無法檢查")
        print(f"找不到 {TEMPLATE} 的引擎版本，這份 skill 可能不完整，或是很舊的版本。")
        print(f"建議請使用者重新下載安裝：{DOWNLOAD}")
        return
    theirs, why = remote_version(args.branch, args.timeout)
    where = f"GitHub 的 {args.branch}"
    if not theirs:
        print("狀態：無法檢查")
        print(f"{why}，沒辦法確認是不是最新版。安裝的範本是引擎版本 {mine}。")
        return
    if mine == theirs:
        print("狀態：已是最新版")
        print(f"安裝的範本是引擎版本 {mine}，和 {where} 相同。")
    elif mine > theirs:
        print("狀態：比 GitHub 上的版本新")
        print(f"安裝的範本是引擎版本 {mine}，{where} 是 {theirs}。這是還沒合併的開發版本，不用更新。")
    else:
        print("狀態：有新版")
        print(f"安裝的範本是引擎版本 {mine}，{where} 已經是 {theirs}。")
        if args.branch == "main":
            print(f"重新下載安裝 skill 之後，新做或重新產生的練習簿才會用到新版：{DOWNLOAD}")
        print(f"改了什麼：{COMMITS.format(branch=args.branch)}")


if __name__ == "__main__":
    main()
