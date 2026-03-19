import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import base64
import requests
import os

# connect to database
conn = sqlite3.connect("transmissions.db")

# Attach the second database (digital IDs)
conn.execute("ATTACH DATABASE 'dig_id_user.db' AS digid")

df = pd.read_sql_query("""
SELECT t.timestamp, t.source_id, d.CALLSIGN, STATE
FROM transmissions t
LEFT JOIN digid.dig_id_user d
ON t.source_id = d.CALLSIGN
ORDER BY t.timestamp
""", conn)

# convert date column
df['date'] = pd.to_datetime(df['timestamp'])


start_date = "2026-03-10"
end_date = "2026-03-11"

mask = (df['date'] >= start_date)
df_period = df.loc[mask]

users_per_state = df_period.groupby('STATE')['source_id'].nunique().reset_index(name='num_users')
df_sorted = users_per_state.sort_values(by='num_users', ascending=True)
print(df_sorted)

#plot

plt.figure(figsize=(10,6))
plt.barh(df_sorted['STATE'], df_sorted['num_users'], color='skyblue')
plt.title("Unique Users per Sub-Country Jurisdiction since 3/10/26")
plt.xticks(rotation=0)
plt.tight_layout()
plt.tick_params(axis='y', labelsize=6)  # smaller font on y-axis
plt.show()

# save static image
plt.savefig("users_by_state.jpg", dpi=200)

conn.close()

# --- GITHUB API INFO
GITHUB_USER = "josiahn99"
REPO = "kc1yqn"
file_path = "users_by_state.jpg"
FILE_PATH_IN_REPO = "assets/images/users_by_state.jpg"  # path in repo
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")  # read from environment

if not TOKEN:
    print("❌ Set GITHUB_TOKEN environment variable!")
    exit(1)

# --- Encode the file ---
with open(file_path, "rb") as f:
    content = f.read()
encoded_content = base64.b64encode(content).decode("utf-8")

# --- Prepare API URL ---
url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO}/contents/{FILE_PATH_IN_REPO}"

# --- Check if file exists to get SHA ---
headers = {"Authorization": f"token {TOKEN}"}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    sha = response.json()["sha"]
else:
    sha = None

# --- Prepare payload for PUT ---
payload = {
    "message": "Add JPG",
    "content": encoded_content,
    "branch": BRANCH
}

if sha:
    payload["sha"] = sha

# --- Push file ---
r = requests.put(url, json=payload, headers=headers)

if r.status_code in [200, 201]:
    print("✅ File pushed to GitHub!")
else:
    print(f"❌ Failed: {r.status_code} - {r.text}")
