#!/usr/bin/env python3
"""把題庫 JSON（和圖片）塞進練習簿範本，產生一個可以直接開啟的 HTML。

用法：
  python build.py --bank bank.json --out 練習簿.html [--images 圖片資料夾]
  python build.py --bank bank.json --check          # 只檢查格式與品質，不產生檔案
  python build.py --extract 舊練習簿.html --dump 資料夾 # 從現有練習簿取出 bank.json 和 images.json
  python build.py --bank 資料夾/bank.json --images-json 資料夾/images.json --out 新版.html

檢查分兩級：
  錯誤：格式不符，頁面會把那一題排除。有錯誤時預設不產生檔案（加 --force 仍然產生）。
  提醒：格式沒問題，但可能影響出題品質（例如正確答案老是放在同一個位置）。
"""
import argparse, base64, io, json, mimetypes, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "template.html"
TYPES = ("mcq", "multi", "cls", "order", "match")
TYPE_ZH = {"mcq": "單選", "multi": "複選", "cls": "分類", "order": "排序", "match": "配對"}


def s(x):
    return isinstance(x, str) and x.strip() != ""


def dup(arr):
    seen = set()
    for v in arr:
        k = str(v).strip().lower()
        if k in seen:
            return v
        seen.add(k)
    return None


def void_fields(r):
    """不可作答的兩個欄位：回傳 (錯誤訊息或 None, 是否缺 voidNote)。和頁面引擎的檢查一致。"""
    if "void" in r and not isinstance(r["void"], bool):
        return "void 要是 true 或 false（不加引號）。", False
    if "voidNote" in r and not isinstance(r["voidNote"], str):
        return "voidNote 要是文字。", False
    return None, r.get("void") is True and not s(r.get("voidNote"))


VOID_NO_NOTE = "標成不可作答（void），但沒有用 voidNote 說明這題哪裡有問題。"


