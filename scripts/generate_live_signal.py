#!/usr/bin/env python3
"""Generate a compact SVG from a GitHub user's current public repository data."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any


API_ROOT = "https://api.github.com"


def github_json(path: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Himath2002-profile-signal",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code} for {path}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach the GitHub API for {path}: {error.reason}") from error


def select_public_work(repositories: list[dict[str, Any]], profile_repository: str) -> list[dict[str, Any]]:
    return sorted(
        (
            repository
            for repository in repositories
            if not repository.get("fork")
            and not repository.get("archived")
            and repository.get("name") != profile_repository
        ),
        key=lambda repository: repository.get("pushed_at") or "",
        reverse=True,
    )


def compact_name(value: str, limit: int) -> str:
    """Keep dynamic repository labels inside their fixed SVG cards."""
    return value if len(value) <= limit else f"{value[: limit - 1]}…"


def render_svg(username: str, profile: dict[str, Any], repositories: list[dict[str, Any]], refreshed_at: datetime) -> str:
    public_work = select_public_work(repositories, username)
    languages = Counter(
        repository["language"]
        for repository in public_work
        if repository.get("language")
    )
    recent_names = [repository["name"] for repository in public_work[:3]]
    while len(recent_names) < 3:
        recent_names.append("More work in progress")

    latest = public_work[0] if public_work else None
    latest_name = compact_name(latest["name"], 38) if latest else "Public work in progress"
    latest_date = "—"
    if latest and latest.get("pushed_at"):
        latest_date = datetime.fromisoformat(latest["pushed_at"].replace("Z", "+00:00")).strftime("%d %b %Y")

    values = {
        "username": escape(username),
        "public_repos": escape(str(profile.get("public_repos", len(repositories)))),
        "languages": escape(str(len(languages))),
        "latest_name": escape(latest_name),
        "latest_date": escape(latest_date),
        "refreshed": escape(refreshed_at.astimezone(UTC).strftime("%d %b %Y · %H:%M UTC")),
        "recent_1": escape(compact_name(recent_names[0], 28)),
        "recent_2": escape(compact_name(recent_names[1], 28)),
        "recent_3": escape(compact_name(recent_names[2], 34)),
    }

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="370" viewBox="0 0 1200 370" role="img" aria-labelledby="title desc">
  <title id="title">Live public engineering signal for {values["username"]}</title>
  <desc id="desc">Current public repository count, active language count, latest update, and recently active repositories.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071C24"/>
      <stop offset="1" stop-color="#154D47"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="370" rx="28" fill="url(#bg)"/>
  <circle cx="1120" cy="-18" r="170" fill="#73E6C3" opacity="0.08"/>
  <text x="54" y="58" fill="#9DEFD7" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="15" font-weight="760" letter-spacing="2.4">LIVE PUBLIC ENGINEERING PULSE</text>
  <circle cx="954" cy="51" r="6" fill="#B8E860"/>
  <text x="972" y="57" fill="#CEE2DE" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="14" font-weight="650">AUTO-REFRESHED DAILY</text>

  <g font-family="Inter,Segoe UI,Arial,sans-serif">
    <g transform="translate(54 92)">
      <rect width="250" height="116" rx="20" fill="#F6FAF9"/>
      <text x="24" y="34" fill="#54716C" font-size="13" font-weight="750" letter-spacing="1.4">PUBLIC REPOSITORIES</text>
      <text x="24" y="84" fill="#153F3B" font-size="42" font-weight="800">{values["public_repos"]}</text>
    </g>
    <g transform="translate(322 92)">
      <rect width="250" height="116" rx="20" fill="#F6FAF9"/>
      <text x="24" y="34" fill="#54716C" font-size="13" font-weight="750" letter-spacing="1.4">PRIMARY LANGUAGES</text>
      <text x="24" y="84" fill="#153F3B" font-size="42" font-weight="800">{values["languages"]}</text>
    </g>
    <g transform="translate(590 92)">
      <rect width="556" height="116" rx="20" fill="#F6FAF9"/>
      <text x="24" y="34" fill="#54716C" font-size="13" font-weight="750" letter-spacing="1.4">LATEST PUBLIC UPDATE</text>
      <text x="24" y="72" fill="#153F3B" font-size="25" font-weight="780">{values["latest_name"]}</text>
      <text x="24" y="98" fill="#5A756F" font-size="14" font-weight="600">{values["latest_date"]}</text>
    </g>

    <text x="54" y="252" fill="#9DEFD7" font-size="13" font-weight="750" letter-spacing="1.6">RECENT PUBLIC WORK</text>
    <g font-size="15" font-weight="680">
      <rect x="54" y="272" width="330" height="45" rx="22" fill="#174740" stroke="#4F9488"/>
      <text x="219" y="300" fill="#ECF7F4" text-anchor="middle">{values["recent_1"]}</text>
      <rect x="398" y="272" width="330" height="45" rx="22" fill="#174740" stroke="#4F9488"/>
      <text x="563" y="300" fill="#ECF7F4" text-anchor="middle">{values["recent_2"]}</text>
      <rect x="742" y="272" width="404" height="45" rx="22" fill="#174740" stroke="#4F9488"/>
      <text x="944" y="300" fill="#ECF7F4" text-anchor="middle">{values["recent_3"]}</text>
    </g>
    <text x="1146" y="346" fill="#87AAA3" font-size="12" font-weight="600" text-anchor="end">Refreshed {values["refreshed"]}</text>
  </g>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, help="Read profile and repository data from a local JSON fixture")
    args = parser.parse_args()

    if args.fixture:
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        profile = fixture["profile"]
        repositories = fixture["repositories"]
    else:
        token = os.getenv("GITHUB_TOKEN")
        profile = github_json(f"/users/{args.username}", token)
        repositories = github_json(
            f"/users/{args.username}/repos?per_page=100&sort=pushed&direction=desc",
            token,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_svg(args.username, profile, repositories, datetime.now(UTC)),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
