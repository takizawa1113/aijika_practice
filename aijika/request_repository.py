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
        SELECT id, department, title, description, request_date,
               start_time, end_time, required_hours, people_needed,
               skills, status
        FROM support_requests
        ORDER BY request_date, start_time
        """,
        conn,
    )
    conn.close()
    return df


def insert_request(
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
        (department,title,description,request_date,start_time,end_time,
         required_hours,people_needed,skills,status)
        VALUES (?,?,?,?,?,?,?,?,?,?)
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
            status,
        ),
    )
    conn.commit()
    conn.close()
