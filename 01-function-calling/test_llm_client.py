"""Test llm_client — không cần mạng.
Chạy: ../.venv/Scripts/python.exe -m pytest test_llm_client.py -v
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import pytest
import llm_client as lc


def test_model_ladder_uu_tien_primary_roi_fallback(monkeypatch):
    monkeypatch.setenv("OPENCODE_MODEL", "step-5-preview-free")
    monkeypatch.setenv("OPENCODE_FALLBACK_MODEL", "deepseek-v4.1-flash")
    assert lc.model_ladder() == ["step-5-preview-free", "deepseek-v4.1-flash"]


def test_model_ladder_bo_qua_fallback_trung_lap(monkeypatch):
    monkeypatch.setenv("OPENCODE_MODEL", "step-5-preview-free")
    monkeypatch.setenv("OPENCODE_FALLBACK_MODEL", "step-5-preview-free")
    assert lc.model_ladder() == ["step-5-preview-free"]


def test_build_client_thieu_key_thi_raise(monkeypatch):
    monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
    with pytest.raises(lc.LlmError):
        lc.build_client()


def test_build_client_placeholder_key_thi_raise(monkeypatch):
    monkeypatch.setenv("OPENCODE_API_KEY", "your_opencode_api_key_here")
    with pytest.raises(lc.LlmError):
        lc.build_client()


def test_attempts_uu_tien_effort_cho_model_du_phong(monkeypatch):
    monkeypatch.setenv("OPENCODE_MODEL", "step-5-preview-free")
    monkeypatch.setenv("OPENCODE_FALLBACK_MODEL", "deepseek-v4.1-flash")
    monkeypatch.setenv("OPENCODE_FALLBACK_EFFORT", "low")
    assert lc._attempts() == [
        ("step-5-preview-free", {}),
        ("deepseek-v4.1-flash", {"reasoning_effort": "low"}),
        ("deepseek-v4.1-flash", {}),
    ]
