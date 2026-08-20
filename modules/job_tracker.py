import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assistant.db")

def init_job_db():
    """채용 테이블 초기화"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            company    TEXT NOT NULL,
            position   TEXT NOT NULL,
            status     TEXT DEFAULT '지원 예정',
            deadline   TEXT,
            notes      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_job(company: str, position: str, status: str = "지원 예정",
            deadline: str = "", notes: str = "") -> str:
    if not company.strip() or not position.strip():
        return "⚠️ 기업명과 직무를 입력해주세요."
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO jobs (company, position, status, deadline, notes) VALUES (?, ?, ?, ?, ?)",
        (company.strip(), position.strip(), status, deadline.strip(), notes.strip())
    )
    conn.commit()
    conn.close()
    return f"✅ {company} - {position} 추가 완료!"

def get_jobs() -> list:
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, company, position, status, deadline, notes FROM jobs ORDER BY deadline, company")
    rows = c.fetchall()
    conn.close()
    return rows

def update_job_status(job_id, status: str) -> str:
    if not job_id:
        return "⚠️ ID를 입력해주세요."
    init_job_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, int(job_id)))
    conn.commit()
    conn.close()
    return f"✅ ID {int(job_id)} 상태를 '{status}'로 변경!"