def validate(bank, image_keys):
    """回傳 (錯誤, 提醒, 不可作答的題數)。不可作答只算格式正確、會出現在頁面上的題目和縮寫題。"""
    errors, notes = [], []
    if not isinstance(bank, dict):
        return ["題庫要是一個 { } 物件。"], notes, 0
    cfg = bank.get("config")
    if not isinstance(cfg, dict):
        errors.append("缺少 config 設定。")
        cfg = {}
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,39}", str(cfg.get("id", ""))):
        errors.append('config.id 要用 2 到 40 個小寫英文、數字或連字號，例如 "fw-upgrade-101"。')
    if not s(cfg.get("title")):
        errors.append("config.title（練習簿標題）不能空白。")
    for k in ("aiRole", "aiBasis", "abbrScope"):
        if not s(cfg.get(k)):
            notes.append(f"config.{k} 沒有填，AI 解析會用通用的說法。")

    qs = bank.get("questions")
    if not isinstance(qs, list):
        errors.append("題庫缺少 questions 陣列。")
        qs = []
    seen, valid = set(), []
    for idx, q in enumerate(qs):
        where = f"第 {q['n']} 題" if isinstance(q, dict) and isinstance(q.get("n"), int) else f"questions 裡的第 {idx + 1} 筆"

        def bad(msg):
            errors.append(f"{where}：{msg}")

        if not isinstance(q, dict):
            bad("要是一個 { } 物件。"); continue
        t = q.get("type", "mcq")
        if t not in TYPES:
            bad(f"type「{t}」不認得，只能是 {'、'.join(TYPES)}（縮寫題放在 abbr）。"); continue
        n = q.get("n")
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 9998 or n == 1000:
            bad("n 要是 1 到 999（題庫）或 1001 到 9998（頁面內建的補充題）的整數。"); continue
        if n in seen:
            bad("n 重複了。"); continue
        if t in ("mcq", "multi", "cls") and not s(q.get("q")):
            bad("缺少題目文字 q。"); continue
        if "q" in q and not isinstance(q["q"], str):
            bad("q 要是文字。"); continue
        if "e" in q and not isinstance(q["e"], str):
            bad("解析 e 要是文字。"); continue
        if not s(q.get("e")):
            notes.append(f"{where}：沒有解析 e。")
        img_bad = False
        for f in ("img", "eimg"):
            if f in q:
                if not (isinstance(q[f], list) and all(s(x) for x in q[f])):
                    bad(f'{f} 要是圖片代號的陣列，例如 ["topo1"]。'); img_bad = True; break
                miss = [x for x in q[f] if x not in image_keys]
                if miss:
                    errors.append(f"{where}：{f} 用到的圖片 {'、'.join(miss)} 找不到（圖片檔名去掉副檔名就是代號）。")
        if img_bad:
            continue
        # 不可作答只是多一個狀態，題目原本的欄位下面照常檢查
        verr, no_note = void_fields(q)
        if verr:
            bad(verr); continue
        if no_note:
            notes.append(f"{where}：{VOID_NO_NOTE}")
        if t in ("mcq", "multi"):
            o = q.get("o")
            if not (isinstance(o, list) and 2 <= len(o) <= 6 and all(s(x) for x in o)):
                bad("選項 o 要是 2 到 6 個非空白的文字。"); continue
            d = dup(o)
            if d is not None:
                bad(f"選項「{d}」重複了。"); continue
            a = q.get("a")
            if t == "mcq":
                if not isinstance(a, int) or isinstance(a, bool) or not 0 <= a < len(o):
                    bad(f"單選題的答案 a 要是 0 到 {len(o) - 1} 的整數（0 代表第一個選項）。"); continue
            else:
                if not (isinstance(a, list) and a and all(isinstance(i, int) and 0 <= i < len(o) for i in a)):
                    bad(f"複選題的答案 a 要是陣列，例如 [0, 2]，數字介於 0 到 {len(o) - 1}。"); continue
                if len(set(a)) != len(a):
                    bad("答案 a 裡有重複的數字。"); continue
        elif t == "cls":
            items = q.get("items")
            if not (isinstance(items, list) and len(items) >= 2 and all(s(x) for x in items)):
                bad("分類題的 items 要是至少 2 個非空白的文字。"); continue
            d = dup(items)
            if d is not None:
                bad(f"項目「{d}」重複了。"); continue
            groups = q.get("groups")
            if not (isinstance(groups, list) and groups):
                bad("分類題要有 groups，至少一組。"); continue
            used, ok = set(), True
            for gi, g in enumerate(groups, 1):
                if not (isinstance(g, dict) and isinstance(g.get("t", ""), str) and isinstance(g.get("s"), list) and g["s"]):
                    bad(f'groups 第 {gi} 組要有標題 t 和至少一格 s，例如 {{"t": "控制面", "s": [{{"a": 0}}]}}。'); ok = False; break
                for sl in g["s"]:
                    if not (isinstance(sl, dict) and isinstance(sl.get("a"), int) and 0 <= sl["a"] < len(items)):
                        bad(f"groups 第 {gi} 組有一格的 a 不是 0 到 {len(items) - 1} 的整數。"); ok = False; break
                    if "l" in sl and not isinstance(sl["l"], str):
                        bad(f"groups 第 {gi} 組有一格的標籤 l 不是文字。"); ok = False; break
                    if sl["a"] in used:
                        bad(f"項目「{items[sl['a']]}」被放進兩個格子。"); ok = False; break
                    used.add(sl["a"])
                if not ok:
                    break
            if not ok:
                continue
            unused = len(items) - len(used)
            if unused and not re.search(r"用不到|不需要|多餘", q["q"]):
                notes.append(f"{where}：有 {unused} 個項目用不到，建議在題目註明「有 {unused} 個項目用不到」。")
        elif t == "order":
            items = q.get("items")
            if not (isinstance(items, list) and len(items) >= 2 and all(s(x) for x in items)):
                bad("排序題的 items 要是至少 2 個非空白的文字，照正確順序寫。"); continue
            d = dup(items)
            if d is not None:
                bad(f"項目「{d}」重複了。"); continue
        elif t == "match":
            pairs = q.get("pairs")
            if not (isinstance(pairs, list) and len(pairs) >= 2 and all(isinstance(p, list) and len(p) == 2 and s(p[0]) and s(p[1]) for p in pairs)):
                bad("配對題的 pairs 要是至少 2 組 [左, 右]，兩邊都要有文字。"); continue
            d = dup([p[0] for p in pairs]) or dup([p[1] for p in pairs])
            if d is not None:
                bad(f"「{d}」重複了，配對會無法判定。"); continue
        seen.add(n)
        valid.append(q)

    ab = bank.get("abbr", [])
    if not isinstance(ab, list):
        errors.append("abbr 要是陣列。"); ab = []
    seen_ab, void_ab = set(), []
    for i, r in enumerate(ab, 1):
        if isinstance(r, list):
            r = {"cat": r[0] if len(r) > 0 else "", "abbr": r[1] if len(r) > 1 else "", "full": r[2] if len(r) > 2 else "", "alts": r[3] if len(r) > 3 else [], "e": r[4] if len(r) > 4 else ""}
        if not (isinstance(r, dict) and s(r.get("abbr")) and s(r.get("full"))):
            errors.append(f"縮寫題第 {i} 筆：要有縮寫 abbr 和英文全名 full。"); continue
        k = r["abbr"].strip().lower()
        if k in seen_ab:
            errors.append(f"縮寫題第 {i} 筆（{r['abbr']}）：縮寫重複了。"); continue
        if "alts" in r and not (isinstance(r["alts"], list) and all(isinstance(x, str) for x in r["alts"])):
            errors.append(f"縮寫題第 {i} 筆（{r['abbr']}）：alts 要是文字陣列。"); continue
        verr, no_note = void_fields(r)
        if verr:
            errors.append(f"縮寫題第 {i} 筆（{r['abbr']}）：{verr}"); continue
        if no_note:
            notes.append(f"縮寫題第 {i} 筆（{r['abbr']}）：{VOID_NO_NOTE}")
        if r.get("void") is True:
            void_ab.append(r["abbr"].strip())
        seen_ab.add(k)

    gs = bank.get("groups", [])
    if not isinstance(gs, list):
        errors.append("groups 要是陣列。"); gs = []
    vn = {q["n"] for q in valid}
    void_n = sorted(q["n"] for q in valid if q.get("void") is True)
    for i, g in enumerate(gs, 1):
        if not (isinstance(g, dict) and s(g.get("name")) and isinstance(g.get("qs"), list)):
            errors.append(f"易混淆組第 {i} 組：要有名稱 name 和題號陣列 qs。"); continue
        miss = [x for x in g["qs"] if x not in vn]
        if miss:
            errors.append(f"易混淆組第 {i} 組（{g['name']}）：題號 {'、'.join(map(str, miss))} 不存在或有錯。")
        if len([x for x in g["qs"] if x in vn]) < 2:
            errors.append(f"易混淆組第 {i} 組（{g['name']}）：至少要有兩題有效的題目。")
        elif len([x for x in g["qs"] if x in vn and x not in void_n]) < 2:
            notes.append(f"易混淆組第 {i} 組（{g['name']}）：扣掉不可作答的題目後不到兩題，這一組不會出現在練習裡。")
    if void_n or void_ab:
        which = ([f"第 {'、'.join(map(str, void_n))} 題"] if void_n else []) + ([f"縮寫題 {'、'.join(void_ab)}"] if void_ab else [])
        notes.append(f"有 {len(void_n) + len(void_ab)} 題標成不可作答（{'，'.join(which)}）：這些題目不計入題數，也不會出題；拿掉 void 就會恢復，原本的作答紀錄都還在。")
    if not valid and not ab:
        errors.append("題庫裡沒有任何有效的題目。")
    return errors, notes + quality(valid), len(void_n) + len(void_ab)


