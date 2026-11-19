#!/usr/bin/env python3
"""Create local S3 zone encryption and service authentication secrets."""

import base64
import os
import secrets
import sys
from pathlib import Path


def create_if_missing(path, value):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not path.is_file():
            raise ValueError(f"{path} exists but is not a regular file")
        return False
    try:
        with os.fdopen(fd, "w", encoding="ascii") as file:
            file.write(value + "\n")
    except OSError:
        path.unlink()
        raise
    return True


def main(directory):
    directory = Path(directory)
    key_path = directory / "local-zone-key"
    token_path = directory / "local-zone-token"
    key_created = create_if_missing(key_path, base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii"))
    token_created = create_if_missing(token_path, secrets.token_urlsafe(32))
    try:
        key = base64.b64decode(key_path.read_bytes().strip(), altchars=b"-_", validate=True)
    except (ValueError, OSError) as exc:
        raise ValueError(f"Invalid local encryption key in {key_path}") from exc
    if len(key) != 32:
        raise ValueError(f"Invalid local encryption key in {key_path}")
    if not token_path.read_text(encoding="ascii").strip():
        raise ValueError(f"Empty local service token in {token_path}")
    print(f"Local zone key: {'created' if key_created else 'preserved'}")
    print(f"Local zone token: {'created' if token_created else 'preserved'}")


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else "config")
    except (OSError, ValueError) as exc:
        print(f"Unable to prepare local zone secrets: {exc}", file=sys.stderr)
        sys.exit(1)
