# -*- coding: utf-8 -*-
"""测试 box.json 里 type 0/1 远端采集接口的连通性，只保留能返回有效数据的站。"""
import json, sys, io, re
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BOX = "box.json"
TIMEOUT = 12
WORKERS = 24

def fetch(url):
    """返回 (ok, reason, info)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            code = r.status
            data = r.read(300000)
    except urllib.error.HTTPError as e:
        return False, "HTTP %d" % e.code, {}
    except urllib.error.URLError as e:
        return False, "URLError:%s" % getattr(e, "reason", e), {}
    except Exception as e:
        return False, "Err:%s" % type(e).__name__, {}

    if code != 200:
        return False, "HTTP %d" % code, {}
    if len(data) < 20:
        return False, "empty", {}

    text = data.decode("utf-8", "ignore")
    s = text.lstrip()

    # 1) JSON 采集接口（provide/vod 标准返回）
    try:
        j = json.loads(text)
        info = {}
        if isinstance(j, dict):
            lst = j.get("list") or j.get("data") or j.get("vodlist") or []
            info["code"] = j.get("code")
            info["msg"] = j.get("msg", "")
            if isinstance(lst, list):
                if len(lst) > 0:
                    info["n"] = len(lst)
                    return True, "json list=%d" % len(lst), info
                # list 为空：接口活着但无数据，也算连得上
                if j.get("code") in ("1", 1, 200, "200", 0, "0"):
                    return True, "json ok(empty)", info
                return False, "json no-list", info
            # 有 code 成功字段
            if j.get("code") in ("1", 1, 200, "200"):
                return True, "json code-ok", info
            return False, "json no-list", info
        elif isinstance(j, list):
            if len(j) > 0:
                return True, "json array=%d" % len(j), {"n": len(j)}
            return False, "json empty-array", {}
    except Exception:
        pass

    # 2) XML / HTML 数据
    if s.startswith("<?xml") or s.startswith("<"):
        low = text[:2000].lower()
        if "vod" in low or "item" in low or "<list" in low or "video" in low:
            return True, "xml/html", {}
        return False, "html-no-vod", {}

    return False, "unknown-content", {}


def main():
    with open(BOX, encoding="utf-8") as f:
        d = json.load(f)
    sites = d["sites"]
    remote = [s for s in sites if s.get("type") in (0, 1) and s.get("api", "").startswith("http")]
    local = [s for s in sites if s.get("type") == 3]
    print("远端接口站: %d  本地csp站: %d" % (len(remote), len(local)))

    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch, s["api"]): s for s in remote}
        for i, fut in enumerate(as_completed(futs), 1):
            s = futs[fut]
            ok, reason, info = fut.result()
            results[s["key"]] = (ok, reason, info)
            if i % 20 == 0:
                print("  进度 %d/%d" % (i, len(remote)), flush=True)

    good = [s for s in remote if results[s["key"]][0]]
    bad = [s for s in remote if not results[s["key"]][0]]

    print("\n================ 结果 ================")
    print("连得上: %d   连不上: %d" % (len(good), len(bad)))
    print("\n--- 连不上的站（%d）---" % len(bad))
    for s in bad:
        ok, reason, info = results[s["key"]]
        print("  [%s] %s  <- %s" % (s.get("type"), s.get("name", s["key"]), reason))

    # 保存结果
    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "good": [s["key"] for s in good],
            "bad": {s["key"]: results[s["key"]][1] for s in bad},
        }, f, ensure_ascii=False, indent=2)
    print("\n已保存 test_result.json")


if __name__ == "__main__":
    main()
