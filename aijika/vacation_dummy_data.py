"""
休暇レコメンド機能で使うダミーデータ（デモ用）。

本番では「勤怠システムの有給残」「チームの休暇予定表」「会社カレンダー」
などから取得する想定の情報を、ここではハードコードしている。
本物に差し替えるときは、このファイルの関数の中身だけを置き換えれば
vacation_recommender.py / vacation_widget.py 側は変更不要。
"""

from datetime import date, timedelta

# ------------------------------------------------------------
# 祝日（デモ用。2026年度分）
# ------------------------------------------------------------
HOLIDAYS = {
    date(2026, 4, 29): "昭和の日",
    date(2026, 5, 3): "憲法記念日",
    date(2026, 5, 4): "みどりの日",
    date(2026, 5, 5): "こどもの日",
    date(2026, 5, 6): "振替休日",
    date(2026, 7, 20): "海の日",
    date(2026, 8, 11): "山の日",
    date(2026, 9, 21): "敬老の日",
    date(2026, 9, 22): "国民の休日",
    date(2026, 9, 23): "秋分の日",
    date(2026, 10, 12): "スポーツの日",
    date(2026, 11, 3): "文化の日",
    date(2026, 11, 23): "勤労感謝の日",
    date(2027, 1, 1): "元日",
    date(2027, 1, 11): "成人の日",
    date(2027, 2, 11): "建国記念の日",
    date(2027, 2, 23): "天皇誕生日",
    date(2027, 3, 22): "振替休日",
}


def get_holidays():
    return HOLIDAYS


# ------------------------------------------------------------
# 有給休暇の残日数（社員ID → 情報）
# ------------------------------------------------------------
_LEAVE_BALANCES = {
    1: {"granted": 20, "carried_over": 6, "used": 2.5},
    2: {"granted": 18, "carried_over": 10, "used": 7.0},
    3: {"granted": 14, "carried_over": 0, "used": 1.0},
    4: {"granted": 16, "carried_over": 4, "used": 4.5},
}


def get_leave_balance(employee_id):
    b = _LEAVE_BALANCES.get(employee_id, {"granted": 10, "carried_over": 0, "used": 0})
    return {**b, "remaining": b["granted"] + b["carried_over"] - b["used"]}


# ------------------------------------------------------------
# 同じ部署のメンバーの休暇予定
# 日付は「今日から何日後か」で持ち、デモをいつ開いても近い日付に出るようにする。
# ------------------------------------------------------------
_TEAM_LEAVE_PLANS = [
    # (部署, 名前, 今日からの日数, 種別)
    ("営業部", "伊藤 健", 1, "全休"),
    ("営業部", "高橋 さくら", 1, "午後半休"),
    ("営業部", "渡辺 翔", 3, "全休"),
    ("営業部", "伊藤 健", 8, "午前半休"),
    ("経理部", "中村 由美", 2, "全休"),
    ("経理部", "小林 大輔", 2, "全休"),
    ("システム部", "加藤 陽介", 4, "全休"),
    ("人事部", "吉田 恵", 5, "午後半休"),
]


def get_team_leave_plans(today=None):
    today = today or date.today()
    return [
        {"department": dept, "name": name, "date": today + timedelta(days=d), "type": t}
        for dept, name, d, t in _TEAM_LEAVE_PLANS
    ]


# ------------------------------------------------------------
# 余白時間の過ごし方カタログ
# category は config.PREFERENCE_OPTIONS の「休暇 / 自己研鑽 / レジャー」に対応。
# skill を持つものは「応援依頼で需要があるのに自分が持っていないスキル」と
# 一致したときに優先表示する。
# ------------------------------------------------------------
ACTIVITY_CATALOG = [
    # 休暇（しっかり休む）
    {"category": "休暇", "icon": "☕", "title": "早めに上がってカフェで読書", "min_h": 1, "max_h": 3},
    {"category": "休暇", "icon": "🏥", "title": "平日しか行けない用事（銀行・役所・通院）", "min_h": 1, "max_h": 4},
    {"category": "休暇", "icon": "🛌", "title": "家でゆっくり休む", "min_h": 3, "max_h": 24},
    {"category": "休暇", "icon": "👨‍👩‍👧", "title": "家族との時間・子どもの送り迎え", "min_h": 2, "max_h": 24},
    # レジャー
    {"category": "レジャー", "icon": "🏋️", "title": "空いている平日昼のジム・プール", "min_h": 1, "max_h": 3},
    {"category": "レジャー", "icon": "♨️", "title": "日帰り温泉（平日は空いていておすすめ）", "min_h": 4, "max_h": 24},
    {"category": "レジャー", "icon": "🎬", "title": "平日昼の映画館", "min_h": 2, "max_h": 5},
    {"category": "レジャー", "icon": "🧳", "title": "連休にして1泊旅行", "min_h": 8, "max_h": 99},
    # 自己研鑽（スキルと紐づく講座）
    {"category": "自己研鑽", "icon": "📊", "title": "Excel ピボット・関数 実践講座", "min_h": 1, "max_h": 3, "skill": "Excel"},
    {"category": "自己研鑽", "icon": "🔢", "title": "データ集計の基本（集計設計とチェック方法）", "min_h": 2, "max_h": 4, "skill": "データ集計"},
    {"category": "自己研鑽", "icon": "📝", "title": "伝わる資料作成の型 e-learning", "min_h": 1, "max_h": 3, "skill": "資料作成"},
    {"category": "自己研鑽", "icon": "🖼️", "title": "PowerPoint スライドデザイン講座", "min_h": 2, "max_h": 4, "skill": "PowerPoint"},
    {"category": "自己研鑽", "icon": "🐍", "title": "Python入門（業務自動化ハンズオン）", "min_h": 3, "max_h": 8, "skill": "Python"},
    {"category": "自己研鑽", "icon": "📋", "title": "アンケート設計・集計のコツ", "min_h": 1, "max_h": 3, "skill": "アンケート集計"},
    {"category": "自己研鑽", "icon": "📚", "title": "業界ニュース・専門書のインプット", "min_h": 1, "max_h": 4},
]


def get_activity_catalog():
    return ACTIVITY_CATALOG
