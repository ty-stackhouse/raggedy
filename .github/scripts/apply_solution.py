#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, **kwargs):
    print(f"> {cmd}")
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kwargs)


def main():
    if len(sys.argv) < 2:
        print("Usage: apply_solution.py <solution.json> [issue_number]")
        sys.exit(2)

    sol_path = Path(sys.argv[1])
    issue_num = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("ISSUE_NUM")

    if not sol_path.exists():
        print(f"solution file not found: {sol_path}")
        sys.exit(3)

    data = json.loads(sol_path.read_text())

    branch = data.get("branch_name")
    commit_message = data.get("commit_message")
    pr_title = data.get("pr_title")
    pr_body = data.get("pr_body", "")
    files = data.get("files", [])

    if not branch or not commit_message or not pr_title or not files:
        print("Missing required fields in solution.json")
        sys.exit(4)

    try:
        # Git identity
        run(["git", "config", "user.name", "AI Agent"])
        run(["git", "config", "user.email", "ai-agent@users.noreply.github.com"]) 

        # Create branch
        run(["git", "checkout", "-b", branch])

        added = []
        for f in files:
            path = Path(f["path"])
            content = f.get("content", "")
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            run(["git", "add", str(path)])
            added.append(str(path))

        # Commit and push
        run(["git", "commit", "-m", commit_message])
        run(["git", "push", "origin", branch])

        # Create PR (append closing to body if issue present)
        body = pr_body
        if issue_num:
            body = f"{pr_body}\n\nCloses #{issue_num}"

        run([
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", body,
            "--base", "main",
            "--head", branch,
        ])

        print("Done: PR created")

    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        sys.exit(5)


if __name__ == '__main__':
    main()
