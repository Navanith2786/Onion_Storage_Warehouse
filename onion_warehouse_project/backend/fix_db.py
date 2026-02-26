import sqlite3
import os

db_paths = [
    r"c:\Users\ADMIN\Documents\PlatformIO\Projects\onion_warehouse_project\backend\instance\onion_warehouse.db",
    r"c:\Users\ADMIN\Documents\PlatformIO\Projects\onion_warehouse_project\instance\onion_warehouse.db"
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"Updating database: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("ALTER TABLE sensor_reading ADD COLUMN cooler_on BOOLEAN DEFAULT 0;")
            conn.commit()
            conn.close()
            print(f"Successfully added 'cooler_on' column to {db_path}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column already exists in {db_path}")
            else:
                print(f"Error: {e}")
    else:
        print(f"Database not found at: {db_path}")
