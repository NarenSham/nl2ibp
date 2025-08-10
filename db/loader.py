import sqlite3

DB_PATH = "db/optiguide.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open("db/schema.sql", "r") as f:
        cursor.executescript(f.read())

    # Sample data
    warehouses = [
        (1, "Warehouse A", 43.65107, -79.347015),
        (2, "Warehouse B", 43.6532, -79.3832),
    ]

    retailers = [
        (1, "Retailer X", 100, 43.6629, -79.3957),
        (2, "Retailer Y", 80, 43.6455, -79.3806),
        (3, "Retailer Z", 60, 43.6414, -79.3894),
    ]

    routes = [
        (1, 1, 1, 12.0),
        (2, 1, 2, 15.5),
        (3, 1, 3, 20.0),
        (4, 2, 1, 14.0),
        (5, 2, 2, 10.0),
        (6, 2, 3, 8.5),
    ]

    cursor.executemany("INSERT INTO warehouses VALUES (?, ?, ?, ?);", warehouses)
    cursor.executemany("INSERT INTO retailers VALUES (?, ?, ?, ?, ?);", retailers)
    cursor.executemany("INSERT INTO routes VALUES (?, ?, ?, ?);", routes)

    conn.commit()
    conn.close()
    print("Database initialized and sample data inserted.")

if __name__ == "__main__":
    init_db()
