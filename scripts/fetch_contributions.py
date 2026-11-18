#!/usr/bin/env python3
"""
Relève les contributions quotidiennes du profil sur la page publique que GitHub sert
lui-même (github.com/users/<login>/contributions), sans jeton, et écrit
data/contributions.json : les jours bruts et les chiffres dérivés (série en cours,
plus longue série, record d'une journée, totaux par mois).

Lancé chaque jour par .github/workflows/cartes.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

LOGIN = os.environ.get("GH_PROFILE_USER", "ethan-coo")
URL = f"https://github.com/users/{LOGIN}/contributions"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")


def fetch_days():
    r = requests.get(URL, headers={"User-Agent": "profile-cards/1.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        text = tips.get(td.get("id"), "")
        m = re.match(r"(\d+)", text)
        days.append({"date": date, "count": int(m.group(1)) if m else 0})
    if not days:
        sys.exit("aucun jour trouvé : la page de GitHub a peut-être changé")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    # série en cours : la journée d'aujourd'hui n'est pas finie, elle ne casse pas la série
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1
    cur = 0
    while i >= 0 and days[i]["count"] > 0:
        cur += 1
        i -= 1
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    return cur, longest


def build(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    cur, longest = streaks(days)
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "login": LOGIN,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": best,
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"{data['total']} contributions, série {data['current_streak']}, record {data['longest_streak']}")
