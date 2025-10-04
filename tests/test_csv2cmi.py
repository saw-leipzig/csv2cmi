import runpy
import sys
from pathlib import Path
from xml.etree.ElementTree import parse

import pytest


@pytest.fixture
def csv_file() -> Path:
    csv_path = Path(__file__).parent / "data" / "test.csv"
    return csv_path


@pytest.fixture
def temp_output_file(tmp_path: Path) -> Path:
    return tmp_path / "output.xml"


def test_cli_conversion(csv_file: Path, temp_output_file: Path, monkeypatch: pytest.MonkeyPatch):
    # Simulate CLI call
    sys_argv = ["csv2cmi.py", str(csv_file), "-o", str(temp_output_file)]
    monkeypatch.setattr(sys, "argv", sys_argv)
    runpy.run_module("csv2cmi", run_name="__main__")
    assert temp_output_file.exists()
    # Check XML root
    tree = parse(temp_output_file)
    root = tree.getroot()
    assert root.tag == "{http://www.tei-c.org/ns/1.0}TEI"


def test_missing_file(monkeypatch: pytest.MonkeyPatch):
    sys_argv = ["csv2cmi.py", "nonexistent.csv"]
    monkeypatch.setattr(sys, "argv", sys_argv)
    with pytest.raises(SystemExit):
        runpy.run_module("csv2cmi", run_name="__main__")
