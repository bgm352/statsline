import os
import sqlite3

# Define absolute path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "armor_os.db")


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT UNIQUE,
            title TEXT,
            price REAL,
            url TEXT,
            image_url TEXT,
            opencv_status TEXT DEFAULT 'PENDING',
            review_status TEXT DEFAULT 'UNREVIEWED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


def save_candidate(item):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  try:
    cursor.execute(
        """
            INSERT OR IGNORE INTO candidates (item_id, title, price, url, image_url)
            VALUES (?, ?, ?, ?, ?)
        """,
        (
            item["item_id"],
            item["title"],
            item["price"],
            item["url"],
            item["image_url"],
        ),
    )
    conn.commit()
  except Exception as e:
    print(f"DB Error: {e}")
  finally:
    conn.close()


if __name__ == "__main__":
  init_db()
  print(f"Database initialized at: {DB_NAME}")
