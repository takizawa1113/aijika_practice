"""
free_times テーブルへのアクセスを担当するモジュール。

「余白時間を登録」「カレンダー」「マイページ」の各画面から利用される。
"""

import pandas as pd

from database import get_conn


def get_free_times(employee_id=1):
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, free_date, start_time, end_time, skills, preference, created_at
        FROM free_times
        WHERE employee_id = ?
        ORDER BY free_date, start_time
        """,
        conn,
        params=(employee_id,),
    )
    conn.close()
    return df


def insert_free_time(employee_id, free_date, start_time, end_time, skills, preference, created_at):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO free_times
        (employee_id, free_date, start_time, end_time, skills, preference, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (employee_id, free_date, start_time, end_time, skills, preference, created_at),
    )
    conn.commit()
    conn.close()
