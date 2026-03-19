import sqlite3
import glob
import re
import os

# ----- CONFIG -----

LOG_DIR = "/var/log/pi-star"
DB_FILE = "/home/pi-star/transmissions.db"

# ----- CONNECT TO DATABASE -----

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Create table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS transmissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    slot INTEGER,
    source_id TEXT,
    target_id INTEGER,
    duration REAL,
    packet_loss REAL,
    ber REAL,
    UNIQUE(timestamp, slot, source_id, target_id)
)
""")

conn.commit()

# ----- FIND LOG FILES -----

log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))

if not log_files:
    print("No log files found.")
    exit()

print(f"Found {len(log_files)} log files")

# ----- REGEX PATTERN -----

pattern = re.compile(
    r"M:\s(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+\sDMR Slot (\d), received network end of voice transmission from (\S+) to TG (\d+), ([\d\.]+) seconds, ([\d\.]+)% packet loss, BER: ([\d\.]+)%"
)

total_inserted = 0

# ----- PROCESS LOG FILES -----

for log_file in log_files:

    print(f"Processing {log_file}")

    with open(log_file, "r") as f:

        conn.execute("BEGIN")

        for line in f:

            match = pattern.search(line)

            if match:

                ts, slot, source, target, duration, loss, ber = match.groups()

                cur.execute(
                    """
                    INSERT OR IGNORE INTO transmissions
                    (timestamp, slot, source_id, target_id, duration, packet_loss, ber)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ts,
                        int(slot),
                        source,
                        int(target),
                        float(duration),
                        float(loss),
                        float(ber),
                    ),
                )

                total_inserted += cur.rowcount

        conn.commit()

# ----- DONE -----

print(f"Inserted {total_inserted} new transmissions")

conn.close()
