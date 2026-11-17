# -*- coding: utf-8 -*-
"""对上一轮走代理失败的站，用直连（绕过系统代理）重测，能救回的保留。"""
import json, sys, io
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
TIMEOUT = 12
WORKERS = 24

def judge(data, text, s):
    low = text[:2000].lower()
    try:
        j = json.loads(text)
        if isinstance(j, dict):
            lst = j.get("list") or j.get("data") or j.get("vodlist") or []
            if isinstance(lst, list) and len(lst) > 0:
                return True, "json list=%d" % len(lst)
            if j.get("code") in ("1", 1, 200, "200", 0, "0"):
                return True, "json code-ok"
            return False, "json no-list"
        elif isinstance(j, list):
            return (len(j) > 0, "json array=%d" % len(j))
    except Exception:
        pass
    if s.startswith("<?xml") or s.startswith("<"):
        if "vod" in low or "item" in low or "<list" in low or "video" in low:
            return True, "xml/html"
        return False, "html-no-vod"
    return False, "unknown"

def fetch_direct(url):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "*/*"})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            code = r.status
            data = r.read(300000)
    except Exception as e:
        return False, "Direct:%s:%s" % (type(e).__name__, getattr(e, "reason", e)), {}
    if code != 200:
        return False, "HTTP %d" % code, {}
    if len(data) < 20:
        return False, "empty", {}
    text = data.decode("utf-8", "ignore")
    ok, reason = judge(data, text, text.lstrip())
    return ok, reason, {}

def main():
    d = json.load(open("box.json", encoding="utf-8"))
    r = json.load(open("test_result.json", encoding="utf-8"))
    bad_keys = set(r["bad"].keys())
    bad_sites = [s for s in d["sites"] if s.get("type") in (0, 1) and s["key"] in bad_keys]
    print("直连重测 %d 个失败站..." % len(bad_sites), flush=True)

    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_direct, s["api"]): s for s in bad_sites}
        for i, fut in enumerate(as_completed(futs), 1):
            s = futs[fut]
            results[s["key"]] = fut.result()
            if i % 20 == 0:
                print("  进度 %d/%d" % (i, len(bad_sites)), flush=True)

    saved = [s for s in bad_sites if results[s["key"]][0]]
    still_bad = [s for s in bad_sites if not results[s["key"]][0]]
    print("\n直连救回: %d   仍连不上: %d" % (len(saved), len(still_bad)))
    print("\n--- 直连救回的站 ---")
    for s in saved:
        print("  [%s] %s  <- %s" % (s.get("type"), s.get("name", s["key"]), results[s["key"]][1]))

    # 合并最终保留
    good_proxy = set(r["good"])
    good_direct = {s["key"] for s in saved}
    final_remote = good_proxy | good_direct
    print("\n=== 最终远端保留: %d (代理成功 %d + 直连救回 %d) ===" % (
        len(final_remote), len(good_proxy), len(good_direct)))

    json.dump({
        "final_remote": sorted(final_remote),
        "saved_direct": sorted(good_direct),
        "still_bad": {s["key"]: results[s["key"]][1] for s in still_bad},
    }, open("final_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已保存 final_result.json")

if __name__ == "__main__":
    main()
