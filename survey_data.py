# -*- coding: utf-8 -*-
"""survey existing data files for KG schema design"""
import json, os
os.chdir(r"D:\Desktop\VAST CHALLENGE")

def show(name):
    with open(name, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        print(f"\n=== {name} === list[{len(data)}]")
        print(f"  keys: {list(data[0].keys())}")
        sample = data[50]
        for k,v in sample.items():
            s = str(v)[:100]
            print(f"  {k}: {s}")
    else:
        print(f"\n=== {name} === dict[{len(data)}]")
        sample_k = list(data.keys())[0]
        print(f"  sample key: {sample_k} -> {data[sample_k]}")

for f in ["hbh_events_raw.json","alias_map.json","hbh_persons.json",
          "hbh_interactions.json","hbh_locations.json","hbh_creations.json",
          "hbh_topics.json"]:
    show(f)