def quality(qs):
    """不影響格式、但會影響出題品質的提醒。"""
    out = []
    # 練習時選項順序會自動打亂，所以不檢查答案位置；但「正確答案最長」這個線索打亂也還在。
    mcq = [q for q in qs if q.get("type", "mcq") == "mcq"]
    longest = [q for q in mcq if len(q["o"][q["a"]]) > max(len(x) for i, x in enumerate(q["o"]) if i != q["a"]) * 1.25]
    if len(mcq) >= 6 and len(longest) / len(mcq) > 0.5:
        out.append(f"品質：{len(longest)}/{len(mcq)} 題單選題的正確答案明顯是最長的選項，學員會挑最長的猜。請把干擾選項寫得一樣具體。")
    for q in qs:
        t = q.get("type", "mcq")
        where = f"第 {q['n']} 題"
        if t in ("mcq", "multi") and any(re.search(r"以上皆(是|非)|皆是|皆非|all of the above|none of the above", x, re.I) for x in q["o"]):
            out.append(f"品質：{where} 用了「以上皆是／皆非」類的選項，建議改成具體的敘述。")
        if t == "multi":
            if len(q["a"]) == len(q["o"]):
                out.append(f"品質：{where} 複選題的選項全部都是正確答案。")
            elif len(q["a"]) == 1:
                out.append(f"提醒：{where} 複選題只有一個正確答案（允許，但建議偶爾為之）。")
            if not re.search(r"選出所有|所有正確|哪些", q["q"]):
                out.append(f"提醒：{where} 複選題的題目建議註明「（選出所有正確答案）」。")
        e = q.get("e", "")
        if re.search(r"圖上|圖中|附圖|如圖", e + q.get("q", "")) and not (q.get("img") or q.get("eimg")):
            out.append(f"提醒：{where} 的題目或解析提到圖，但沒有附圖。")
    no_trap = [q["n"] for q in qs if q.get("e") and "容易卡住的地方" not in q["e"]]
    if no_trap and len(no_trap) / max(1, len(qs)) > 0.3:
        out.append(f"提醒：有 {len(no_trap)} 題的解析沒有「容易卡住的地方」段落（例如第 {'、'.join(map(str, no_trap[:5]))} 題）。")
    return out


