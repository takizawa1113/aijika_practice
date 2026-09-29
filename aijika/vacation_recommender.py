"""
休暇レコメンドのロジック。

matching.py と同じく、DB や Streamlit に依存しない「純粋な関数」だけを置く。
データ（祝日・有給残・チームの休暇予定・過ごし方カタログ）はすべて引数で受け取る。
"""

from collections import Counter
from datetime import date, time, timedelta

from config import WORK_END_TIME, WORK_START_TIME

LUNCH_START = time(12, 0)
LUNCH_END = time(13, 0)
MANDATORY_LEAVE_DAYS = 5  # 年5日の有給取得義務
WEEKDAY_JA = "月火水木金土日"


def _minutes(t):
    return t.hour * 60 + t.minute


def work_hours_in(start, end):
    """勤務時間内・昼休みを除いた時間数。"""
    s = max(_minutes(start), _minutes(WORK_START_TIME))
    e = min(_minutes(end), _minutes(WORK_END_TIME))
    if e <= s:
        return 0.0
    lunch = max(0, min(e, _minutes(LUNCH_END)) - max(s, _minutes(LUNCH_START)))
    return (e - s - lunch) / 60


def fmt_date(d):
    return f"{d.month}/{d.day}（{WEEKDAY_JA[d.weekday()]}）"


# ------------------------------------------------------------
# 1. 休暇の取り方（全休・半休・時間休）
# ------------------------------------------------------------
def classify_leave(start, end):
    """
    空き時間帯から、おすすめの休暇の取り方を判定する。
    戻り値: {"type": str, "days": float, "hours": float, "reaches_end": bool, "from_start": bool}
    days は有給の消化日数（時間休は 1日=8時間 で換算）。
    """
    from_start = start <= WORK_START_TIME
    reaches_end = end >= WORK_END_TIME
    hours = work_hours_in(start, end)

    if from_start and reaches_end:
        return {"type": "全休", "days": 1.0, "hours": hours, "reaches_end": True, "from_start": True}
    if reaches_end and start <= LUNCH_END:
        return {"type": "午後半休", "days": 0.5, "hours": hours, "reaches_end": True, "from_start": False}
    if from_start and end >= LUNCH_START:
        return {"type": "午前半休", "days": 0.5, "hours": hours, "reaches_end": False, "from_start": True}

    rounded = max(1, round(hours))
    if reaches_end:
        label = f"時間休 {rounded}時間（早上がり）"
    elif from_start:
        label = f"時間休 {rounded}時間（遅めの出社）"
    else:
        label = f"時間休 {rounded}時間（中抜け）"
    return {"type": label, "days": rounded / 8, "hours": hours, "reaches_end": reaches_end, "from_start": from_start}


# ------------------------------------------------------------
# 2. 連休になるか
# ------------------------------------------------------------
def is_day_off(d, holidays):
    return d.weekday() >= 5 or d in holidays


def long_weekend_info(free_date, leave, holidays):
    """
    休暇を取ると前後の土日・祝日とつながって何連休になるかを返す。
    戻り値: {"days": float, "label": str} つながらない場合は days=0。
    """
    after = 0
    if leave["reaches_end"]:
        d = free_date + timedelta(days=1)
        while is_day_off(d, holidays):
            after += 1
            d += timedelta(days=1)

    before = 0
    if leave["from_start"]:
        d = free_date - timedelta(days=1)
        while is_day_off(d, holidays):
            before += 1
            d -= timedelta(days=1)

    if after == 0 and before == 0:
        return {"days": 0, "label": ""}

    if leave["type"] == "全休":
        total = before + 1 + after
        return {"days": total, "label": f"{total}連休"}

    # 半休・時間休は「半日ぶん」をおまけとして 0.5 で表現
    total = before + after + 0.5
    names = [holidays[free_date + timedelta(days=i)] for i in range(1, after + 1)
             if (free_date + timedelta(days=i)) in holidays]
    extra = f"（{'・'.join(names)}を含む）" if names else ""
    return {"days": total, "label": f"{total:g}連休{extra}"}


# ------------------------------------------------------------
# 3. チームの休暇予定との重なり
# ------------------------------------------------------------
def team_conflicts(department, target_date, team_plans):
    return [p for p in team_plans if p["department"] == department and p["date"] == target_date]


