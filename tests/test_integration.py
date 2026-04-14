"""Integration tests -- API calls mocked via unittest.mock."""
import json
import re
from unittest.mock import patch

import pytest

import shop
from conftest import MockResponse


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock(text: str) -> MockResponse:
    return MockResponse(text)


MOCK_KW_KO = json.dumps([
    {"jp": "春の味覚", "kr": "봄의 맛", "type": "normal"},
    {"jp": "お花見弁当", "kr": "꽃놀이 도시락", "type": "normal"},
    {"jp": "新生活応援", "kr": "새 생활 응원", "type": "normal"},
], ensure_ascii=False)

MOCK_KW_JA = json.dumps([
    {"jp": "春の味覚", "kr": "春の味覚", "type": "normal"},
    {"jp": "お花見弁当", "kr": "お花見弁当", "type": "normal"},
    {"jp": "新生活応援", "kr": "新生活応援", "type": "normal"},
], ensure_ascii=False)

MOCK_SHOP_KO = json.dumps({
    "comment": "매운맛 가득한 라인업으로 채워봤어요!",
    "items": [
        {"jp": "だし巻き卵 惣菜", "kr": "계란말이 반찬", "category": "惣菜",
         "price_est": 230, "price_source": "reference"},
        {"jp": "レトルトカレー 1食", "kr": "레토르트 카레 1인분", "category": "インスタント",
         "price_est": 165, "price_source": "reference"},
        {"jp": "冷凍うどん 5食", "kr": "냉동 우동 5인분", "category": "冷凍食品",
         "price_est": 230, "price_source": "reference"},
        {"jp": "カット野菜サラダ 1袋", "kr": "샐러드용 컷 야채 1봉지", "category": "野菜・果物",
         "price_est": 120, "price_source": "inferred"},
    ],
}, ensure_ascii=False)

MOCK_SHOP_JA = json.dumps({
    "comment": "辛いもの尽くしで揃えてみました！",
    "items": [
        {"jp": "だし巻き卵 惣菜", "kr": "だし巻き卵 惣菜", "category": "惣菜",
         "price_est": 230, "price_source": "reference"},
        {"jp": "レトルトカレー 1食", "kr": "レトルトカレー 1食", "category": "インスタント",
         "price_est": 165, "price_source": "reference"},
        {"jp": "冷凍うどん 5食", "kr": "冷凍うどん 5食", "category": "冷凍食品",
         "price_est": 230, "price_source": "reference"},
        {"jp": "カット野菜サラダ 1袋", "kr": "カット野菜サラダ 1袋", "category": "野菜・果物",
         "price_est": 120, "price_source": "inferred"},
    ],
}, ensure_ascii=False)

MOCK_HEALTH_KO = json.dumps({
    "comment": "단백질이 부족해요. 냉동 닭가슴살을 추가하면 균형이 좋아질 거예요.",
    "add": [{"jp": "冷凍サラダチキン 1袋", "kr": "냉동 닭가슴살 1봉지",
             "category": "冷凍食品", "price_est": 278, "price_source": "reference"}],
    "remove": [],
}, ensure_ascii=False)

MOCK_HEALTH_JA = json.dumps({
    "comment": "タンパク質が不足しています。冷凍サラダチキンを追加するとバランスが良くなります。",
    "add": [{"jp": "冷凍サラダチキン 1袋", "kr": "冷凍サラダチキン 1袋",
             "category": "冷凍食品", "price_est": 278, "price_source": "reference"}],
    "remove": [],
}, ensure_ascii=False)


def _kw_json(lang):
    return MOCK_KW_KO if lang == "ko" else MOCK_KW_JA

def _shop_json(lang):
    return MOCK_SHOP_KO if lang == "ko" else MOCK_SHOP_JA

def _health_json(lang):
    return MOCK_HEALTH_KO if lang == "ko" else MOCK_HEALTH_JA


