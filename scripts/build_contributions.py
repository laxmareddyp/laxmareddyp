"""Regenerate the generated sections of README.md.

Needs the GitHub CLI (`gh`), logged in. Run from anywhere:

    python scripts/build_contributions.py

All merged pull requests: every merged pull request by AUTHOR in OWNERS is
fetched and placed in exactly one category. A pull request that matches no
rule stops the script, so nothing is dropped silently: add a rule or an
OVERRIDES entry and re-run.

Code reviews: every pull request in OWNERS that AUTHOR reviewed and someone
else wrote, in any state.

The same data is written to data/profile.json, which the website loads.
"""

import json
import re
import subprocess
from pathlib import Path

from build_assets import (
    ASSETS,
    KIND_COLOURS,
    TILE_URLS,
    TILES,
    TOOLBOX,
    bar,
    tile,
    write,
)

README = Path(__file__).resolve().parent.parent / "README.md"
DATA = README.parent / "data" / "profile.json"

AUTHOR = "laxmareddyp"
OWNERS = ["keras-team", "tensorflow"]
SEARCH_CAP = 1000

REVIEWS = "Code reviews"
REVIEWS_COLOUR = KIND_COLOURS["review"]
# The live GitHub search behind the Code reviews tile.
REVIEWS_URL = (
    f"https://github.com/search?q=is%3Apr+reviewed-by%3A{AUTHOR}"
    f"+-author%3A{AUTHOR}"
    + "".join(f"+org%3A{owner}" for owner in OWNERS)
    + "&type=pullrequests"
)

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


def search(owner, *filters):
    proc = subprocess.run(
        [
            "gh",
            "search",
            "prs",
            "--owner",
            owner,
            "--limit",
            str(SEARCH_CAP),
            "--json",
            "number,title,repository,closedAt,createdAt,url,author",
            *filters,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
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


def newest_first(prs, date_field):
    return sorted(prs, key=lambda pr: (pr[date_field], pr["url"]), reverse=True)


def repositories(prs):
    return {pr["repository"]["nameWithOwner"] for pr in prs}


def authors(prs):
    return {(pr["author"] or {}).get("login", "ghost") for pr in prs}


def block(name, colour, prs, date_field, bars):
    """One collapsed list under a clickable bar, newest first."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    count = f"{len(prs)} PRs"
    bars[slug] = bar(name, count, colour)
    return [
        "<details>",
        f'<summary><picture><img src="assets/categories/{slug}.svg" '
        f'width="94%" alt="{name}, {count}"></picture></summary>',
        "",
        *(
            f"- [{clean(pr['title'])}]({pr['url']}) · {label(pr)}"
            for pr in newest_first(prs, date_field)
        ),
        "",
        "</details>",
        "",
    ]


def group(prs):
    """Place every pull request in exactly one category, or stop."""
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
    return groups


def render(prs, groups, bars):
    lines = [
        f"{len(prs)} merged pull requests across {len(repositories(prs))} "
        "repositories in keras-team and TensorFlow. Open a category to see "
        "every one.",
        "",
    ]
    for category in CATEGORIES:
        if groups[category]:
            colour = CATEGORY_COLOURS[category]
            lines += block(category, colour, groups[category], "closedAt", bars)
    return "\n".join(lines)


def render_reviews(prs, bars):
    lines = [
        f"Reviews on {len(prs)} pull requests by {len(authors(prs))} other "
        f"authors across {len(repositories(prs))} repositories.",
        "",
    ]
    lines += block(REVIEWS, REVIEWS_COLOUR, prs, "createdAt", bars)
    return "\n".join(lines)


def entries(prs, date_field):
    return [
        {
            "title": " ".join(pr["title"].split()),
            "url": pr["url"],
            "label": label(pr),
            "date": pr[date_field][:10],
        }
        for pr in newest_first(prs, date_field)
    ]


def section(slug, kind):
    """Which part of the website a tile belongs to."""
    if slug == "model-porter":
        return "automation"
    return {"guide": "guides", "link": "links"}.get(kind, "models")


def site_data(merged, groups, reviewed):
    """Everything the website shows, as one JSON document."""
    return {
        "tiles": [
            {
                "slug": slug,
                "name": name,
                "tag": tag,
                "kind": kind,
                "footer": footer,
                "section": section(slug, kind),
                "url": TILE_URLS[slug],
            }
            for slug, name, tag, kind, footer in TILES
        ],
        "kind_colours": KIND_COLOURS,
        "toolbox": TOOLBOX,
        "merged": {
            "total": len(merged),
            "repositories": len(repositories(merged)),
            "categories": [
                {
                    "name": category,
                    "colour": CATEGORY_COLOURS[category],
                    "prs": entries(groups[category], "closedAt"),
                }
                for category in CATEGORIES
                if groups[category]
            ],
        },
        "reviews": {
            "total": len(reviewed),
            "authors": len(authors(reviewed)),
            "repositories": len(repositories(reviewed)),
            "colour": REVIEWS_COLOUR,
            "url": REVIEWS_URL,
            "prs": entries(reviewed, "createdAt"),
        },
    }


def check_tile_links(text):
    """The README tile links are hand-written; keep them equal to the code."""
    links = {**TILE_URLS, "code-reviews": REVIEWS_URL}
    wrong = [
        slug
        for slug, url in links.items()
        if f'href="{url}"><img src="assets/tiles/{slug}.svg"' not in text
    ]
    if wrong:
        raise SystemExit(f"README.md tile link differs from the code: {wrong}")


def replace_block(text, name, body):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    if start not in text or end not in text:
        raise SystemExit(f"README.md needs the {start} and {end} markers.")
    head = text[: text.index(start) + len(start)]
    return f"{head}\n{body}{text[text.index(end) :]}"


def main():
    merged = [
        pr
        for owner in OWNERS
        for pr in search(owner, "--author", AUTHOR, "--merged")
    ]
    others = f"-author:{AUTHOR}"
    reviewed = [
        pr
        for owner in OWNERS
        for pr in search(owner, "--reviewed-by", AUTHOR, "--", others)
    ]
    groups = group(merged)
    bars = {}
    text = README.read_text(encoding="utf-8")
    check_tile_links(text)
    text = replace_block(text, "contributions", render(merged, groups, bars))
    text = replace_block(text, "reviews", render_reviews(reviewed, bars))
    bars_dir = ASSETS / "categories"
    bars_dir.mkdir(parents=True, exist_ok=True)
    for slug, svg in bars.items():
        write(bars_dir / f"{slug}.svg", svg)
    count = f"{len(reviewed)} PRs reviewed"
    review_tile = tile(REVIEWS, count, "review", "keras-team · TensorFlow")
    write(ASSETS / "tiles" / "code-reviews.svg", review_tile)
    write(README, text)
    data = site_data(merged, groups, reviewed)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    write(DATA, json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(
        f"Wrote {len(merged)} merged and {len(reviewed)} reviewed pull "
        f"requests to {README} and {DATA}"
    )


if __name__ == "__main__":
    main()