def load_images(folder, wanted):
    imgs, notes = {}, []
    if not folder:
        return imgs, notes
    try:
        from PIL import Image
    except Exception:
        Image = None
    files = {p.stem: p for p in sorted(Path(folder).iterdir()) if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")}
    for key, p in files.items():
        if key not in wanted:
            notes.append(f"圖片 {p.name} 沒有被任何題目用到，沒有放進練習簿。")
            continue
        data = p.read_bytes()
        ext = p.suffix.lower()
        if ext == ".svg":
            mime = "image/svg+xml"
        elif Image is not None and ext in (".png", ".jpg", ".jpeg") :
            im = Image.open(io.BytesIO(data))
            im.thumbnail((1800, 1800))
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=82, method=6)
            if buf.tell() < len(data):
                data, mime = buf.getvalue(), "image/webp"
            else:
                mime = mimetypes.guess_type(p.name)[0]
        else:
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
        imgs[key] = f"data:{mime};base64," + base64.b64encode(data).decode()
    return imgs, notes


def _js_to_json(src):
    """把 JS 物件／陣列字面值（鍵沒有引號、單引號字串、結尾逗號）轉成 JSON。只轉換資料，不執行任何程式。"""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            j, buf = i + 1, []
            while j < n and src[j] != c:
                if src[j] == "\\":
                    buf.append(src[j:j + 2]); j += 2; continue
                buf.append(src[j]); j += 1
            body = "".join(buf)
            if c == "'":
                body = body.replace("\\'", "'").replace('"', '\\"')
            out.append('"' + body + '"'); i = j + 1; continue
        if c.isalpha() or c in "_$":
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            k = j
            while k < n and src[k] in " \t\r\n":
                k += 1
            word = src[i:j]
            out.append('"' + word + '"' if k < n and src[k] == ":" and (not out or out[-1].strip()[-1:] in "{,") else word)
            i = j; continue
        if c == ",":
            k = i + 1
            while k < n and src[k] in " \t\r\n":
                k += 1
            if k < n and src[k] in "]}":
                i += 1; continue
        out.append(c); i += 1
    return "".join(out)


