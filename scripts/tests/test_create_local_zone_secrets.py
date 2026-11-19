import base64
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "create_local_zone_secrets.py"


def run_script(directory):
    return subprocess.run([sys.executable, str(SCRIPT), str(directory)], capture_output=True, text=True)


def test_creates_private_random_secrets_and_preserves_existing_files(tmp_path):
    assert run_script(tmp_path).returncode == 0
    key_path = tmp_path / "local-zone-key"
    token_path = tmp_path / "local-zone-token"
    key = key_path.read_bytes()
    token = token_path.read_bytes()
    assert len(base64.urlsafe_b64decode(key.strip())) == 32
    assert len(token.strip()) >= 32
    assert os.stat(key_path).st_mode & 0o777 == 0o600
    assert os.stat(token_path).st_mode & 0o777 == 0o600
    result = run_script(tmp_path)
    assert result.returncode == 0
    assert "preserved" in result.stdout
    assert key_path.read_bytes() == key
    assert token_path.read_bytes() == token


def test_invalid_existing_key_fails_without_overwriting(tmp_path):
    key = tmp_path / "local-zone-key"
    key.write_text("invalid", encoding="ascii")
    result = run_script(tmp_path)
    assert result.returncode != 0
    assert "Invalid local encryption key" in result.stderr
    assert key.read_text(encoding="ascii") == "invalid"


def test_missing_directory_fails(tmp_path):
    result = run_script(tmp_path / "missing")
    assert result.returncode != 0
    assert "Unable to prepare" in result.stderr
