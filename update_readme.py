#!/usr/bin/env python3
"""Auto-regenerate the 'Projects by theme' section of the profile README.

Fetches all public repos, groups them by topic (fallback: name/description
keywords), and rewrites the content between the section markers.
Run by .github/workflows/update-readme.yml every 6 hours.
"""
import json
import os
import re
import urllib.request

USER = "AfridaMehanaz"
README = "README.md"
START = "<!--START_SECTION:projects-->"
END = "<!--END_SECTION:projects-->"

# (title, topic tags, fallback keywords) — order = display order
GROUPS = [
    ("🔍 RAG & Retrieval", {"rag", "retrieval"}, ("rag", "retrieval")),
    ("🛡️ AI Safety", {"ai-safety", "guardrails", "safety"}, ("guardrail", "safety", "pii")),
    ("⚙️ LLMOps", {"llmops", "mlops", "cicd", "ci-cd"}, ("llmops", "cicd", "ci/cd", "pipeline", "dashboard", "evaluation")),
    ("🤖 Agents", {"agents", "agent", "mcp"}, ("agent", "mcp", "sql-assistant")),
    ("🔧 Fine-tuning & Data", {"fine-tuning", "lora", "etl", "data"}, ("finetun", "fine-tun", "lora", "etl", "data")),
]
OTHER = "📦 Other projects"


def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as r:
        repos = json.load(r)
    return [r for r in repos
            if not r["fork"] and not r["archived"] and r["name"] != USER]


def classify(repo):
    topics = {t.lower() for t in repo.get("topics", [])}
    text = (repo["name"] + " " + (repo["description"] or "")).lower()
    for title, tags, _ in GROUPS:
        if topics & tags:
            return title
    for title, _, keywords in GROUPS:
        if any(k in text for k in keywords):
            return title
    return OTHER


def render(repos):
    buckets = {}
    for r in repos:
        buckets.setdefault(classify(r), []).append(r)
    lines = []
    for title in [g[0] for g in GROUPS] + [OTHER]:
        if title not in buckets:
            continue
        lines.append(f"**{title}**")
        for r in buckets[title]:
            desc = (r["description"] or "").strip()
            lines.append(f"- [**{r['name']}**]({r['html_url']})" + (f" — {desc}" if desc else ""))
        lines.append("")
    return "\n".join(lines).rstrip()


def main():
    with open(README, encoding="utf-8") as f:
        content = f.read()
    section = f"{START}\n{render(fetch_repos())}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), section, content, flags=re.S)
    if new != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
