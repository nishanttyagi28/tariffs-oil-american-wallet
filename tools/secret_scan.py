"""Light secret scanner: working tree (tracked + to-be-committed data) and full git history.

Prints only file/line/rule, never the matched value. Exit code 1 if anything looks like a secret.
Usage: python tools/secret_scan.py [--history]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "github_token": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"),
    "openai_style_key": re.compile(r"\bsk-(proj-|ant-)?[A-Za-z0-9_-]{20,}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack_token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "cursor_key": re.compile(r"\b(key|crsr)_[A-Za-z0-9]{32,}"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "url_with_key_param": re.compile(r"[?&](api_?key|registrationkey|token|access_token)=[A-Za-z0-9_\-]{12,}", re.I),
    "assignment": re.compile(
        r"(api[_-]?key|secret|password|passwd|token|auth|census_api_key|bls_api_key|fred_api_key|eia_api_key)"
        r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+=]{16,})", re.I),
}
# assignment values that are clearly not secrets (env lookups, placeholders)
BENIGN = re.compile(r"os\.environ|getenv|env_var|\{\{|<|your_|example|placeholder|xxxx|None|null", re.I)
TEXT_EXT = {".py", ".sql", ".yml", ".yaml", ".md", ".txt", ".json", ".toml", ".cfg", ".ini", ".ps1", ".sh",
            ".csv", ".tmdl", ".pbir", ".pbism", ".pbip", ".example", ".gitignore", ".gitattributes", ""}


def scan_text(label: str, text: str, hits: list[str]) -> None:
    for n, line in enumerate(text.splitlines(), 1):
        for rule, rx in RULES.items():
            m = rx.search(line)
            if not m:
                continue
            if rule == "assignment" and BENIGN.search(line):
                continue
            hits.append(f"{label}:{n}: {rule}")


def tree_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.splitlines()
    return [ROOT / p for p in out]


def main() -> int:
    hits: list[str] = []
    for f in tree_files():
        if f.suffix.lower() not in TEXT_EXT or not f.is_file() or f.stat().st_size > 20_000_000:
            continue
        scan_text(str(f.relative_to(ROOT)).replace("\\", "/"), f.read_text(encoding="utf-8", errors="ignore"), hits)
    if subprocess.run(["git", "ls-files", "--error-unmatch", ".env"], cwd=ROOT,
                                         capture_output=True).returncode == 0:
        hits.append(".env: tracked by git")
    if "--history" in sys.argv:
        log = subprocess.run(["git", "log", "--all", "-p", "--no-color", "--format=commit %h", "-U0"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
        commit = file = "?"
        for line in log.splitlines():
            if line.startswith("commit "):
                commit = line.split()[1]
            elif line.startswith("+++ "):
                file = line[6:] if line.startswith("+++ b/") else line[4:]
            elif line.startswith("+") and not line.startswith("+++"):
                before = len(hits)
                scan_text(f"history {commit} {file}", line[1:], hits)
                for i in range(before, len(hits)):
                    hits[i] = hits[i].replace(":1:", ":")
        names = subprocess.run(["git", "log", "--all", "--name-only", "--format="], cwd=ROOT, capture_output=True,
                               text=True).stdout.split()
        if any(Path(n).name == ".env" for n in names):
            hits.append("history: a .env file was committed at some point")
    for h in sorted(set(hits)):
        print(h)
    print(f"secret scan: {len(set(hits))} finding(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
