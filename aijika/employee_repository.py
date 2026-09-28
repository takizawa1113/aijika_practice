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


def update_employee(employee_id, name, department, skills):
    """
    社員情報を更新する。

    employee_id: 更新対象の社員ID
    name: 社員名
    department: 所属部署
    skills: カンマ区切りのスキル文字列
    """

    conn = get_conn()

    conn.execute(
        """
        UPDATE employees
        SET name = ?,
            department = ?,
            skills = ?
        WHERE id = ?
        """,
        (
            name,
            department,
            skills,
            employee_id,
        ),
    )

    conn.commit()
    conn.close()