def _literal_end(t, i):
    depth, j, n = 0, i, len(t)
    while j < n:
        c = t[j]
        if c in "\"'`":
            j += 1
            while j < n and t[j] != c:
                j += 2 if t[j] == "\\" else 1
        elif c in "[{(":
            depth += 1
        elif c in "]})":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError("括號沒有成對")


def _decode_after(t, marker):
    i = t.find(marker)
    if i < 0:
        return None
    i += len(marker)
    try:
        return json.JSONDecoder().raw_decode(t, i)[0]
    except json.JSONDecodeError:
        return json.loads(_js_to_json(t[i:_literal_end(t, i)]))


def extract(html_path, dump_dir):
    """從練習簿 HTML 取出題庫。新版讀資料區塊；舊版（題目寫在程式裡）盡量轉成新格式並沿用作答紀錄的 key。"""
    t = Path(html_path).read_text(encoding="utf-8")
    out = Path(dump_dir)
    out.mkdir(parents=True, exist_ok=True)
    m = re.search(r'<script type="application/json" id="bank">\n(.*?)\n</script>', t, re.S)
    if m and not m.group(1).strip().startswith("__"):
        bank = json.loads(m.group(1))
        mi = re.search(r'<script type="application/json" id="bank-images">\n(.*?)\n</script>', t, re.S)
        imgs = json.loads(mi.group(1)) if mi and not mi.group(1).strip().startswith("__") else {}
        kind = "新版"
    else:
        q = _decode_after(t, "const Q = ")
        if q is None:
            sys.exit("看不出這是練習簿：找不到題庫資料區塊，也找不到舊版的 const Q。")
        imgs = _decode_after(t, "const IMG = ") or {}
        abbr_raw = _decode_after(t, "const ABBR = ") or []
        groups = _decode_after(t, "const GROUPS = ") or []
        g = lambda pat, d="": (re.search(pat, t, re.S).group(1).strip() if re.search(pat, t, re.S) else d)
        key = g(r'const KEY = "([^"]+)"')
        sk = {"local": key, "aiLocal": g(r'const AIKEY = "([^"]+)"'),
              "remote": g(r'"/([A-Za-z0-9_.~:@+-]+-progress)"'), "inbox": g(r'"/([A-Za-z0-9_.~:@+-]+-inbox)"'),
              "aiRemote": g(r'"/([A-Za-z0-9_.~:@+-]+)-" \+ Math\.floor\(n / 100\)')}
        cid = re.sub(r"[^a-z0-9-]", "-", re.sub(r"-progress-v\d+$", "", key.lower())).strip("-")[:40] or "workbook"
        config = {"id": cid if len(cid) >= 2 else "workbook", "title": g(r"<title>([^<]*)</title>", "練習簿"),
                  "subtitle": "", "mainLabel": g(r'const TYPE_NAME = \{mcq:"([^"]+)"', "選擇題"),
                  "passLine": int(g(r"參考及格線 (\d+)%", "80")), "passNote": "", "pace": int(g(r'pace:(\d+)', "60")),
                  "examNote": g(r'<p class="note">(正式考試是[^$<]*?)\$\{'),
                  "aiRole": g(r'AI_RULES = "你是 ?(.+?)，要替'), "aiTerms": g(r"用繁體中文（?[^，]*?）?，(.+?)。\\n"),
                  "aiBasis": g(r"\\n- (依.+?)。如果你認為"), "abbrScope": g(r"說明這個縮寫是什麼、在 ?(.+?) ?中會出現在什麼情境"),
                  "storageKeys": {k: v for k, v in sk.items() if v}}
        abbr = [{"cat": r[0], "abbr": r[1], "full": r[2], "alts": r[3], "e": r[4]} if isinstance(r, list) else r for r in abbr_raw]
        bank = {"config": config, "questions": q, "abbr": abbr, "groups": groups}
        kind = "舊版"
    (out / "bank.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "images.json").write_text(json.dumps(imgs, ensure_ascii=False), encoding="utf-8")
    print(f"已從{kind}練習簿取出 {len(bank.get('questions', []))} 題、縮寫 {len(bank.get('abbr', []))} 個、圖片 {len(imgs)} 張到 {out}/")
    if kind == "舊版":
        print("提醒：config 是從舊程式推測的，請檢查 title、subtitle、aiRole 等欄位；storageKeys 沿用舊的作答紀錄，不要刪。")


def embed(tpl, block_id, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")
    pat = re.compile(r'(<script type="application/json" id="' + re.escape(block_id) + r'">\n)(.*?)(\n</script>)', re.S)
    if not pat.search(tpl):
        sys.exit(f"範本裡找不到 id=\"{block_id}\" 的資料區塊。")
    return pat.sub(lambda m: m.group(1) + text + m.group(3), tpl, count=1)


def main():
    ap = argparse.ArgumentParser(description="把題庫 JSON 塞進練習簿範本")
    ap.add_argument("--bank", help="題庫 JSON 檔")
    ap.add_argument("--images", help="圖片資料夾（檔名去掉副檔名 = 圖片代號）")
    ap.add_argument("--images-json", help="圖片對照表 JSON（{代號: data URI 或路徑}），例如 --extract 取出的 images.json")
    ap.add_argument("--extract", help="從現有的練習簿 HTML 取出題庫")
    ap.add_argument("--dump", help="--extract 的輸出資料夾")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="範本 HTML")
    ap.add_argument("--out", help="輸出的 HTML")
    ap.add_argument("--check", action="store_true", help="只檢查，不產生檔案")
    ap.add_argument("--force", action="store_true", help="有錯誤也產生檔案")
    args = ap.parse_args()
    if args.extract:
        extract(args.extract, args.dump or "extracted")
        return
    if not args.bank:
        sys.exit("要指定 --bank 題庫檔（或用 --extract 取出現有練習簿的題庫）。")

    try:
        bank = json.loads(Path(args.bank).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"題庫不是合法的 JSON：第 {e.lineno} 行第 {e.colno} 字，{e.msg}")
    wanted = {k for q in bank.get("questions", []) if isinstance(q, dict) for f in ("img", "eimg") for k in (q.get(f) or []) if isinstance(k, str)}
    imgs, img_notes = load_images(args.images, wanted)
    if args.images_json:
        extra = json.loads(Path(args.images_json).read_text(encoding="utf-8"))
        unused = [k for k in extra if k not in wanted]
        if unused:
            img_notes.append(f"images.json 有 {len(unused)} 張圖沒有被題目用到，沒有放進練習簿。")
        imgs.update({k: v for k, v in extra.items() if k in wanted and isinstance(v, str) and v})
    errors, notes, nvoid = validate(bank, set(imgs))
    notes = img_notes + notes

    qs = [q for q in bank.get("questions", []) if isinstance(q, dict)]
    mix = Counter(q.get("type", "mcq") for q in qs)
    print("題型：" + "、".join(f"{TYPE_ZH.get(k, k)} {v}" for k, v in mix.items()) + f"、縮寫 {len(bank.get('abbr', []))}、易混淆組 {len(bank.get('groups', []))}"
          + (f"、不可作答 {nvoid}" if nvoid else ""))
    for e in errors:
        print("錯誤：" + e)
    for n in notes:
        print(n if n.startswith(("品質：", "提醒：")) else "提醒：" + n)
    if not errors:
        print("格式檢查通過。")
    if args.check:
        sys.exit(1 if errors else 0)
    if not args.out:
        sys.exit("要指定 --out 輸出檔名。")
    if errors and not args.force:
        sys.exit(f"有 {len(errors)} 個錯誤，沒有產生檔案。修正後再執行，或加 --force。")

    tpl = Path(args.template).read_text(encoding="utf-8")
    tpl = embed(tpl, "bank", bank)
    tpl = embed(tpl, "bank-images", imgs)
    title = bank.get("config", {}).get("title") or "模擬考練習簿"
    tpl = re.sub(r"<title>.*?</title>", lambda m: "<title>" + title.replace("&", "&amp;").replace("<", "&lt;") + "</title>", tpl, count=1)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl, encoding="utf-8")
    print(f"已產生 {out}（{out.stat().st_size / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