# ═══════════════════════════════════════════════════════════════════════════════
# generate_keywords
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateKeywords:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_count_with_preferences(self, lang):
        t = shop.UI[lang]
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_kw_json(lang))):
            kws = shop.generate_keywords("4月13日", lang, "trend", "prefs", t)
        # 3 AI + trend + souzai + pref + random = 7
        assert len(kws) == 7

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_count_without_preferences(self, lang):
        t = shop.UI[lang]
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_kw_json(lang))):
            kws = shop.generate_keywords("4月13日", lang, "trend", None, t)
        # 3 AI + trend + souzai + random = 6 (no pref)
        assert len(kws) == 6

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_hardcoded_types(self, lang):
        t = shop.UI[lang]
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_kw_json(lang))):
            kws = shop.generate_keywords("4月13日", lang, "trend", "prefs", t)
        types = [kw["type"] for kw in kws]
        assert types[3] == "trend"
        assert types[4] == "souzai"
        assert types[5] == "pref"
        assert types[6] == "random"


# ═══════════════════════════════════════════════════════════════════════════════
# generate_original -- structure + language
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateOriginal:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_returns_items_with_required_fields(self, lang, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_shop_json(lang))):
            items, comment = shop.generate_original(1000, "テスト", lang, None, sample_prices)
        assert isinstance(items, list)
        assert isinstance(comment, str)
        assert len(comment) > 0
        for item in items:
            assert "jp" in item
            assert "kr" in item
            assert "price_est" in item
            assert item["price_source"] in ("reference", "inferred")

    @pytest.mark.parametrize("lang,expected_lang_str", [
        ("ko", "韓国語"), ("ja", "日本語"),
    ])
    def test_system_prompt_language(self, lang, expected_lang_str, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_shop_json(lang))) as mock_create:
            shop.generate_original(1000, "テスト", lang, None, sample_prices)
        system = mock_create.call_args.kwargs["system"]
        assert expected_lang_str in system


# ═══════════════════════════════════════════════════════════════════════════════
# health_check -- structure + language
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_returns_required_fields(self, lang, sample_items, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_health_json(lang))):
            advice = shop.health_check(sample_items, 1000, lang, sample_prices)
        assert "comment" in advice
        assert isinstance(advice.get("add"), list)
        assert isinstance(advice.get("remove"), list)

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_comment_has_content(self, lang, sample_items, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_health_json(lang))):
            advice = shop.health_check(sample_items, 1000, lang, sample_prices)
        assert len(advice["comment"]) > 0

    @pytest.mark.parametrize("lang,expected_lang_str", [
        ("ko", "韓国語"), ("ja", "日本語"),
    ])
    def test_system_prompt_language(self, lang, expected_lang_str,
                                    sample_items, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(_health_json(lang))) as mock_create:
            shop.health_check(sample_items, 1000, lang, sample_prices)
        system = mock_create.call_args.kwargs["system"]
        assert expected_lang_str in system

    def test_retry_on_comment_action_mismatch(self, sample_items, sample_prices):
        """comment mentions changes but remove/reduce are empty -> retry once."""
        bad_response = json.dumps({
            "comment": "컵라면을 빼고 채소를 추가하세요.",
            "add": [], "remove": [], "reduce": [],
        }, ensure_ascii=False)
        good_response = json.dumps({
            "comment": "컵라면을 빼고 채소를 추가하세요.",
            "add": [{"jp": "ほうれん草 1袋", "kr": "시금치 1봉지",
                      "category": "野菜・果物", "price_est": 140,
                      "price_source": "reference"}],
            "remove": ["レトルトカレー 1食"],
            "reduce": [],
        }, ensure_ascii=False)
        with patch.object(shop.client.messages, "create",
                          side_effect=[_mock(bad_response),
                                       _mock(good_response)]) as mock_create:
            advice = shop.health_check(sample_items, 1000, "ko", sample_prices)
        # Should have retried (2 API calls)
        assert mock_create.call_count == 2
        assert len(advice["remove"]) == 1

    def test_no_retry_when_actions_present(self, sample_items, sample_prices):
        """comment mentions changes and actions exist -> no retry."""
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(MOCK_HEALTH_KO)) as mock_create:
            shop.health_check(sample_items, 1000, "ko", sample_prices)
        assert mock_create.call_count == 1


# ═══════════════════════════════════════════════════════════════════════════════
# fetch_and_save_trend
# ═══════════════════════════════════════════════════════════════════════════════

