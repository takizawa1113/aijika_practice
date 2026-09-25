"""
applications テーブルへのアクセスを担当するモジュール。

「余白時間」と「支援依頼」を結びつける応募情報を扱う。
"""

from database import get_conn


def apply_to_request(free_time_id, request_id):
    """
    指定した余白時間で支援依頼に応募する。
    既に同じ組み合わせで応募済みの場合は何もせず False を返す。
    """
    conn = get_conn()
    exists = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE free_time_id = ? AND request_id = ?
        """,
        (free_time_id, request_id),
    ).fetchone()[0]

    if exists == 0:
        conn.execute(
            """
            INSERT INTO applications (free_time_id, request_id, status)
            VALUES (?, ?, '応募済')
            """,
            (free_time_id, request_id),
        )
        conn.commit()
        result = True
    else:
        result = False

    conn.close()
    return result
