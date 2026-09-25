"""
employees テーブルへのアクセスを担当するモジュール。
"""

from database import get_conn


def get_employee(employee_id=1):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM employees WHERE id = ?", (employee_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "department": row[2],
        "role": row[3],
        "skills": [x.strip() for x in row[4].split(",") if x.strip()],
    }
