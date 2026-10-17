"""Shell-quoting helpers for copyable curl examples.

Bash never expands ``$VAR`` / ``${VAR}`` inside single quotes, so a header
such as ``-H 'Authorization: Bearer ${GROQ_API_KEY}'`` sends the literal text
``${GROQ_API_KEY}`` and the provider answers 401.  These helpers rewrite such
single-quoted curl arguments into double-quoted ones (``"Authorization: Bearer
$GROQ_API_KEY"``) and can prepend an ``export NAME="你的 Key"`` line so the
command works when pasted into a fresh macOS / Linux terminal.

Only *logical lines that invoke curl* are touched.  Other shell commands keep
their quoting on purpose, e.g. NVIDIA NGC's ``docker login --username
'$oauthtoken'`` where ``$oauthtoken`` is the literal username.
"""
from __future__ import annotations

import re

_VAR_REF = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
_SINGLE_QUOTED = re.compile(r"'([^']*)'")
_CURL_WORD = re.compile(r"(?:^|[\s;|&(])curl(?:\s|$)")
_EXPORT_PLACEHOLDER = "你的 Key"


def _logical_lines(command: str) -> list[str]:
    """Split on newlines but keep backslash-continued lines together."""
    lines: list[str] = []
    buffer = ""
    for raw in command.split("\n"):
        buffer = raw if not buffer else buffer + "\n" + raw
        if raw.rstrip().endswith("\\"):
            continue
        lines.append(buffer)
        buffer = ""
    if buffer:
        lines.append(buffer)
    return lines


def is_curl_line(line: str) -> bool:
    return bool(_CURL_WORD.search(line))


def _brace_to_plain(text: str) -> str:
    """``${NAME}`` -> ``$NAME`` when the next character cannot extend the name."""

    def repl(match: re.Match[str]) -> str:
        end = match.end()
        nxt = text[end] if end < len(text) else ""
        if match.group(1) and not re.match(r"[A-Za-z0-9_]", nxt):
            return "$" + match.group(1)
        return match.group(0)

    return _VAR_REF.sub(repl, text)


def _double_quote(content: str) -> str:
    escaped = content.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`")
    return '"' + _brace_to_plain(escaped) + '"'


def fix_curl_quoting(command: str | None) -> str | None:
    """Return ``command`` with variable-bearing single-quoted curl args double-quoted.

    Single-quoted arguments without a ``$`` reference (typically the JSON
    body) are left exactly as they are.
    """
    if not command or "'" not in command or "$" not in command:
        return command
    out: list[str] = []
    for line in _logical_lines(command):
        if is_curl_line(line):
            line = _SINGLE_QUOTED.sub(
                lambda m: _double_quote(m.group(1)) if _VAR_REF.search(m.group(1)) else m.group(0),
                line,
            )
        out.append(line)
    return "\n".join(out)


def curl_env_vars(command: str | None) -> list[str]:
    """Environment variables referenced by curl lines, in order of appearance."""
    names: list[str] = []
    for line in _logical_lines(command or ""):
        if not is_curl_line(line):
            continue
        for match in _VAR_REF.finditer(line):
            name = match.group(1) or match.group(2)
            if name not in names:
                names.append(name)
    return names


def with_env_exports(command: str | None, placeholder: str = _EXPORT_PLACEHOLDER) -> str | None:
    """Fix curl quoting and prepend ``export NAME="…"`` for unset referenced vars."""
    fixed = fix_curl_quoting(command)
    if not fixed:
        return fixed
    exported = set(re.findall(r"(?m)^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=", fixed))
    missing = [name for name in curl_env_vars(fixed) if name not in exported]
    if not missing:
        return fixed
    preamble = "\n".join(f'export {name}="{placeholder}"' for name in missing)
    return preamble + "\n" + fixed


def single_quoted_curl_vars(command: str | None) -> list[str]:
    """Single-quoted curl arguments that still contain a ``$`` variable (the bug)."""
    bad: list[str] = []
    for line in _logical_lines(command or ""):
        if not is_curl_line(line):
            continue
        for match in _SINGLE_QUOTED.finditer(line):
            if _VAR_REF.search(match.group(1)):
                bad.append(match.group(1))
    return bad
