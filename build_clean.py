# -*- coding: utf-8 -*-
"""生成只含可用站的新 box.json（保留 type3 全部 + 连通性测试通过的 type0/1）。"""
import json

d = json.load(open("box.json", encoding="utf-8"))
final = set(json.load(open("final_result.json", encoding="utf-8"))["final_remote"])

new_sites = []
for s in d["sites"]:
    if s.get("type") == 3:
        new_sites.append(s)
    elif s.get("type") in (0, 1) and s["key"] in final:
        new_sites.append(s)

d["sites"] = new_sites
json.dump(d, open("box.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(d, open("box-remote.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

t3 = sum(1 for s in new_sites if s.get("type") == 3)
t1 = sum(1 for s in new_sites if s.get("type") == 1)
t0 = sum(1 for s in new_sites if s.get("type") == 0)
print("保留 %d 站  (type1=%d, type0=%d, type3=%d)" % (len(new_sites), t1, t0, t3))
print("\n--- 保留的远端站 ---")
for s in new_sites:
    if s.get("type") in (0, 1):
        print("  [%d] %s" % (s["type"], s.get("name", s["key"])))