class TestFetchAndSaveTrend:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_creates_trend_file(self, lang, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        t = shop.UI[lang]
        suffix = "kr" if lang == "ko" else "jp"
        with patch.object(shop.client.messages, "create",
                          return_value=_mock("トレンド情報テスト")):
            shop.fetch_and_save_trend(t, lang)
        trend_file = tmp_path / f"trend_{suffix}.md"
        assert trend_file.exists()
        content = trend_file.read_text(encoding="utf-8")
        assert "トレンド情報テスト" in content

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_trend_file_title_language(self, lang, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        t = shop.UI[lang]
        suffix = "kr" if lang == "ko" else "jp"
        with patch.object(shop.client.messages, "create",
                          return_value=_mock("テスト")):
            shop.fetch_and_save_trend(t, lang)
        content = (tmp_path / f"trend_{suffix}.md").read_text(encoding="utf-8")
        if lang == "ko":
            assert "일본 슈퍼 식품 트렌드" in content
        else:
            assert "日本スーパー食品トレンド" in content


# ═══════════════════════════════════════════════════════════════════════════════
# language separation
# ═══════════════════════════════════════════════════════════════════════════════

class TestLanguageSeparation:
    def test_ko_health_comment_no_japanese_only(self, sample_items, sample_prices):
        """ko mode health comment should contain Korean."""
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(MOCK_HEALTH_KO)):
            advice = shop.health_check(sample_items, 1000, "ko", sample_prices)
        assert re.search(r"[\uac00-\ud7a3]", advice["comment"]), \
            "Korean mode comment should contain Hangul"

    def test_ja_health_comment_no_korean(self, sample_items, sample_prices):
        """ja mode health comment should NOT contain Korean."""
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(MOCK_HEALTH_JA)):
            advice = shop.health_check(sample_items, 1000, "ja", sample_prices)
        assert not re.search(r"[\uac00-\ud7a3]", advice["comment"]), \
            "Japanese mode comment should not contain Hangul"

    def test_ko_shopping_kr_field_has_korean(self, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(MOCK_SHOP_KO)):
            items, _ = shop.generate_original(1000, "テスト", "ko", None, sample_prices)
        for item in items:
            assert re.search(r"[\uac00-\ud7a3]", item["kr"]), \
                f"ko mode kr field should have Korean: {item['kr']}"

    def test_ja_shopping_kr_field_no_korean(self, sample_prices):
        with patch.object(shop.client.messages, "create",
                          return_value=_mock(MOCK_SHOP_JA)):
            items, _ = shop.generate_original(1000, "テスト", "ja", None, sample_prices)
        for item in items:
            assert not re.search(r"[\uac00-\ud7a3]", item["kr"]), \
                f"ja mode kr field should not have Korean: {item['kr']}"


# ═══════════════════════════════════════════════════════════════════════════════
# end-to-end chain (all mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2EChain:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_full_chain(self, lang, tmp_path, monkeypatch, sample_prices):
        monkeypatch.chdir(tmp_path)
        t = shop.UI[lang]

        responses = [
            _mock(_kw_json(lang)),     # generate_keywords
            _mock(_shop_json(lang)),   # generate_original
            _mock(_health_json(lang)), # health_check
        ]

        with patch.object(shop.client.messages, "create", side_effect=responses):
            keywords = shop.generate_keywords("4月13日", lang, "trend", "prefs", t)
            preferences = shop.parse_input("1", keywords)
            prefs_display = shop.display_preferences("1", keywords, lang)
            original, shopper_comment = shop.generate_original(
                1000, preferences, lang, "prefs", sample_prices)
            advice = shop.health_check(original, 1000, lang, sample_prices)

        improved = shop.apply_health(original, advice)
        path = shop.save_cart_markdown(lang, 1000, prefs_display, shopper_comment, advice, improved)

        assert path.exists()
        content = path.read_text(encoding="utf-8")

        if lang == "ko":
            assert "장바구니" in content
            assert "예산" in content
        else:
            assert "買い物リスト" in content
            assert "予算" in content

        # Added item from health check should be present
        assert "冷凍サラダチキン" in content
