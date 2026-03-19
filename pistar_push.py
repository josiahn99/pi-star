#!/usr/bin/env python3

import json
import os
import base64
from operator import concat
import requests
from datetime import datetime
import glob
import re

# ----- CONFIG -----
#Automatically pick the latest MMDVM log

log_files = sorted(glob.glob("/var/log/pi-star/MMDVM-*.log"))
if not log_files:
    raise FileNotFoundError("No MMDVM log files found")
log_file = log_files[-1]  # newest file


# --- GITHUB API INFO
GITHUB_USER = "josiahn99"
REPO = "kc1yqn"
FILE_PATH_IN_REPO = "./_data/pi-star.json"
#LOCAL_JSON_PATH = "/home/pi-star/mydata.json"   # local file path (optional)
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")     # read from environment

if not TOKEN:
    print("❌ Set GITHUB_TOKEN environment variable!")
    exit(1)


# ------------------

max_entries = 50

entries = []

# --- REGEX Pattern

pattern = re.compile(
    r"M:\s(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+\sDMR Slot (\d), received network end of voice transmission from (\S+) to TG (\d+), ([\d\.]+) seconds, ([\d\.]+)% packet loss, BER: ([\d\.]+)%"
)

with open(log_file) as f:
    lines = f.readlines()[-max_entries:]

    for line in lines:
        match = pattern.search(line)
        if not match:
            continue

        ts, slot, source, target, duration, loss, ber = match.groups()

        entries.append({
            "time": ts,
            "callsign": source,
            "tg_slot": target,
        })

entries.sort(key=lambda x: x["time"], reverse=True)

commit_message = "Update Pi-Star log JSON"
json_string = json.dumps(entries)
encoded = base64.b64encode(json_string.encode()).decode()

payload = {
    "message": "Update Pi-Star log JSON",
    "content": encoded,
    "branch": BRANCH,
    }
"""
# Save JSON locally (optional)
with open(LOCAL_JSON_PATH, "w") as f:
    json.dump(data, f, indent=2)
"""
# --------- PUSH TO GITHUB ---------
url = f"https://api.github.com/repos/josiahn99/kc1yqn/contents/_data/pi-star.json"

print("URL:", url)
print("Encoded length:", len(encoded))
print("Payload keys:", payload.keys())
print("Branch:", BRANCH)

# Check if file exists to get SHA
response = requests.get(url, headers={"Authorization": f"token {TOKEN}"})
if response.status_code == 200:
    sha = response.json()["sha"]
else:
    sha = None

if sha:
    payload["sha"] = sha

r = requests.put(url, headers={"Authorization": f"token {TOKEN}"}, data=json.dumps(payload))

if r.status_code in [200, 201]:
    print("✅ JSON pushed to GitHub!")
else:
    print(f"❌ Failed: {r.status_code} - {r.text}")
