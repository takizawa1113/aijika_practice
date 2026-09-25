"""
マッチングスコアの計算・おすすめ抽出を担当するモジュール。

このファイルはDBやStreamlitに依存しない「純粋なロジック」に保つ。
（引数として DataFrame や employee dict を受け取るだけにする）
こうしておくと、画面側の変更とロジック側の変更が衝突しにくく、
将来的に単体テストも書きやすい。
"""

from datetime import date, datetime

import pandas as pd

from config import MATCH_SCORE_THRESHOLD


def parse_time(t):
    return datetime.strptime(t, "%H:%M").time()


def hours_between(start, end):
    dt1 = datetime.combine(date.today(), start)
    dt2 = datetime.combine(date.today(), end)
    return max(0, (dt2 - dt1).total_seconds() / 3600)


def calculate_score(employee_skills, free_start, free_end, req):
    score = 0

    # 時間適合
    fs = parse_time(free_start)
    fe = parse_time(free_end)
    rs = parse_time(req["start_time"])
    re_ = parse_time(req["end_time"])

    overlap_start = max(fs, rs)
    overlap_end = min(fe, re_)
    overlap_hours = hours_between(overlap_start, overlap_end)

    if overlap_hours >= req["required_hours"]:
        score += 50
    elif overlap_hours >= 2:
        score += 30
    elif overlap_hours > 0:
        score += 15

    # スキル適合
    employee_skill_set = {s.strip().lower() for s in employee_skills}
    required_skill_set = {
        s.strip().lower() for s in req["skills"].split(",") if s.strip()
    }
    if required_skill_set:
        matched = employee_skill_set & required_skill_set
        skill_ratio = len(matched) / len(required_skill_set)
        score += round(skill_ratio * 40)

    # 業務時間に余裕があることを少し加点
    free_hours = hours_between(fs, fe)
    if free_hours >= req["required_hours"]:
        score += 10

    return min(score, 100)


def make_recommendations(employee, free_date, free_start, free_end, requests_df):
    """
    requests_df（support_requests の DataFrame）の中から、
    指定した余白時間に合う支援依頼をスコア順に返す。

    DB取得は呼び出し側（views）で行い、ここでは受け取った
    DataFrame に対する計算だけを行う。
    """
    if requests_df.empty:
        return requests_df.iloc[0:0]

    candidates = []
    for _, req in requests_df.iterrows():
        if req["status"] != "募集中":
            continue
        if req["request_date"] != free_date.isoformat():
            continue

        score = calculate_score(employee["skills"], free_start, free_end, req)

        if score >= MATCH_SCORE_THRESHOLD:
            matched_skills = [
                s for s in req["skills"].split(",")
                if s.strip().lower() in {x.lower() for x in employee["skills"]}
            ]
            reason = []
            if matched_skills:
                reason.append("スキルが一致")
            if score >= 50:
                reason.append("時間帯が適合")
            if not reason:
                reason.append("条件が比較的近い")

            candidates.append(
                {
                    "id": int(req["id"]),
                    "department": req["department"],
                    "title": req["title"],
                    "description": req["description"],
                    "start_time": req["start_time"],
                    "end_time": req["end_time"],
                    "skills": req["skills"],
                    "score": score,
                    "reason": "・".join(reason),
                }
            )

    result = pd.DataFrame(candidates)
    if not result.empty:
        result = result.sort_values("score", ascending=False)
    return result
