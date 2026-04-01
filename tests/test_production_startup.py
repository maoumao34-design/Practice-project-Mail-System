"""子进程测试：避免污染已缓存的 get_settings 与 app 单例。"""

import subprocess
import sys
from pathlib import Path


def test_production_rejects_default_secret_key_subprocess() -> None:
    root = Path(__file__).resolve().parents[1]
    script = f"""
import os
import sys
sys.path.insert(0, {str(root)!r})
os.environ["APP_ENV"] = "production"
os.environ["SECRET_KEY"] = "please-change-this-in-env"
from fastapi.testclient import TestClient
from server.main import app
try:
    with TestClient(app):
        pass
except RuntimeError as e:
    msg = str(e)
    if "SECRET_KEY" in msg or "生产环境" in msg:
        sys.exit(0)
    raise
sys.exit(1)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
