import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

BASE = "https://www.postgresql.org/docs/current/"
PAGES = [
    "pgstatstatements",
    "using-explain",
    "monitoring-stats",
    "runtime-config-logging",
    "routine-vacuuming",
    "indexes-types",
    "runtime-config-connection",
    "explicit-locking",
    "runtime-config-resource",
    "planner-stats",
    "diskusage",
    "disk-full",
]
BLOCKS = ["h1", "h2", "h3", "h4", "p", "li", "pre", "dt", "dd", "tr"]

OUT = Path("data/runbooks/database")
OUT.mkdir(parents=True, exist_ok=True)


def extract_text(main) -> str:
    """One paragraph per block element, so inline tags don't split sentences."""
    parts = []
    for element in main.find_all(BLOCKS):
        if element.find(BLOCKS):          # only the innermost blocks
            continue
        if element.name == "pre":
            text = element.get_text().strip()
        elif element.name == "tr":
            cells = [" ".join(c.get_text().split()) for c in element.find_all(["th", "td"])]
            text = " | ".join(c for c in cells if c)
        else:
            text = " ".join(element.get_text().split())
        if text:
            parts.append(text)
    return "\n\n".join(parts)


for page in PAGES:
    url = f"{BASE}{page}.html"
    resp = httpx.get(
        url,
        headers={"User-Agent": "incident-pilot-learning-project"},
        follow_redirects=True,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"SKIPPED {page} (status {resp.status_code})")
        continue

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.find(id="docContent") or soup.body
    for tag in main.find_all(["nav", "script", "style"]):
        tag.decompose()

    cleaned = extract_text(main)
    dest = OUT / f"postgres__{page}.txt"
    dest.write_text(f"SOURCE_URL: {url}\n\n{cleaned}\n", encoding="utf-8")
    print(f"saved {dest}  ({len(cleaned)} characters)")
    time.sleep(1)

    