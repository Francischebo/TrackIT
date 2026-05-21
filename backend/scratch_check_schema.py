import sqlite3

def check_schema():
    conn = sqlite3.connect('trackit_dev.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transfer_requests)")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_schema()