def rank_leave_days(department, start_from, team_plans, holidays, leave_type="全休", days=14, top_n=3):
    """
    今後 days 日間の平日から「休みやすい日」を点数づけして上位を返す。
    ・連休につながる日を加点
    ・同じ部署で休む人が多い日を減点
    """
    reaches_end = leave_type in ("全休", "午後半休") or "早上がり" in leave_type
    from_start = leave_type in ("全休", "午前半休") or "遅めの出社" in leave_type
    probe = {"type": leave_type, "reaches_end": reaches_end, "from_start": from_start}

    candidates = []
    for i in range(days):
        d = start_from + timedelta(days=i)
        if is_day_off(d, holidays):
            continue
        conflicts = team_conflicts(department, d, team_plans)
        lw = long_weekend_info(d, probe, holidays)
        score = 50 + lw["days"] * 10 - len(conflicts) * 25
        reasons = []
        if lw["days"]:
            reasons.append(f"🎌 {lw['label']}になる")
        if conflicts:
            reasons.append(f"⚠️ 部署で{len(conflicts)}名が休み予定")
        else:
            reasons.append("✅ 部署の休みと重ならない")
        candidates.append({"date": d, "score": score, "reasons": reasons})

    candidates.sort(key=lambda c: (-c["score"], c["date"]))
    return candidates[:top_n]


# ------------------------------------------------------------
# 4. 有給の取得状況（年5日の義務）
# ------------------------------------------------------------
def fiscal_year_end(today):
    year = today.year if today.month <= 3 else today.year + 1
    return date(year, 3, 31)


def leave_obligation_status(balance, today):
    fy_end = fiscal_year_end(today)
    months_left = max(1, (fy_end.year - today.year) * 12 + fy_end.month - today.month + 1)
    shortfall = max(0.0, MANDATORY_LEAVE_DAYS - balance["used"])
    if shortfall == 0:
        message = f"年{MANDATORY_LEAVE_DAYS}日の取得義務はクリア済み。残り{balance['remaining']:g}日を計画的に使いましょう。"
    else:
        pace = months_left / shortfall
        message = (
            f"年{MANDATORY_LEAVE_DAYS}日の取得義務まであと{shortfall:g}日。"
            f"年度末まで{months_left}ヶ月なので、{pace:.1f}ヶ月に1日ペースで取得が必要です。"
        )
    return {"shortfall": shortfall, "months_left": months_left, "message": message}


# ------------------------------------------------------------
# 5. 過ごし方のおすすめ（自己研鑽はスキル需要と連動）
# ------------------------------------------------------------
def skill_demand_gap(employee_skills, requests_df):
    """
    募集中の支援依頼で求められているのに、本人が持っていないスキルを
    需要の多い順に返す。 [(skill, 件数), ...]
    """
    if requests_df is None or requests_df.empty:
        return []
    owned = {s.strip().lower() for s in employee_skills}
    counter = Counter()
    for skills in requests_df[requests_df["status"] == "募集中"]["skills"]:
        for s in str(skills).split(","):
            s = s.strip()
            if s and s.lower() not in owned:
                counter[s] += 1
    return counter.most_common()


def recommend_activities(hours, preferences, gap_skills, catalog, per_category=2):
    """
    空き時間の長さと「希望する過ごし方」から、カテゴリごとに過ごし方を選ぶ。
    戻り値: {"休暇": [...], "自己研鑽": [...], "レジャー": [...]}
    """
    categories = [c for c in ("休暇", "自己研鑽", "レジャー") if c in preferences]
    if not categories:  # 「他部署支援」だけ選んでいた場合などは全カテゴリを出す
        categories = ["休暇", "自己研鑽", "レジャー"]

    gap_rank = {s: i for i, (s, _) in enumerate(gap_skills)}
    gap_count = dict(gap_skills)
    result = {}
    for cat in categories:
        items = [a for a in catalog if a["category"] == cat and a["min_h"] <= hours <= a["max_h"]]
        if not items:  # 時間が合うものが無ければ短めのものを出す
            items = sorted((a for a in catalog if a["category"] == cat), key=lambda a: a["min_h"])[:per_category]

        enriched = []
        for a in items:
            a = dict(a)
            skill = a.get("skill")
            if skill in gap_rank:
                a["note"] = f"応援依頼で需要あり（{gap_count[skill]}件）→ 次はマッチしやすくなります"
            enriched.append(a)
        enriched.sort(key=lambda a: gap_rank.get(a.get("skill"), 99))
        result[cat] = enriched[:per_category]
    return result


# ------------------------------------------------------------
# 6. 休暇申請の文面
# ------------------------------------------------------------
def build_leave_request_text(employee, free_date, start, end, leave):
    period = "終日" if leave["type"] == "全休" else f"{start.strftime('%H:%M')}～{end.strftime('%H:%M')}"
    return (
        f"お疲れさまです。{employee['name']}です。\n"
        f"{fmt_date(free_date)} {period} に{leave['type'].split('（')[0]}を取得させてください。\n"
        f"当日は自分のスキルに合う他部署支援の募集もなく、業務への影響はない見込みです。\n"
        f"よろしくお願いいたします。"
    )
