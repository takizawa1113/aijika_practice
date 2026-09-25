"""
DB接続とスキーマ定義・初期データ投入を担当するモジュール。

テーブル構成を変える人だけがここを触ればよい構成にしてある。
データの「取得・登録」ロジックは *_repository.py 側に置き、
このファイルは「テーブルを用意する」ことだけに責任を持つ。
"""

import sqlite3
from datetime import date, timedelta

from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT,
            skills TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            request_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            required_hours REAL NOT NULL,
            people_needed INTEGER NOT NULL,
            skills TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '募集中'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS free_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            free_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            skills TEXT,
            preference TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            free_time_id INTEGER NOT NULL,
            request_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT '応募済'
        )
        """
    )

    _seed_employees(cur)
    _seed_requests(cur)

    conn.commit()
    conn.close()


def _seed_employees(cur):
    """初回起動時だけサンプル社員データを登録する。"""
    count = cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if count != 0:
        return

    employees = [
        (1, "山田 太郎", "営業部", "主任", "Excel,データ集計,資料作成"),
        (2, "佐藤 花子", "経理部", "担当", "Excel,データ集計,経理"),
        (3, "鈴木 一郎", "システム部", "担当", "Python,Excel,資料作成"),
        (4, "田中 美咲", "人事部", "担当", "Excel,アンケート集計,資料作成"),
    ]
    cur.executemany(
        "INSERT INTO employees (id,name,department,role,skills) VALUES (?,?,?,?,?)",
        employees,
    )


def _seed_requests(cur):
    """初回起動時だけサンプル支援依頼データを登録する。"""
    count = cur.execute("SELECT COUNT(*) FROM support_requests").fetchone()[0]
    if count != 0:
        return

    base = date.today()
    requests = [
        (
            "営業部",
            "営業部のデータチェック",
            "営業リストのデータ確認・整形をお願いします。",
            (base + timedelta(days=1)).isoformat(),
            "13:00",
            "17:00",
            2.0,
            2,
            "Excel,データ集計",
            "募集中",
        ),
        (
            "企画部",
            "社内向け資料の作成補助",
            "新サービスの社内向け説明資料の作成補助です。",
            (base + timedelta(days=2)).isoformat(),
            "09:00",
            "12:00",
            3.0,
            1,
            "PowerPoint,資料作成",
            "募集中",
        ),
        (
            "経理部",
            "データ集計（Excel）",
            "月次データの集計・チェックをお願いします。",
            (base + timedelta(days=3)).isoformat(),
            "10:00",
            "15:00",
            3.0,
            1,
            "Excel,データ集計",
            "募集中",
        ),
        (
            "システム部",
            "FAQ更新作業",
            "社内FAQの内容確認と更新作業です。",
            (base + timedelta(days=4)).isoformat(),
            "13:00",
            "16:00",
            2.0,
            1,
            "資料作成,Excel",
            "募集中",
        ),
        (
            "人事部",
            "アンケート集計",
            "社員アンケートの集計をお願いします。",
            (base + timedelta(days=5)).isoformat(),
            "09:00",
            "12:00",
            2.0,
            1,
            "Excel,アンケート集計",
            "募集中",
        ),
    ]
    cur.executemany(
        """
        INSERT INTO support_requests
        (department,title,description,request_date,start_time,end_time,
         required_hours,people_needed,skills,status)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        requests,
    )
