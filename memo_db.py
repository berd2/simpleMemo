import sqlite3
from datetime import datetime

class MemoDB:
    def __init__(self, db_path='nemo_memo.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        self.create_state_table()
        self._migrate_schema()

    def create_state_table(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS notepad_state (key TEXT PRIMARY KEY, value TEXT)")

    def save_state(self, key, value):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO notepad_state (key, value) VALUES (?, ?)", (key, str(value)))

    def load_state(self, key, default=None):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM notepad_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_important INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL DEFAULT '',
                    sort_order INTEGER
                )
            """)

    def _migrate_schema(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(memos)")
            columns = [info[1] for info in cursor.fetchall()]

            # Check if migration is needed by looking for a column that was removed.
            if 'importance_timestamp' in columns:
                print("Schema migration needed. Migrating...")
                # 1. Rename old table
                cursor.execute("ALTER TABLE memos RENAME TO memos_old")

                # 2. Create new table with the correct schema
                self.create_table()

                # 3. Migrate data
                cursor.execute("SELECT id, title, created_at, content, is_important, category, sort_order FROM memos_old")
                old_memos = cursor.fetchall()

                for memo in old_memos:
                    (id, title, created_at_str, content, is_important, category, sort_order) = memo
                    
                    # Convert created_at from ISO string to epoch integer
                    try:
                        # Example format: 2023-11-05T10:30:00.123456
                        dt_obj = datetime.fromisoformat(created_at_str)
                        created_at_epoch = int(dt_obj.timestamp())
                    except (ValueError, TypeError):
                        # Fallback for invalid or empty date strings
                        created_at_epoch = int(datetime.now().timestamp())

                    # Ensure sort_order has a value
                    final_sort_order = sort_order if sort_order is not None else id

                    cursor.execute('''
                        INSERT INTO memos (id, title, created_at, content, is_important, category, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (id, title, created_at_epoch, content, is_important, category, final_sort_order))

                # 4. Drop the old table
                cursor.execute("DROP TABLE memos_old")
                print("Schema migration completed.")

            # Migration to add sort_order if it's missing from a previous version
            if 'sort_order' not in columns:
                cursor.execute("ALTER TABLE memos ADD COLUMN sort_order INTEGER")
                cursor.execute("UPDATE memos SET sort_order = id WHERE sort_order IS NULL")

    def get_all_memos(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, title, created_at, content, is_important, category, sort_order FROM memos ORDER BY is_important DESC, sort_order DESC")
            return cursor.fetchall()

    def get_memo_by_id(self, memo_id):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, title, created_at, content, is_important, category, sort_order FROM memos WHERE id = ?", (memo_id,))
            return cursor.fetchone()

    def add_memo(self, title, content, category='', is_important=0):
        now_ts = int(datetime.now().timestamp())
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memos (title, created_at, content, is_important, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                (title, now_ts, content, is_important, category, now_ts)
            )
            return cursor.lastrowid

    def update_memo(self, memo_id, title, content):
        with self.conn:
            # `created_at` is not updated here, as it marks the creation time.
            self.conn.execute(
                "UPDATE memos SET title = ?, content = ? WHERE id = ?",
                (title, content, memo_id)
            )

    def update_memo_importance(self, memo_id, is_important):
        with self.conn:
            self.conn.execute(
                "UPDATE memos SET is_important = ? WHERE id = ?",
                (1 if is_important else 0, memo_id)
            )

    def delete_memo(self, memo_id):
        with self.conn:
            self.conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))

    def restore_memo(self, memo_id, title, created_at, content, is_important, category, sort_order):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO memos
                   (id, title, created_at, content, is_important, category, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (memo_id, title, created_at, content, is_important, category, sort_order)
            )

    def swap_memo_order(self, memo_id_1, memo_id_2):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT sort_order FROM memos WHERE id = ?", (memo_id_1,))
            order1 = cursor.fetchone()
            cursor.execute("SELECT sort_order FROM memos WHERE id = ?", (memo_id_2,))
            order2 = cursor.fetchone()

            if order1 is not None and order2 is not None:
                cursor.execute("UPDATE memos SET sort_order = ? WHERE id = ?", (order2[0], memo_id_1))
                cursor.execute("UPDATE memos SET sort_order = ? WHERE id = ?", (order1[0], memo_id_2))

    def get_all_categories(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM memos ORDER BY category")
            return [row[0] for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
