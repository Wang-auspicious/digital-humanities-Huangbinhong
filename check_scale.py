# -*- coding: utf-8 -*-
import json
with open("hbh_events_raw.json", encoding="utf-8") as f:
    evts = json.load(f)

content = [e for e in evts if e.get("type") != "year_header"]
total_chars = sum(len(e.get("raw_text","")) for e in content)
texts = [e.get("raw_text","") for e in content]
lens = [len(t) for t in texts]

print(f"content events: {len(content)}")
print(f"total chars: {total_chars}")
print(f"avg chars/event: {total_chars//len(content)}")
print(f"max chars: {max(lens)}")
print(f"min chars: {min(lens)}")

for e in content[100:103]:
    print("---")
    print(f"{e['id']} [{e['year']}]: {e['raw_text'][:200]}")
