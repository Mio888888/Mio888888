#!/usr/bin/env python3
"""自动更新 GitHub 个人主页 README 的统计数据"""

import os
import re
import json
import base64
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# 配置
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "Mio888888")
WAKATIME_API_KEY = os.environ.get("WAKATIME_API_KEY")
README_PATH = os.environ.get("README_PATH", "README.md")
TZ_OFFSET = int(os.environ.get("TZ_OFFSET", "8"))

DAY_NAMES_CN = {
    "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
    "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日",
}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def api_get(url, headers=None):
    req = Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_post(url, data, headers=None):
    body = json.dumps(data).encode()
    req = Request(url, data=body, method="POST")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_user_stats():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = api_get(f"https://api.github.com/users/{GITHUB_USERNAME}", headers)
    return {
        "disk_usage": data.get("disk_usage", 0),
        "hireable": data.get("hireable", False),
        "public_repos": data.get("public_repos", 0),
        "total_private_repos": data.get("total_private_repos", 0),
    }


def get_yearly_contributions():
    now = datetime.now(timezone.utc)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
                contributionCalendar { totalContributions }
            }
        }
    }
    """
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
    result = api_post("https://api.github.com/graphql", {
        "query": query,
        "variables": {
            "login": GITHUB_USERNAME,
            "from": f"{now.year}-01-01T00:00:00Z",
            "to": now.isoformat(),
        },
    }, headers)
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]


def get_commit_stats():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    hours = []
    day_commits = defaultdict(int)

    for page in range(1, 11):
        try:
            events = api_get(
                f"https://api.github.com/users/{GITHUB_USERNAME}/events?per_page=100&page={page}",
                headers,
            )
        except (HTTPError, URLError):
            break
        if not events:
            break
        for event in events:
            if event["type"] == "PushEvent":
                created = datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                local_hour = (created.hour + TZ_OFFSET) % 24
                hours.append(local_hour)
                day_commits[created.strftime("%A")] += 1

    total = len(hours)
    if total == 0:
        return None

    morning = sum(1 for h in hours if 6 <= h < 12)
    daytime = sum(1 for h in hours if 12 <= h < 18)
    evening = sum(1 for h in hours if 18 <= h < 22)
    night = sum(1 for h in hours if h >= 22 or h < 6)

    most_productive = max(day_commits, key=day_commits.get) if day_commits else "Saturday"

    return {
        "morning": morning, "daytime": daytime,
        "evening": evening, "night": night,
        "total": total,
        "day_commits": dict(day_commits),
        "most_productive_cn": DAY_NAMES_CN.get(most_productive, most_productive),
        "is_early_bird": (morning + daytime) >= (evening + night),
    }


def get_language_stats():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    lang_count = defaultdict(int)
    page = 1
    while True:
        try:
            repos = api_get(
                f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&page={page}&type=owner",
                headers,
            )
        except (HTTPError, URLError):
            break
        if not repos:
            break
        for repo in repos:
            if not repo.get("fork") and repo.get("language"):
                lang_count[repo["language"]] += 1
        page += 1
    return dict(sorted(lang_count.items(), key=lambda x: x[1], reverse=True))


def get_wakatime_stats():
    if not WAKATIME_API_KEY:
        return None
    auth = base64.b64encode(WAKATIME_API_KEY.encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    try:
        data = api_get("https://wakatime.com/api/v1/users/current/stats/last_7_days", headers)
        return data["data"]
    except (HTTPError, URLError, KeyError):
        return None


# ── 格式化工具 ──────────────────────────────────────────────

def format_size(kb):
    if kb < 1024:
        return f"{kb} kB"
    return f"{kb / 1024:.1f} MB"


def make_bar(value, max_val, width=25):
    if max_val == 0:
        return "░" * width
    filled = min(round(width * value / max_val), width)
    return "█" * filled + "░" * (width - filled)


def fmt_pct(value, total):
    return f"{value / total * 100:.2f}%" if total else "0.0%"


def fmt_duration(seconds):
    if not seconds:
        return "0 秒"
    h, remainder = divmod(int(seconds), 3600)
    m, s = divmod(remainder, 60)
    parts = []
    if h:
        parts.append(f"{h} 小时")
    if m:
        parts.append(f"{m} 分钟")
    if not h and s:
        parts.append(f"{s} 秒")
    return " ".join(parts) or "0 秒"


# ── 生成内容 ────────────────────────────────────────────────

def generate_content():
    user = get_user_stats()
    contributions = get_yearly_contributions()
    commits = get_commit_stats()
    langs = get_language_stats()
    waka = get_wakatime_stats()
    now = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))

    L = []

    # 基础统计
    L.append("")
    L.append("**🐱 我的 GitHub 数据**")
    L.append("")
    L.append(f"> 🏆 {now.year} 年共 {contributions} 次贡献")
    L.append(">")
    L.append(f"> 📦 已使用 GitHub 存储 {format_size(user['disk_usage'])}")
    L.append(">")
    hireable = "开放招聘意向" if user["hireable"] else "未开启招聘意向"
    L.append(f"> 🚫 {hireable}")
    L.append(">")
    L.append(f"> 📜 {user['public_repos']} 个公开仓库")
    L.append(">")
    L.append(f"> 🔑 {user['total_private_repos']} 个私有仓库")
    L.append(">")

    if commits:
        bird = "我是个早起 🐤" if commits["is_early_bird"] else "我是个夜猫子 🦉"
        L.append(f"> **{bird}**")

        # 提交时段分布
        L.append("")
        L.append("```text")
        t = commits["total"]
        segments = [
            ("🌞 早晨", commits["morning"]),
            ("🌆 白天", commits["daytime"]),
            ("🌃 傍晚", commits["evening"]),
            ("🌙 深夜", commits["night"]),
        ]
        seg_max = max(v for _, v in segments)
        for label, count in segments:
            L.append(f"{label}     {count:>3} 次提交     {make_bar(count, seg_max)}   {fmt_pct(count, t):>7}")
        L.append("")
        L.append("```")

        # 最高产的一天
        L.append("")
        L.append(f'📅 **我在{commits["most_productive_cn"]}最高产**')
        L.append("")
        L.append("```text")
        dc = commits["day_commits"]
        day_max = max(dc.values()) if dc else 1
        for day in DAY_ORDER:
            count = dc.get(day, 0)
            cn = DAY_NAMES_CN[day]
            L.append(f"{cn}       {count:>2} 次提交       {make_bar(count, day_max)}   {fmt_pct(count, t):>7}")
        L.append("")
        L.append("```")

    # WakaTime 本周时间
    if waka:
        L.append("")
        L.append("📊 **本周时间分配**")
        L.append("")
        L.append("```text")
        L.append("💬 编程语言:")
        for item in waka.get("languages", [])[:5]:
            sec = item.get("total_seconds", 0)
            L.append(f'{item["name"]:<24}{fmt_duration(sec):<20}{make_bar(sec, waka["languages"][0]["total_seconds"])}   {item["percent"]:>6}%')
        L.append("")
        L.append("🔥 编辑器:")
        for item in waka.get("editors", [])[:5]:
            sec = item.get("total_seconds", 0)
            L.append(f'{item["name"]:<24}{fmt_duration(sec):<20}{make_bar(sec, waka["languages"][0]["total_seconds"])}   {item["percent"]:>6}%')
        L.append("")
        L.append("💻 操作系统:")
        for item in waka.get("operating_systems", [])[:5]:
            sec = item.get("total_seconds", 0)
            L.append(f'{item["name"]:<24}{fmt_duration(sec):<20}{make_bar(sec, waka["languages"][0]["total_seconds"])}   {item["percent"]:>6}%')
        L.append("")
        L.append("```")

    # 语言分布
    if langs:
        top_lang = next(iter(langs))
        L.append("")
        L.append(f"**我最常使用 {top_lang} 编程**")
        L.append("")
        L.append("```text")
        total_repos = sum(langs.values())
        lang_max = max(langs.values())
        for lang, count in list(langs.items())[:5]:
            L.append(f"{lang:<24}{count} 个仓库            {make_bar(count, lang_max)}   {fmt_pct(count, total_repos):>7}")
        L.append("")
        L.append("```")

    L.append("")
    L.append(f"最后更新于 {now.strftime('%Y/%m/%d')}")
    return "\n".join(L)


# ── 入口 ────────────────────────────────────────────────────

def main():
    content = generate_content()
    with open(README_PATH, "r") as f:
        readme = f.read()

    pattern = r"(<!--START_SECTION:waka-->).*?(<!--END_SECTION:waka-->)"
    new_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}\n{content}\n\n{m.group(2)}",
        readme,
        flags=re.DOTALL,
    )

    if new_readme != readme:
        with open(README_PATH, "w") as f:
            f.write(new_readme)
        print("README 已更新")
    else:
        print("README 无变化")


if __name__ == "__main__":
    main()
