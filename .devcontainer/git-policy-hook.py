#!/usr/bin/env python3
"""
PreToolUse hook on the Bash tool. Blocks git/gh commands that rewrite or delete
existing history, branches, or tags. Configured alongside this script in claude-policy.json.

Contract:
  stdin  : JSON from Claude Code; tool_input.command is the bash string about to run.
  stdout : JSON decision (only when blocking). Silence = allow.
  exit   : 0.

The hook covers three common ways a simple permission matcher can be bypassed:
  - compound commands (a; b, a && b, a || b, a | b, a & b);
  - git config overrides (`git -c key=val push --force ...`);
  - nested shells (bash -c '...', sh -c '...', eval '...').
"""

from __future__ import annotations

import json
import re
import shlex
import sys

DENIED_FLAGS_PUSH = {"--force", "-f", "--force-with-lease", "--delete", "-d"}
DENIED_FLAGS_BRANCH = {"-d", "-D", "--delete", "--delete-force", "-m", "-M", "--move"}
DENIED_FLAGS_TAG = {"-d", "--delete"}
DENIED_FLAGS_CHECKOUT = {"-B", "--orphan"}
DENIED_FLAGS_SWITCH = {"-C", "--orphan"}
DENIED_FLAGS_RESET = {"--hard", "--keep"}
DENIED_GIT_SUBCOMMANDS_FULL = {
    "pull",
    "rebase",
    "update-ref",
    "filter-branch",
    "filter-repo",
    "replace",
}

NESTED_SHELLS = {"bash", "sh", "zsh", "dash", "ash"}

SHELL_SEPARATOR_RE = re.compile(r";|&&|\|\||(?<!\|)\|(?!\|)|(?<!&)&(?!&)")


def split_by_shell_separators(cmd: str) -> list[str]:
    return [p.strip() for p in SHELL_SEPARATOR_RE.split(cmd) if p.strip()]


def strip_git_config_prefix(tokens: list[str]) -> list[str]:
    if not tokens or tokens[0] != "git":
        return tokens

    out = ["git"]
    i = 1
    while i < len(tokens):
        if tokens[i] == "-c" and i + 1 < len(tokens):
            i += 2

        elif tokens[i].startswith("--config-env="):
            i += 1

        else:
            break

    out.extend(tokens[i:])

    return out


def check_git(tokens: list[str]) -> str | None:
    tokens = strip_git_config_prefix(tokens)
    if len(tokens) < 2:
        return None

    sub = tokens[1]
    rest = tokens[2:]

    if sub in DENIED_GIT_SUBCOMMANDS_FULL:
        return f"git {sub} is forbidden by policy"

    if sub == "commit" and "--amend" in rest:
        return "git commit --amend is forbidden by policy"

    if sub == "reset":
        for a in rest:
            if a in DENIED_FLAGS_RESET:
                return f"git reset {a} is forbidden by policy"

    if sub == "push":
        for a in rest:
            if a in DENIED_FLAGS_PUSH or a.startswith("--force-with-lease="):
                return f"git push {a} is forbidden by policy"

            if a.startswith(":") and len(a) > 1:
                return "git push <remote> :<branch> (branch deletion) is forbidden by policy"

    if sub == "branch":
        for a in rest:
            if a in DENIED_FLAGS_BRANCH:
                return f"git branch {a} is forbidden by policy"

    if sub == "tag":
        for a in rest:
            if a in DENIED_FLAGS_TAG:
                return f"git tag {a} is forbidden by policy"

    if sub == "checkout":
        for a in rest:
            if a in DENIED_FLAGS_CHECKOUT:
                return f"git checkout {a} is forbidden by policy"

    if sub == "switch":
        for a in rest:
            if a in DENIED_FLAGS_SWITCH:
                return f"git switch {a} is forbidden by policy"

    if sub == "reflog" and rest and rest[0] in {"expire", "delete"}:
        return f"git reflog {rest[0]} is forbidden by policy"

    if sub == "gc":
        for a in rest:
            if a == "--aggressive" or a.startswith("--prune=now"):
                return f"git gc {a} is forbidden by policy"

    return None


def check_gh(tokens: list[str]) -> str | None:
    if len(tokens) >= 3 and tokens[0] == "gh" and tokens[1] == "pr" and tokens[2] == "merge":
        return "gh pr merge is forbidden — only the developer merges PRs manually"

    return None


def check_tokens(tokens: list[str]) -> str | None:
    if not tokens:
        return None

    head = tokens[0]

    if head in NESTED_SHELLS and len(tokens) >= 3 and tokens[1] == "-c":
        return check_command(tokens[2])

    if head == "eval":
        return check_command(" ".join(tokens[1:]))

    if head == "git":
        return check_git(tokens)

    if head == "gh":
        return check_gh(tokens)

    return None


def check_command(cmd: str) -> str | None:
    for part in split_by_shell_separators(cmd):
        try:
            tokens = shlex.split(part)

        except ValueError:
            return f"failed to parse command: {part}"

        reason = check_tokens(tokens)
        if reason:
            return reason

    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)

    except json.JSONDecodeError:
        sys.exit(0)

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        sys.exit(0)

    reason = check_command(cmd)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()