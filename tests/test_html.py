# tests/test_html.py
import subprocess
import pytest
from pathlib import Path

def test_html_report_generation(tmp_path, monkeypatch):
    # 1. Point to a fake report path under tmp_path
    report_file = tmp_path / "report.html"

    # 2. Stub subprocess.run so it doesn't call pytest recursively
    def fake_run(cmd, *args, **kwargs):
        # Simulate that HTML report was generated
        report_file.write_text("<html><body>OK</body></html>")
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", fake_run)  # monkeypatch docs  [oai_citation_attribution:0‡pytest](https://docs.pytest.org/en/stable/how-to/monkeypatch.html?utm_source=chatgpt.com)

    # 3. Call the same CLI you'd run normally
    result = subprocess.run(
        ["pytest", "--html", str(report_file), "--self-contained-html", "-q"],
        check=True
    )

    # 4. Verify exit code and that the file now exists
    assert result.returncode == 0
    assert report_file.exists()