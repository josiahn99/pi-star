import pandas as pd
import sqlite3
import os
import requests

csv_url = "https://radioid.net/static/user.csv"
local_csv = "dig_id_user.csv"
db_file = "dig_id_user.db"

# 1. Download CSV if it doesn't exist
if not os.path.exists(local_csv):
    r = requests.get(csv_url)
    with open(local_csv, 'wb') as f:
        f.write(r.content)

# 2. Load CSV and write to SQLite
df_ids = pd.read_csv(local_csv)
conn = sqlite3.connect(db_file)
df_ids.to_sql("dig_id_user", conn, if_exists="replace", index=False)
conn.close()
