import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assistant.db")

def init_db():
    """DB 초기화 및 테이블 생성"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT    NOT NULL,
            due_date  TEXT,
            priority  TEXT    DEFAULT '보통',
            completed INTEGER DEFAULT 0,
            created_at TEXT   DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_todo(title: str, due_date: str = "", priority: str = "보통") -> str:
    if not title.strip():
        return "⚠️ 할 일을 입력해주세요."
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO todos (title, due_date, priority) VALUES (?, ?, ?)",
        (title.strip(), due_date.strip(), priority)
    )
    conn.commit()
    conn.close()
    return f"✅ '{title}' 추가 완료!"

def get_todos(show_completed: bool = False) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if show_completed:
        c.execute("SELECT id, title, due_date, priority, completed FROM todos ORDER BY completed, priority DESC, due_date")
    else:
        c.execute("SELECT id, title, due_date, priority, completed FROM todos WHERE completed=0 ORDER BY priority DESC, due_date")
    rows = c.fetchall()
    conn.close()
    return rows

def complete_todo(todo_id) -> str:
    if not todo_id:
        return "⚠️ ID를 입력해주세요."
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE todos SET completed=1 WHERE id=?", (int(todo_id),))
    conn.commit()
    conn.close()
    return f"✅ ID {int(todo_id)} 완료 처리!"

def delete_todo(todo_id) -> str:
    if not todo_id:
        return "⚠️ ID를 입력해주세요."
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM todos WHERE id=?", (int(todo_id),))
    conn.commit()
    conn.close()
    return f"🗑️ ID {int(todo_id)} 삭제 완료!"
