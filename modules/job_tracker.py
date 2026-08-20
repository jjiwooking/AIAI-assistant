import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assistant.db")

def init_job_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,company TEXT NOT NULL,position TEXT NOT NULL,status TEXT DEFAULT '지원 예정',deadline TEXT,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    c.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in c.fetchall()]
    if "user_id" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT")
        c.execute("UPDATE jobs SET user_id='legacy' WHERE user_id IS NULL")
    conn.commit()
    conn.close()

def add_job(user_id, company, position, status="지원 예정", deadline="", notes=""):
    if not company.strip() or not position.strip():
        return "⚠️ 기업명과 직무를 입력해주세요."
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO jobs (user_id,company,position,status,deadline,notes) VALUES (?,?,?,?,?,?)",(user_id,company.strip(),position.strip(),status,deadline.strip(),notes.strip()))
    conn.commit()
    conn.close()
    return f"✅ {company} - {position} 추가 완료!"

def get_jobs(user_id):
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,company,position,status,deadline,notes FROM jobs WHERE user_id=? ORDER BY created_at DESC",(user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_job_status(user_id, job_id, status):
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("UPDATE jobs SET status=? WHERE id=? AND user_id=?",(status,int(job_id),user_id))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    if rowcount == 0:
        return "⚠️ 해당 채용 정보를 찾을 수 없습니다."
    return f"✅ ID {int(job_id)} 상태를 '{status}'로 변경!"
