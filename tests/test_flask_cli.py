import subprocess
import sys
from pathlib import Path


def test_flask_cli_can_import_application():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "flask", "--app", "app", "routes"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "health" in result.stdout
    assert "/ask" in result.stdout
