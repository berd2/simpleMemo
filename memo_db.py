import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Any

logger = logging.getLogger(__name__)

class MemoDB:
    def __init__(self, db_path: str = 'nemo_memo.db') -> None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """데이터베이스 연결을 초기화하고 권한 문제를 처리합니다."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.create_table()
            self.create_state_table()
            self._migrate_schema()
            logger.info(f"메모 데이터베이스 초기화 완료: {self.db_path}")
        except (sqlite3.Error, PermissionError, OSError) as e:
            logger.error(f"메모 데이터베이스 초기화 실패: {e}")
            # 메모리 데이터베이스로 폴백
            try:
                self.conn = sqlite3.connect(":memory:")
                self.create_table()
                self.create_state_table()
                logger.warning("메모리 데이터베이스로 폴백했습니다. 데이터는 프로그램 종료 시 사라집니다.")
            except Exception as fallback_error:
                logger.error(f"메모리 데이터베이스 생성도 실패: {fallback_error}")
                self.conn = None

    def _execute_safe(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """안전한 데이터베이스 실행 래퍼"""
        if not self.conn:
            logger.error("데이터베이스 연결이 없습니다.")
            return None if fetch_one else [] if fetch_all else None
            
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.lastrowid
        except (sqlite3.Error, PermissionError) as e:
            logger.error(f"데이터베이스 쿼리 실행 실패: {e}")
            return None if fetch_one else [] if fetch_all else None

    def create_state_table(self) -> None:
        """상태 저장 테이블을 생성합니다."""
        self._execute_safe("CREATE TABLE IF NOT EXISTS notepad_state (key TEXT PRIMARY KEY, value TEXT)")

    def save_state(self, key: str, value: str) -> None:
        """상태를 저장합니다."""
        self._execute_safe("INSERT OR REPLACE INTO notepad_state (key, value) VALUES (?, ?)", (key, str(value)))

    def load_state(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """상태를 로드합니다."""
        result = self._execute_safe("SELECT value FROM notepad_state WHERE key = ?", (key,), fetch_one=True)
        return result[0] if result else default

    def create_table(self) -> None:
        """메모 테이블을 생성합니다."""
        self._execute_safe("""
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

    def _migrate_schema(self) -> None:
        """스키마 마이그레이션을 수행합니다."""
        if not self.conn:
            return
            
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA table_info(memos)")
                columns = [info[1] for info in cursor.fetchall()]

                # Check if migration is needed by looking for a column that was removed.
                if 'importance_timestamp' in columns:
                    logger.info("스키마 마이그레이션이 필요합니다. 마이그레이션을 시작합니다...")
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
                    logger.info("스키마 마이그레이션이 완료되었습니다.")

                # Migration to add sort_order if it's missing from a previous version
                if 'sort_order' not in columns:
                    cursor.execute("ALTER TABLE memos ADD COLUMN sort_order INTEGER")
                    cursor.execute("UPDATE memos SET sort_order = id WHERE sort_order IS NULL")
        except Exception as e:
            logger.error(f"스키마 마이그레이션 실패: {e}")

    def get_all_memos(self) -> List[Tuple[Any, ...]]:
        """모든 메모를 가져옵니다."""
        result = self._execute_safe(
            "SELECT id, title, created_at, content, is_important, category, sort_order FROM memos ORDER BY is_important DESC, sort_order DESC",
            fetch_all=True
        )
        return result or []

    def get_memo_by_id(self, memo_id: int) -> Optional[Tuple[Any, ...]]:
        """ID로 메모를 가져옵니다."""
        return self._execute_safe(
            "SELECT id, title, created_at, content, is_important, category, sort_order FROM memos WHERE id = ?",
            (memo_id,),
            fetch_one=True
        )

    def add_memo(self, title: str, content: str, category: str = '', is_important: int = 0) -> Optional[int]:
        """새 메모를 추가합니다."""
        now_ts = int(datetime.now().timestamp())
        return self._execute_safe(
            "INSERT INTO memos (title, created_at, content, is_important, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
            (title, now_ts, content, is_important, category, now_ts)
        )

    def update_memo(self, memo_id: int, title: str, content: str) -> None:
        """메모를 업데이트합니다."""
        self._execute_safe(
            "UPDATE memos SET title = ?, content = ? WHERE id = ?",
            (title, content, memo_id)
        )

    def update_memo_importance(self, memo_id: int, is_important: bool) -> None:
        """메모의 중요도를 업데이트합니다."""
        self._execute_safe(
            "UPDATE memos SET is_important = ? WHERE id = ?",
            (1 if is_important else 0, memo_id)
        )

    def delete_memo(self, memo_id: int) -> None:
        """메모를 삭제합니다."""
        self._execute_safe("DELETE FROM memos WHERE id = ?", (memo_id,))

    def restore_memo(self, memo_id: int, title: str, created_at: int, content: str, 
                    is_important: int, category: str, sort_order: int) -> None:
        """삭제된 메모를 복원합니다."""
        self._execute_safe(
            """INSERT OR REPLACE INTO memos
               (id, title, created_at, content, is_important, category, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (memo_id, title, created_at, content, is_important, category, sort_order)
        )

    def swap_memo_order(self, memo_id_1: int, memo_id_2: int) -> None:
        """두 메모의 순서를 바꿉니다."""
        if not self.conn:
            return
            
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT sort_order FROM memos WHERE id = ?", (memo_id_1,))
                order1 = cursor.fetchone()
                cursor.execute("SELECT sort_order FROM memos WHERE id = ?", (memo_id_2,))
                order2 = cursor.fetchone()

                if order1 is not None and order2 is not None:
                    cursor.execute("UPDATE memos SET sort_order = ? WHERE id = ?", (order2[0], memo_id_1))
                    cursor.execute("UPDATE memos SET sort_order = ? WHERE id = ?", (order1[0], memo_id_2))
        except Exception as e:
            logger.error(f"메모 순서 변경 실패: {e}")

    def get_all_categories(self) -> List[str]:
        """모든 카테고리를 가져옵니다."""
        result = self._execute_safe("SELECT DISTINCT category FROM memos ORDER BY category", fetch_all=True)
        return [row[0] for row in result] if result else []

    def close(self) -> None:
        """데이터베이스 연결을 닫습니다."""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
            except Exception as e:
                logger.error(f"데이터베이스 연결 종료 실패: {e}")
