import time
from pathlib import Path 
import httpx
from bs4 import BeautifulSoup

BASE = "http://www.postgresql.org/docs/current/"
PAGES = [
    "pgstatstatements",
    "using-explain",
    "monitoring-stats",
    "runtime-config-logging",
    "routing-vacuuming",
    "indexes-types",
    "runtime-config-connection",
    "explicit-locking",
    "runtime-config-resources",
    "planner-stats",
]

OUT = Path("data/runbooks/database")
OUT.mkdir(parents=True,exist_ok=True)

for page in PAGES:
    url = f"{BASE}{page}.html"
    resp = httpx.get(
        url,
        headers={"User-Agent":"incident-pilot-learning-project"},
        follow_redirects=True,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"SKIPPED {page} (status {resp.status_code})")
        continue

    soup = BeautifulSoup(resp.text,"html.parser")
    main = soup.find(id="doContent") or soup.body
    for tag in main.find_all(["nav","script","style"]):
        tag.decompose()

    text = main.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)

    dest = OUT / f"postgres__{page}.txt"
    dest.write_text(f"SOURCES_URL: {url}\n\n{cleaned}\n", encoding="utf-8")
    print(f"saved {dest}  ({len(cleaned)} characters)")
    time.sleep(1)



