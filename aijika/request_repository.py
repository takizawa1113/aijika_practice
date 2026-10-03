"""
support_requests テーブルへのアクセスを担当するモジュール。

「支援を探す」「支援を依頼する」「ホーム」の各画面から利用される。
検索条件の絞り込みなどはここではなく views 側で行い、
このファイルは取得・登録のみに責任を持つ。
"""

import pandas as pd

from database import get_conn


def get_requests():
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, employee_id, department, title, description, request_date,
               start_time, end_time, required_hours, people_needed,
               skills, status
        FROM support_requests
        ORDER BY request_date, start_time
        """,
        conn,
    )
    conn.close()
    return df


def get_my_requests(employee_id):
    """指定した社員が登録した支援依頼だけ取得する。"""

    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT id, employee_id, department, title, description, request_date,
               start_time, end_time, required_hours, people_needed,
               skills, status
        FROM support_requests
        WHERE employee_id = ?
        ORDER BY request_date, start_time
        """,
        conn,
        params=(employee_id,),
    )

    conn.close()
    return df


def insert_request(
    employee_id,
    department,
    title,
    description,
    request_date,
    start_time,
    end_time,
    required_hours,
    people_needed,
    skills,
    status="募集中",
):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO support_requests
        (employee_id,department,title,description,request_date,start_time,end_time,
         required_hours,people_needed,skills,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            employee_id,
            department,
            title,
            description,
            request_date,
            start_time,
            end_time,
            required_hours,
            people_needed,
            skills,
            status,
        ),
    )
    conn.commit()
    conn.close()


def update_request(
    request_id,
    employee_id,
    department,
    title,
    description,
    request_date,
    start_time,
    end_time,
    required_hours,
    people_needed,
    skills,
):
    """指定した社員が登録した支援依頼だけ更新する。"""

    conn = get_conn()

    cur = conn.execute(
        """
        UPDATE support_requests
        SET department = ?,
            title = ?,
            description = ?,
            request_date = ?,
            start_time = ?,
            end_time = ?,
            required_hours = ?,
            people_needed = ?,
            skills = ?
        WHERE id = ?
          AND employee_id = ?
        """,
        (
            department,
            title,
            description,
            request_date,
            start_time,
            end_time,
            required_hours,
            people_needed,
            skills,
            request_id,
            employee_id,
        ),
    )

    conn.commit()
    conn.close()

    return cur.rowcount > 0


def delete_request(request_id, employee_id):
    """指定した社員が登録した支援依頼だけ削除する。"""

    conn = get_conn()

    cur = conn.execute(
        """
        DELETE FROM support_requests
        WHERE id = ?
          AND employee_id = ?
        """,
        (request_id, employee_id),
    )

    conn.commit()
    conn.close()

    return cur.rowcount > 0