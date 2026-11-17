# -*- coding: utf-8 -*-
"""最终化：去掉 2 个 18cn csp 站（转点 / csp_xBPQ_公子福利），
生成 box.json（自托管相对路径）与 box-remote.json（绝对 URL），并校验所有本地引用。"""
import json, os, re, sys

DROP = {"转点", "csp_xBPQ_公子福利"}

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def strip_local_query(site):
    """把本地 ./spiders/xxx?v=... 的查询串去掉，保留纯相对路径。"""
    def fix(m):
        return m.group(0).split("?")[0]
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, str):
            return re.sub(r"(\./spiders/[^\"\\]+?)\?[^\"]*", lambda m: m.group(1), o)
        return o
    return walk(site)

def drop_sites(cfg):
    cfg["sites"] = [s for s in cfg["sites"] if s.get("key") not in DROP]
    # 去掉引用本地 ./lib/ 的直播源（RTV.txt 拿不到），保留可正常工作的远端直播
    if isinstance(cfg.get("lives"), list):
        cfg["lives"] = [lv for lv in cfg["lives"]
                        if "./lib/" not in json.dumps(lv, ensure_ascii=False)]
    return cfg

def collect_local_refs(cfg):
    refs = set()
    txt = json.dumps(cfg, ensure_ascii=False)
    for m in re.finditer(r"\./spiders/[^\"\s\\]+", txt):
        refs.add(m.group(0).split("?")[0])
    return refs

def main():
    selfhosted = drop_sites(load("box-selfhosted.json"))
    remote = drop_sites(load("box.json"))

    # 自托管版：清理本地路径查询串
    selfhosted["sites"] = [strip_local_query(s) for s in selfhosted["sites"]]

    # 保存
    with open("box.json", "w", encoding="utf-8") as f:
        json.dump(selfhosted, f, ensure_ascii=False, indent=2)
    with open("box-remote.json", "w", encoding="utf-8") as f:
        json.dump(remote, f, ensure_ascii=False, indent=2)

    # 校验
    refs = collect_local_refs(selfhosted)
    print("=== 自托管 box.json 本地文件引用 ===")
    missing = []
    for r in sorted(refs):
        ok = os.path.exists(r)
        if not ok:
            missing.append(r)
        print(("  OK  " if ok else "  MISS") + " " + r)

    # 检查是否还有 ./lib/ 或 csp_xBPQ 残留
    txt = json.dumps(selfhosted, ensure_ascii=False)
    print("\n=== 残留检查 ===")
    print("  ./lib/ 引用:", txt.count("./lib/"))
    print("  csp_xBPQ 引用:", txt.count("csp_xBPQ"))
    print("  CFlLnSbJ 引用:", txt.count("CFlLnSbJ"))

    # 统计
    types = {}
    for s in selfhosted["sites"]:
        types[s.get("type")] = types.get(s.get("type"), 0) + 1
    print("\n=== box.json 站点统计 ===")
    print("  总站点:", len(selfhosted["sites"]))
    print("  按类型:", types)
    print("  缺失文件:", missing if missing else "无")

    # 顶层字段
    print("\n=== 顶层字段 ===")
    print("  ", {k: (f"<list {len(v)}>" if isinstance(v, list) else v) for k, v in selfhosted.items()})

if __name__ == "__main__":
    main()
