"""Regenerate the "All merged pull requests" section of README.md.

Needs the GitHub CLI (`gh`), logged in. Run from anywhere:

    python scripts/build_contributions.py

Every merged pull request by AUTHOR in OWNERS is fetched and placed in exactly
one category. A pull request that matches no rule stops the script, so nothing
is dropped silently: add a rule or an OVERRIDES entry and re-run.
"""

import json
import re
import subprocess
from pathlib import Path

from build_assets import ASSETS, bar, write

README = Path(__file__).resolve().parent.parent / "README.md"
START = "<!-- contributions:start -->"
END = "<!-- contributions:end -->"

AUTHOR = "laxmareddyp"
OWNERS = ["keras-team", "tensorflow"]
SEARCH_CAP = 1000

MODELS = "Models, weights and converters"
INFRA = "CI, tests and infrastructure"
RELEASES = "Releases"
MIGRATIONS = "Migrations"
FIXES = "Features and fixes"
GUIDES = "Guides and examples"
DOCS = "API docs"
TFJS = "TensorFlow.js"
TF_MODELS = "TensorFlow Model Garden"

# Display order, and the colour of each category bar.
CATEGORY_COLOURS = {
    MODELS: "#FFB454",
    INFRA: "#7CC8FF",
    MIGRATIONS: "#7EDFA4",
    FIXES: "#B8A4FF",
    RELEASES: "#FF8F70",
    GUIDES: "#FF9EC4",
    DOCS: "#FFE08A",
    TFJS: "#F6C177",
    TF_MODELS: "#C9D1E0",
}
CATEGORIES = list(CATEGORY_COLOURS)

INFRA_PATTERN = (
    r"\bci\b|workflow|github actions|kokoro|zizmor|runner|nightly"
    r"|\bpin\b|unpin|pypi|oidc|gemini|triage|assignee|jules|timeout|xdist"
    r"|pr template|pull-request-validation|kagglesdk|kagglehub|cuda"
    r"|\btests?\b|flaky|tolerance|site deploys|project_url|collaborators"
    r"|transformers to latest"
)

# Rules for keras-team code repositories. First match wins.
RULES = [
    (
        RELEASES,
        r"version bump|bump version|bump up master|\[release\]|dev version"
        r"|sync.*kaggle|update keras version|security fixes 3",
    ),
    (INFRA, INFRA_PATTERN),
    (MIGRATIONS, r"pygrain|tf-free|tf-keras to keras 3"),
    (
        MODELS,
        r"model|preset|checkpoint|conver|\bport\b|basnet|embedding"
        r"|safetensors|qwen|gemma",
    ),
    (
        FIXES,
        r"fix|incorrect|honor|track|graph-safe|optional|warnings|resolve"
        r"|treat|openvino|type error",
    ),
]

GUIDE_PATTERN = r"guide|\brag\b|basnet to keras"

# Pull requests the title rules get wrong or cannot place.
OVERRIDES = {
    "keras#24232": FIXES,
    "keras#23792": FIXES,
    "keras-hub#3156": FIXES,
    "keras-hub#3124": FIXES,
    "keras-hub#3115": INFRA,
    "keras-hub#2852": INFRA,
    "keras-hub#2752": INFRA,
    "keras-io#2410": INFRA,
    "keras-hub#2710": FIXES,
    "keras-hub#2709": FIXES,
    "keras-hub#2560": FIXES,
    "keras-hub#2294": MODELS,
    "keras-hub#2284": FIXES,
    "keras-hub#2261": FIXES,
}


def fetch(owner):
    proc = subprocess.run(
        [
            "gh",
            "search",
            "prs",
            "--author",
            AUTHOR,
            "--owner",
            owner,
            "--merged",
            "--limit",
            str(SEARCH_CAP),
            "--json",
            "number,title,repository,closedAt,url",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    prs = json.loads(proc.stdout)
    if len(prs) >= SEARCH_CAP:
        raise SystemExit(
            f"{owner}: hit the {SEARCH_CAP}-result search cap. Split the "
            "query by date so no pull request is missed."
        )
    return prs


def label(pr):
    return f"{pr['repository']['name']}#{pr['number']}"


def categorise(pr):
    if label(pr) in OVERRIDES:
        return OVERRIDES[label(pr)]
    owner, repo = pr["repository"]["nameWithOwner"].split("/")
    title = pr["title"].lower()
    if owner == "tensorflow":
        return TFJS if repo.startswith("tfjs") else TF_MODELS
    if repo == "keras-io":
        if re.search(INFRA_PATTERN, title):
            return INFRA
        return GUIDES if re.search(GUIDE_PATTERN, title) else DOCS
    for category, pattern in RULES:
        if re.search(pattern, title):
            return category
    return None


def clean(title):
    title = " ".join(title.split())
    for char in "\\[]<>`*_|":
        title = title.replace(char, f"\\{char}")
    return title


def render(prs):
    groups = {category: [] for category in CATEGORIES}
    unplaced = []
    for pr in prs:
        category = categorise(pr)
        if category is None:
            unplaced.append(pr)
        else:
            groups[category].append(pr)
    if unplaced:
        listing = "\n".join(
            f"  {label(pr)}  {pr['title'].strip()}" for pr in unplaced
        )
        raise SystemExit(f"No category for:\n{listing}")

    repos = {pr["repository"]["nameWithOwner"] for pr in prs}
    lines = [
        f"{len(prs)} merged pull requests across {len(repos)} repositories "
        "in keras-team and TensorFlow. Open a category to see every one.",
        "",
    ]
    bars = {}
    for category in CATEGORIES:
        items = sorted(
            groups[category],
            key=lambda pr: (pr["closedAt"], pr["url"]),
            reverse=True,
        )
        if not items:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        count = f"{len(items)} PRs"
        bars[slug] = bar(category, count, CATEGORY_COLOURS[category])
        lines += [
            "<details>",
            f'<summary><picture><img src="assets/categories/{slug}.svg" '
            f'width="94%" alt="{category}, {count}"></picture></summary>',
            "",
        ]
        lines += [
            f"- [{clean(pr['title'])}]({pr['url']}) · {label(pr)}"
            for pr in items
        ]
        lines += ["", "</details>", ""]
    return "\n".join(lines), bars


def main():
    prs = [pr for owner in OWNERS for pr in fetch(owner)]
    section, bars = render(prs)
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit(f"README.md needs the {START} and {END} markers.")
    before = text[: text.index(START) + len(START)]
    after = text[text.index(END) :]
    bars_dir = ASSETS / "categories"
    bars_dir.mkdir(parents=True, exist_ok=True)
    for slug, svg in bars.items():
        write(bars_dir / f"{slug}.svg", svg)
    write(README, f"{before}\n{section}{after}")
    print(f"Wrote {len(prs)} pull requests to {README}")


if __name__ == "__main__":
    main()
