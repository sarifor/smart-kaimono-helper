"""Shared fixtures for smart-kaimono-helper tests."""
import os
from dotenv import load_dotenv

# shop.py requires ANTHROPIC_API_KEY at import time.
# Load .env first; fall back to a dummy so non-smoke tests can import shop.
load_dotenv()
if not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = "test-dummy-key"

import json
import pytest


# ── Mock helpers ──────────────────────────────────────────────────────────────

class _TextBlock:
    """Minimal stand-in for anthropic.types.TextBlock."""
    def __init__(self, text: str):
        self.text = text


class MockResponse:
    """Minimal stand-in for anthropic.types.Message."""
    def __init__(self, text: str):
        self.content = [_TextBlock(text)]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_response():
    """Factory: mock_response("json text") -> MockResponse instance."""
    return MockResponse


@pytest.fixture
def sample_prices():
    """Realistic subset of prices.json."""
    return {
        "version": "2026-04",
        "source": "テスト価格参考表",
        "items": [
            {"jp": "だし巻き卵 惣菜", "kr": "계란말이 반찬", "category": "惣菜", "price": 230},
            {"jp": "レトルトカレー 1食", "kr": "레토르트 카레 1인분", "category": "インスタント", "price": 165},
            {"jp": "冷凍うどん 5食", "kr": "냉동 우동 5인분", "category": "冷凍食品", "price": 230},
            {"jp": "カット野菜サラダ 1袋", "kr": "샐러드용 컷 야채 1봉지", "category": "野菜・果物", "price": 120},
            {"jp": "卵 10個", "kr": "계란 10개", "category": "乳製品・卵", "price": 230},
        ],
    }


@pytest.fixture
def prices_json_path(tmp_path, sample_prices):
    """Write sample prices.json to tmp_path and return the path string."""
    p = tmp_path / "prices.json"
    p.write_text(json.dumps(sample_prices, ensure_ascii=False), encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_items():
    """Shopping agent-style item list."""
    return [
        {"jp": "だし巻き卵 惣菜", "kr": "계란말이 반찬", "category": "惣菜",
         "price_est": 230, "price_source": "reference"},
        {"jp": "レトルトカレー 1食", "kr": "레토르트 카레 1인분", "category": "インスタント",
         "price_est": 165, "price_source": "reference"},
        {"jp": "冷凍うどん 5食", "kr": "냉동 우동 5인분", "category": "冷凍食品",
         "price_est": 230, "price_source": "reference"},
        {"jp": "カット野菜サラダ 1袋", "kr": "샐러드용 컷 야채 1봉지", "category": "野菜・果物",
         "price_est": 120, "price_source": "inferred"},
    ]


@pytest.fixture
def sample_keywords():
    """7-keyword list matching generate_keywords() output structure."""
    return [
        {"jp": "春の味覚", "kr": "봄의 맛", "type": "normal"},
        {"jp": "お花見弁当", "kr": "꽃놀이 도시락", "type": "normal"},
        {"jp": "新生活応援", "kr": "새 생활 응원", "type": "normal"},
        {"jp": "今週のトレンド食品", "kr": "이번 주 트렌드 식품", "type": "trend"},
        {"jp": "今週のおすすめ惣菜・冷凍食品", "kr": "이번 주 추천 반찬·냉동식품", "type": "souzai"},
        {"jp": "あなたの好みベースで", "kr": "내 취향 기반 추천", "type": "pref"},
        {"jp": "おまかせ", "kr": "알아서 해줘", "type": "random"},
    ]
