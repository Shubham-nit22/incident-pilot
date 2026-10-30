import shutil
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/runbooks")

K8S_ROOT = RAW / "k8s" / "content" / "en"
OWASP_DIR = RAW / "owasp" / "cheatsheets"

OWASP_FILES = [
    "Authentication_Cheat_Sheet.md",
    "Credential_Stuffing_Prevention_Cheat_Sheet.md",
    "Denial_of_Service_Cheat_Sheet.md",
    "Logging_Cheat_Sheet.md",
    "Secrets_Management_Cheat_Sheet.md",
    "Session_Management_Cheat_Sheet.md",
    "Authorization_Cheat_Sheet.md",
    "Password_Storage_Cheat_Sheet.md",
]

def k8s_url(path: Path) -> str:
    rel = path.relative_to(K8S_ROOT).with_suffix("")
    return f"https://kubernetes.io/{rel.as_posix()}/"


def copy_with_header(src: Path, dest: Path, url: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = src.read_text(encoding="utf-8")
    dest.write_text(f"SOURCE_URL: {url}\n\n{body}", encoding="utf-8")



def collect_k8s(category: str, folder: Path, pattern: str, skip: tuple = ()) -> int:
    count = 0
    if not folder.exists():
        print(f"MISSING folder: {folder}")
        return 0
    for src in sorted(folder.glob(pattern)):
        if src.name in skip or src.name.startswith("_index") or src.stat().st_size < 500:
            continue
        dest = OUT / category / f"k8s__{src.stem}.md"
        copy_with_header(src, dest, k8s_url(src))
        count += 1
    return count


counts = {"deployment":0, "network":0, "security":0}
counts["deployment"] += collect_k8s(
    "deployment", K8S_ROOT / "docs/tasks/debug/debug-application", "*.md",
    skip=("debug-service.md",),
)

counts["deployment"]+= collect_k8s(
    "deployment",K8S_ROOT / "docs/concepts/workloads/controllers","deployment.md"
)

counts["network"] += collect_k8s(
    "network", K8S_ROOT / "docs/tasks/debug/debug-application", "debug-service.md"
)

for name in OWASP_FILES:
    src = OWASP_DIR/name
    if not src.exists():
        print(f"MISSING OWASP file : {name}")
        continue
    url = f"https://cheatsheetseries.owasp.org/cheatsheets/{src.stem}.html"
    copy_with_header(src, OUT / "security" / f"owasp__{src.stem}.md", url)
    counts["security"] += 1

print("Collected: ",counts)

