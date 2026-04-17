"""Security utilities for file path validation and string sanitization."""

import os
import re
import unicodedata

# UUID v4 pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

# Control characters to strip (U+0000-U+001F except \n \t)
_CONTROL_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f]"
)

MAX_FIELD_LENGTH = 50_000


def safe_path(base: str, *parts: str) -> str:
    """Resolve a path and ensure it stays within the base directory.

    Raises ValueError on path traversal attempts.
    """
    joined = os.path.join(base, *parts)
    resolved = os.path.realpath(joined)
    base_resolved = os.path.realpath(base)
    # Allow the base directory itself or anything under it
    if resolved != base_resolved and not resolved.startswith(base_resolved + os.sep):
        raise ValueError(f"Path traversal attempt blocked: {joined}")
    return resolved


def validate_uuid(value: str) -> bool:
    """Validate that a string is a valid UUID v4."""
    return bool(UUID_PATTERN.match(value.lower()))


def sanitize_string(value: str | None) -> str | None:
    """Strip null bytes, control characters, and truncate to MAX_FIELD_LENGTH."""
    if value is None:
        return None
    # Strip null bytes
    value = value.replace("\x00", "")
    # Strip control characters (keep \n and \t)
    value = _CONTROL_CHARS.sub("", value)
    # Truncate
    if len(value) > MAX_FIELD_LENGTH:
        value = value[:MAX_FIELD_LENGTH]
    return value


def validate_xml_start(content: bytes) -> bool:
    """Check that content starts with a valid XML declaration.

    Allows optional BOM (UTF-8 or UTF-16) before <?xml.
    """
    # Strip BOM if present
    stripped = content
    if stripped.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
        stripped = stripped[3:]
    elif stripped.startswith(b"\xff\xfe") or stripped.startswith(b"\xfe\xff"):  # UTF-16 BOM
        stripped = stripped[2:]

    # Strip leading whitespace
    stripped = stripped.lstrip()

    return stripped.startswith(b"<?xml")
