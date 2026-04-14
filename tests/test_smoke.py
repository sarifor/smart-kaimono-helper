"""Smoke tests -- real Anthropic API calls. Run with: pytest -m smoke -v

WARNING: These tests cost real money (a few cents per run).
Requires ANTHROPIC_API_KEY in .env or environment.
"""
import json
import os
import re
from pathlib import Path

import pytest

import shop

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.smoke


def _load_project_file(name: str) -> str | None:
    p = PROJECT_ROOT / name
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return None


def _load_project_prices() -> dict | None:
    p = PROJECT_ROOT / "prices.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _require_real_key():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key == "test-dummy-key":
        pytest.skip("ANTHROPIC_API_KEY not set -- skipping smoke test")


class TestSmokeKo:
    def test_full_flow_ko(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        lang = "ko"
        t = shop.UI[lang]
        budget = 1000

        prices = _load_project_prices()
        assert prices is not None, "prices.json required"

        trend_md = _load_project_file("trend_kr.md") or "트렌드 없음"
        pref_md = _load_project_file("preferences_kr.md")

        # 1) Keywords
        keywords = shop.generate_keywords("4月13日（日曜日）、春", lang,
                                          trend_md, pref_md, t)
        assert len(keywords) >= 6
        for kw in keywords:
            assert "jp" in kw and "kr" in kw

        # 2) Shopping
        preferences = shop.parse_input("1", keywords)
        original, shopper_comment = shop.generate_original(budget, preferences, lang, pref_md, prices)
        assert isinstance(original, list) and len(original) > 0
        assert isinstance(shopper_comment, str)
        for item in original:
            assert "price_est" in item
            assert "price_source" in item
            # kr field should contain Korean
            assert re.search(r"[\uac00-\ud7a3]", item["kr"]), \
                f"No Korean in kr: {item['kr']}"

        # 3) Health
        advice = shop.health_check(original, budget, lang, prices)
        assert "comment" in advice
        assert re.search(r"[\uac00-\ud7a3]", advice["comment"]), \
            "Health comment not in Korean"

        # 4) Save
        improved = shop.apply_health(original, advice)
        path = shop.save_cart_markdown(lang, budget, "테스트", shopper_comment, advice, improved)
        assert path.exists()


class TestSmokeJa:
    def test_full_flow_ja(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        lang = "ja"
        t = shop.UI[lang]
        budget = 1000

        prices = _load_project_prices()
        assert prices is not None, "prices.json required"

        trend_md = _load_project_file("trend_jp.md") or "トレンドなし"
        pref_md = _load_project_file("preferences_jp.md")

        # 1) Keywords
        keywords = shop.generate_keywords("4月13日（日曜日）、春", lang,
                                          trend_md, pref_md, t)
        assert len(keywords) >= 6

        # 2) Shopping
        preferences = shop.parse_input("1", keywords)
        original, shopper_comment = shop.generate_original(budget, preferences, lang, pref_md, prices)
        assert isinstance(original, list) and len(original) > 0
        assert isinstance(shopper_comment, str)
        for item in original:
            assert "price_est" in item
            assert "price_source" in item

        # 3) Health
        advice = shop.health_check(original, budget, lang, prices)
        assert "comment" in advice
        # Japanese check (hiragana / katakana / kanji)
        assert re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]",
                         advice["comment"]), "Health comment not in Japanese"
        # Should NOT contain Korean
        assert not re.search(r"[\uac00-\ud7a3]", advice["comment"]), \
            "Korean found in Japanese mode comment"

        # 4) Save
        improved = shop.apply_health(original, advice)
        path = shop.save_cart_markdown(lang, budget, "テスト", shopper_comment, advice, improved)
        assert path.exists()
