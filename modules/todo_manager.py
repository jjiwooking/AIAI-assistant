import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assistant.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,title TEXT NOT NULL,due_date TEXT,priority TEXT DEFAULT '보통',completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    c.execute("PRAGMA table_info(todos)")
    columns = [row[1] for row in c.fetchall()]
    if "user_id" not in columns:
        c.execute("ALTER TABLE todos ADD COLUMN user_id TEXT")
        c.execute("UPDATE todos SET user_id='legacy' WHERE user_id IS NULL")
    conn.commit()
    conn.close()

def add_todo(user_id, title, due_date="", priority="보통"):
    if not title.strip():
        return "⚠️ 할 일을 입력해주세요."
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO todos (user_id,title,due_date,priority) VALUES (?,?,?,?)",(user_id,title.strip(),due_date.strip(),priority))
    conn.commit()
    conn.close()
    return f"✅ '{title}' 추가 완료!"

def get_todos(user_id, show_completed=False):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if show_completed:
        c.execute("SELECT id,title,due_date,priority,completed FROM todos WHERE user_id=? ORDER BY completed,created_at DESC",(user_id,))
    else:
        c.execute("SELECT id,title,due_date,priority,completed FROM todos WHERE user_id=? AND completed=0 ORDER BY created_at DESC",(user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def complete_todo(user_id, todo_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("UPDATE todos SET completed=1 WHERE id=? AND user_id=?",(int(todo_id),user_id))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    if rowcount == 0:
        return "⚠️ 해당 할 일을 찾을 수 없습니다."
    return f"✅ ID {int(todo_id)} 완료 처리!"

def delete_todo(user_id, todo_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("DELETE FROM todos WHERE id=? AND user_id=?",(int(todo_id),user_id))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    if rowcount == 0:
        return "⚠️ 해당 할 일을 찾을 수 없습니다."
    return f"🗑️ ID {int(todo_id)} 삭제 완료!"
