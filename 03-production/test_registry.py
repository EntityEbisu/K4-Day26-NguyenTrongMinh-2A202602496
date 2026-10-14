"""Test cho ToolRegistry — chạy: ../.venv/Scripts/python.exe -m pytest test_registry.py -v"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from registry_client import ToolRegistry

REG = ToolRegistry()


def test_search_tag_weather_tra_ve_2_tool():
    names = {r["tool"] for r in REG.search(tag="weather")}
    assert names == {"get_weather", "get_weather_v2"}


def test_best_match_chon_version_cao_nhat():
    best = REG.best_match(tag="weather")
    assert best["tool"] == "get_weather_v2"
    assert best["version"] == "2.0.0"
    assert best["deprecated"] is False
