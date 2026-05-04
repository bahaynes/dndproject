import sqlite3
import time
import statistics

def setup_db(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
    cursor.execute("CREATE TABLE characters (id INTEGER PRIMARY KEY, name TEXT, owner_id INTEGER, campaign_id INTEGER)")

    users = [(i, f"user_{i}") for i in range(1, 101)]
    cursor.executemany("INSERT INTO users VALUES (?, ?)", users)

    characters = [(i, f"char_{i}", (i % 100) + 1, 1) for i in range(1, 1001)]
    cursor.executemany("INSERT INTO characters VALUES (?, ?, ?, ?)", characters)
    conn.commit()

def n_plus_one_query(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, owner_id FROM characters WHERE campaign_id = 1")
    chars = cursor.fetchall()

    result = []
    for char in chars:
        char_id, name, owner_id = char
        cursor.execute("SELECT username FROM users WHERE id = ?", (owner_id,))
        owner = cursor.fetchone()
        result.append({
            "id": char_id,
            "name": name,
            "owner_username": owner[0] if owner else None
        })
    return result

def optimized_query(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, u.username
        FROM characters c
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE c.campaign_id = 1
    """)
    chars = cursor.fetchall()

    result = []
    for char in chars:
        char_id, name, username = char
        result.append({
            "id": char_id,
            "name": name,
            "owner_username": username
        })
    return result

def run_benchmark():
    conn = sqlite3.connect(":memory:")
    setup_db(conn)

    iterations = 50

    n1_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        n_plus_one_query(conn)
        n1_times.append(time.perf_counter() - start)

    opt_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        optimized_query(conn)
        opt_times.append(time.perf_counter() - start)

    avg_n1 = statistics.mean(n1_times)
    avg_opt = statistics.mean(opt_times)
    improvement = (avg_n1 - avg_opt) / avg_n1 * 100

    print(f"Benchmark Results (over {iterations} iterations):")
    print(f"N+1 Query Average Time:  {avg_n1:.6f} seconds")
    print(f"Optimized Average Time:  {avg_opt:.6f} seconds")
    print(f"Improvement:             {improvement:.2f}%")

    conn.close()

if __name__ == "__main__":
    run_benchmark()
