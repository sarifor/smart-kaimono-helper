"""Unit tests -- pure logic, no API calls."""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import shop


# ═══════════════════════════════════════════════════════════════════════════════
# validate_budget
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateBudget:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_below_minimum_returns_false(self, lang, capsys):
        t = shop.UI[lang]
        assert shop.validate_budget(699, t) is False
        assert t["budget_too_low"] in capsys.readouterr().out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_exact_minimum_returns_true(self, lang):
        assert shop.validate_budget(700, shop.UI[lang]) is True

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_above_minimum_returns_true(self, lang):
        assert shop.validate_budget(3000, shop.UI[lang]) is True

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_zero_returns_false(self, lang):
        assert shop.validate_budget(0, shop.UI[lang]) is False

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_negative_returns_false(self, lang):
        assert shop.validate_budget(-100, shop.UI[lang]) is False


# ═══════════════════════════════════════════════════════════════════════════════
# _parse_llm_json
# ═══════════════════════════════════════════════════════════════════════════════

class TestParseLlmJson:
    def test_clean_array(self, mock_response):
        resp = mock_response('[{"jp": "卵", "kr": "계란"}]')
        result = shop._parse_llm_json(resp, "test")
        assert isinstance(result, list)
        assert result[0]["jp"] == "卵"

    def test_clean_dict(self, mock_response):
        resp = mock_response('{"comment": "ok", "add": [], "remove": []}')
        result = shop._parse_llm_json(resp, "test")
        assert isinstance(result, dict)
        assert result["comment"] == "ok"

    def test_leading_text(self, mock_response):
        resp = mock_response('Here is the list:\n[{"jp": "卵"}]')
        result = shop._parse_llm_json(resp, "test")
        assert result[0]["jp"] == "卵"

    def test_trailing_text(self, mock_response):
        resp = mock_response('[{"jp": "卵"}]\nHope this helps!')
        result = shop._parse_llm_json(resp, "test")
        assert result[0]["jp"] == "卵"

    def test_code_fence(self, mock_response):
        resp = mock_response('```json\n[{"jp": "卵"}]\n```')
        result = shop._parse_llm_json(resp, "test")
        assert result[0]["jp"] == "卵"

    def test_broken_json_raises(self, mock_response):
        resp = mock_response('[{"jp": "卵"')
        with pytest.raises(RuntimeError, match="JSON 파싱 실패"):
            shop._parse_llm_json(resp, "test")

    def test_empty_text_raises(self, mock_response):
        resp = mock_response("")
        with pytest.raises(RuntimeError, match="빈 응답"):
            shop._parse_llm_json(resp, "test")

    def test_no_json_raises(self, mock_response):
        resp = mock_response("This is just plain text with no JSON.")
        with pytest.raises(RuntimeError, match="JSON 시작 문자"):
            shop._parse_llm_json(resp, "test")

    def test_whitespace_only_raises(self, mock_response):
        resp = mock_response("   \n\t  ")
        with pytest.raises(RuntimeError, match="빈 응답"):
            shop._parse_llm_json(resp, "test")


# ═══════════════════════════════════════════════════════════════════════════════
# is_trend_stale
# ═══════════════════════════════════════════════════════════════════════════════

class TestIsTrendStale:
    def test_missing_file(self, tmp_path):
        assert shop.is_trend_stale(str(tmp_path / "nope.md")) is True

    def test_fresh_file(self, tmp_path):
        p = tmp_path / "trend.md"
        p.write_text("fresh", encoding="utf-8")
        assert shop.is_trend_stale(str(p)) is False

    def test_stale_file(self, tmp_path):
        p = tmp_path / "trend.md"
        p.write_text("old", encoding="utf-8")
        old_time = (datetime.now() - timedelta(days=8)).timestamp()
        os.utime(str(p), (old_time, old_time))
        assert shop.is_trend_stale(str(p)) is True

    def test_empty_but_recent_file(self, tmp_path):
        p = tmp_path / "trend.md"
        p.write_text("", encoding="utf-8")
        # Function only checks mtime, not content
        assert shop.is_trend_stale(str(p)) is False


# ═══════════════════════════════════════════════════════════════════════════════
# load_file
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoadFile:
    def test_existing_file(self, tmp_path):
        p = tmp_path / "hello.md"
        p.write_text("hello world", encoding="utf-8")
        assert shop.load_file(str(p)) == "hello world"

    def test_missing_file(self, tmp_path):
        assert shop.load_file(str(tmp_path / "nope.md")) is None

    def test_strips_whitespace(self, tmp_path):
        p = tmp_path / "padded.md"
        p.write_text("  content  \n\n", encoding="utf-8")
        assert shop.load_file(str(p)) == "content"


# ═══════════════════════════════════════════════════════════════════════════════
# load_prices / format_prices_for_prompt
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoadPrices:
    def test_valid_json(self, prices_json_path):
        result = shop.load_prices(prices_json_path)
        assert result is not None
        assert "items" in result
        assert len(result["items"]) == 5

    def test_missing_file(self, tmp_path):
        assert shop.load_prices(str(tmp_path / "nope.json")) is None

    def test_broken_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{broken", encoding="utf-8")
        assert shop.load_prices(str(p)) is None


class TestFormatPricesForPrompt:
    def test_normal(self, sample_prices):
        result = shop.format_prices_for_prompt(sample_prices)
        assert "テスト価格参考表" in result
        assert "だし巻き卵" in result
        assert "約230円" in result

    def test_empty_dict(self):
        assert shop.format_prices_for_prompt({}) == ""

    def test_no_items_key(self):
        assert shop.format_prices_for_prompt({"source": "x"}) == ""

    def test_none(self):
        assert shop.format_prices_for_prompt(None) == ""


# ═══════════════════════════════════════════════════════════════════════════════
# _get_cat_map
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCatMap:
    def test_keys_match(self):
        ko = shop._get_cat_map("ko")
        ja = shop._get_cat_map("ja")
        assert set(ko.keys()) == set(ja.keys())
        assert len(ko) == 9

    def test_ko_labels_contain_korean(self):
        for label in shop._get_cat_map("ko").values():
            assert re.search(r"[\uac00-\ud7a3]", label), f"No Korean in: {label}"

    def test_ja_labels_no_korean(self):
        for label in shop._get_cat_map("ja").values():
            assert not re.search(r"[\uac00-\ud7a3]", label), f"Korean found in: {label}"


# ═══════════════════════════════════════════════════════════════════════════════
# parse_input / display_preferences
# ═══════════════════════════════════════════════════════════════════════════════

class TestParseInput:
    def test_single_number(self, sample_keywords):
        assert shop.parse_input("1", sample_keywords) == "春の味覚"

    def test_combo(self, sample_keywords):
        assert shop.parse_input("1+2", sample_keywords) == "春の味覚、お花見弁当"

    def test_free_text(self, sample_keywords):
        assert shop.parse_input("매운 거 위주", sample_keywords) == "매운 거 위주"

    def test_out_of_range_single(self, sample_keywords):
        # Beyond length -> treated as free text
        assert shop.parse_input("99", sample_keywords) == "99"

    def test_combo_with_out_of_range(self, sample_keywords):
        # 1 is valid, 99 is skipped
        result = shop.parse_input("1+99", sample_keywords)
        assert result == "春の味覚"


class TestDisplayPreferences:
    @pytest.mark.parametrize("lang,field", [("ko", "kr"), ("ja", "jp")])
    def test_single_number(self, lang, field, sample_keywords):
        result = shop.display_preferences("1", sample_keywords, lang)
        assert result == sample_keywords[0][field]

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_combo_separator(self, lang, sample_keywords):
        result = shop.display_preferences("1+2", sample_keywords, lang)
        if lang == "ko":
            assert "봄의 맛" in result and "꽃놀이 도시락" in result
            assert ", " in result
        else:
            assert "春の味覚" in result and "お花見弁当" in result
            assert "、" in result

    def test_free_text_passthrough(self, sample_keywords):
        assert shop.display_preferences("매운 거", sample_keywords, "ko") == "매운 거"


# ═══════════════════════════════════════════════════════════════════════════════
# apply_health
# ═══════════════════════════════════════════════════════════════════════════════

class TestApplyHealth:
    def test_remove(self, sample_items):
        advice = {"remove": ["だし巻き卵 惣菜"], "add": []}
        result = shop.apply_health(sample_items, advice)
        removed = [i for i in result if i["status"] == "removed"]
        assert len(removed) == 1
        assert removed[0]["jp"] == "だし巻き卵 惣菜"

    def test_add(self, sample_items):
        new_item = {"jp": "バナナ 1房", "kr": "바나나 1송이", "category": "野菜・果物",
                     "price_est": 165, "price_source": "reference"}
        advice = {"remove": [], "add": [new_item]}
        result = shop.apply_health(sample_items, advice)
        added = [i for i in result if i["status"] == "added"]
        assert len(added) == 1
        assert added[0]["jp"] == "バナナ 1房"

    def test_duplicate_add_ignored(self, sample_items):
        dup = {"jp": "だし巻き卵 惣菜", "kr": "계란말이 반찬", "category": "惣菜",
               "price_est": 230, "price_source": "reference"}
        advice = {"remove": [], "add": [dup]}
        result = shop.apply_health(sample_items, advice)
        assert len(result) == len(sample_items)

    def test_partial_remove_duplicates(self):
        """Remove 2 out of 3 identical items."""
        items = [
            {"jp": "カップ麺 1個", "kr": "컵라면 1개", "price_est": 140, "price_source": "reference"},
            {"jp": "カップ麺 1個", "kr": "컵라면 1개", "price_est": 140, "price_source": "reference"},
            {"jp": "カップ麺 1個", "kr": "컵라면 1개", "price_est": 140, "price_source": "reference"},
        ]
        advice = {"remove": ["カップ麺 1個", "カップ麺 1個"], "add": []}
        result = shop.apply_health(items, advice)
        removed = [i for i in result if i["status"] == "removed"]
        kept = [i for i in result if i["status"] == "kept"]
        assert len(removed) == 2
        assert len(kept) == 1

    def test_reduce(self, sample_items):
        """Reduce quantity: item stays with new values and status='reduced'."""
        advice = {
            "remove": [], "add": [],
            "reduce": [{"from": "だし巻き卵 惣菜",
                         "jp": "だし巻き卵 惣菜 1個", "kr": "계란말이 반찬 1개",
                         "category": "惣菜", "price_est": 115, "price_source": "reference"}],
        }
        result = shop.apply_health(sample_items, advice)
        reduced = [i for i in result if i["status"] == "reduced"]
        assert len(reduced) == 1
        assert reduced[0]["jp"] == "だし巻き卵 惣菜 1個"
        assert reduced[0]["price_est"] == 115

    def test_reduce_and_remove_together(self, sample_items):
        """Reduce one item and remove another in same advice."""
        advice = {
            "remove": ["レトルトカレー 1食"],
            "add": [],
            "reduce": [{"from": "だし巻き卵 惣菜",
                         "jp": "だし巻き卵 惣菜 1個", "kr": "계란말이 반찬 1개",
                         "category": "惣菜", "price_est": 115, "price_source": "reference"}],
        }
        result = shop.apply_health(sample_items, advice)
        reduced = [i for i in result if i["status"] == "reduced"]
        removed = [i for i in result if i["status"] == "removed"]
        assert len(reduced) == 1
        assert len(removed) == 1
        assert removed[0]["jp"] == "レトルトカレー 1食"

    def test_empty_advice(self, sample_items):
        advice = {"remove": [], "add": []}
        result = shop.apply_health(sample_items, advice)
        assert all(i["status"] == "kept" for i in result)
        assert len(result) == len(sample_items)

    def test_remove_nonexistent_item(self, sample_items):
        advice = {"remove": ["存在しない商品"], "add": []}
        result = shop.apply_health(sample_items, advice)
        assert all(i["status"] == "kept" for i in result)

    def test_missing_keys_defaults(self, sample_items):
        advice = {}
        result = shop.apply_health(sample_items, advice)
        assert len(result) == len(sample_items)
        assert all(i["status"] == "kept" for i in result)


# ═══════════════════════════════════════════════════════════════════════════════
# save_cart_markdown
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveCartMarkdown:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_creates_directory_and_file(self, lang, tmp_path, monkeypatch, sample_items):
        monkeypatch.chdir(tmp_path)
        advice = {"comment": "テストコメント" if lang == "ja" else "테스트 코멘트"}
        improved = [dict(i, status="kept") for i in sample_items]
        path = shop.save_cart_markdown(lang, 1000, "テスト", "", advice, improved)
        assert path.exists()
        assert (tmp_path / "carts").is_dir()

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_filename_format(self, lang, tmp_path, monkeypatch, sample_items):
        monkeypatch.chdir(tmp_path)
        advice = {"comment": "ok"}
        improved = [dict(i, status="kept") for i in sample_items]
        path = shop.save_cart_markdown(lang, 1000, "test", "", advice, improved)
        assert re.match(r"cart_\d{4}-\d{2}-\d{2}_\d{6}\.md", path.name)

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_content_language(self, lang, tmp_path, monkeypatch, sample_items):
        monkeypatch.chdir(tmp_path)
        advice = {"comment": "テストコメント" if lang == "ja" else "테스트 코멘트"}
        improved = [dict(i, status="kept") for i in sample_items]
        path = shop.save_cart_markdown(lang, 1000, "test", "", advice, improved)
        content = path.read_text(encoding="utf-8")
        if lang == "ko":
            assert "장바구니" in content
            assert "예산" in content
            assert "합계" in content.lower() or "합계" in content
        else:
            assert "買い物リスト" in content
            assert "予算" in content
            assert "合計" in content

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_utf8_roundtrip(self, lang, tmp_path, monkeypatch, sample_items):
        monkeypatch.chdir(tmp_path)
        advice = {"comment": "日本語テスト 한국어테스트"}
        improved = [dict(i, status="kept") for i in sample_items]
        path = shop.save_cart_markdown(lang, 1000, "test", "", advice, improved)
        content = path.read_text(encoding="utf-8")
        # jp field is always displayed
        assert "だし巻き卵" in content
        # kr field is displayed only in ko mode (label format: "jp (kr)")
        if lang == "ko":
            assert "계란말이" in content
        # comment contains both scripts regardless of mode
        assert "한국어테스트" in content


# ═══════════════════════════════════════════════════════════════════════════════
# print_summary
# ═══════════════════════════════════════════════════════════════════════════════

class TestPrintSummary:
    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_over_budget(self, lang, capsys):
        t = shop.UI[lang]
        items = [
            {"price_est": 600, "price_source": "reference", "status": "kept"},
            {"price_est": 500, "price_source": "reference", "status": "kept"},
        ]
        shop.print_summary(items, 1000, t)
        out = capsys.readouterr().out
        assert "+100" in out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_under_budget(self, lang, capsys):
        t = shop.UI[lang]
        items = [
            {"price_est": 400, "price_source": "reference", "status": "kept"},
            {"price_est": 300, "price_source": "reference", "status": "kept"},
        ]
        shop.print_summary(items, 1000, t)
        out = capsys.readouterr().out
        assert "-300" in out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_exact_budget(self, lang, capsys):
        t = shop.UI[lang]
        items = [{"price_est": 1000, "price_source": "reference", "status": "kept"}]
        shop.print_summary(items, 1000, t)
        assert "±0" in capsys.readouterr().out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_removed_items_excluded(self, lang, capsys):
        t = shop.UI[lang]
        items = [
            {"price_est": 500, "price_source": "reference", "status": "kept"},
            {"price_est": 9999, "price_source": "reference", "status": "removed"},
        ]
        shop.print_summary(items, 1000, t)
        out = capsys.readouterr().out
        # Total should be 500, not 10499
        assert "500" in out
        assert "9999" not in out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_inferred_warning_shown(self, lang, capsys):
        t = shop.UI[lang]
        # 2 out of 3 are inferred -> 2*2=4 > 3 -> warning
        items = [
            {"price_est": 300, "price_source": "inferred", "status": "kept"},
            {"price_est": 300, "price_source": "inferred", "status": "kept"},
            {"price_est": 300, "price_source": "reference", "status": "kept"},
        ]
        shop.print_summary(items, 1000, t)
        assert t["inferred_warn"] in capsys.readouterr().out

    @pytest.mark.parametrize("lang", ["ko", "ja"])
    def test_no_inferred_warning_below_threshold(self, lang, capsys):
        t = shop.UI[lang]
        # 1 out of 4 inferred -> 1*2=2 > 4? No -> no warning
        items = [
            {"price_est": 250, "price_source": "inferred", "status": "kept"},
            {"price_est": 250, "price_source": "reference", "status": "kept"},
            {"price_est": 250, "price_source": "reference", "status": "kept"},
            {"price_est": 250, "price_source": "reference", "status": "kept"},
        ]
        shop.print_summary(items, 1000, t)
        assert t["inferred_warn"] not in capsys.readouterr().out

    def test_zero_total_no_output(self, capsys):
        items = [{"price_est": 0, "status": "kept"}]
        shop.print_summary(items, 1000, shop.UI["ko"])
        assert capsys.readouterr().out == ""


# ═══════════════════════════════════════════════════════════════════════════════
# UI key symmetry
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommentSuggestsChanges:
    def test_korean_action_words(self):
        assert shop._comment_suggests_changes("컵라면을 빼고 채소를 추가하세요.")
        assert shop._comment_suggests_changes("하겐다즈를 줄이세요.")
        assert shop._comment_suggests_changes("고로케 대신 시금치를.")

    def test_japanese_action_words(self):
        assert shop._comment_suggests_changes("カップ麺を減らしましょう。")
        assert shop._comment_suggests_changes("コロッケを削除してください。")

    def test_no_action_words(self):
        assert not shop._comment_suggests_changes("バランスが良いですね！")
        assert not shop._comment_suggests_changes("균형 잡힌 식단이에요!")


class TestValidateHealthAdvice:
    def test_filters_nonexistent_removes(self):
        advice = {"comment": "ok", "remove": ["存在する", "存在しない"], "add": [], "reduce": []}
        result = shop._validate_health_advice(advice, {"存在する"})
        assert result["remove"] == ["存在する"]

    def test_filters_nonexistent_reduces(self):
        advice = {
            "comment": "ok", "remove": [], "add": [],
            "reduce": [
                {"from": "存在する", "jp": "new", "kr": "new", "category": "惣菜",
                 "price_est": 100, "price_source": "reference"},
                {"from": "存在しない", "jp": "x", "kr": "x", "category": "惣菜",
                 "price_est": 50, "price_source": "inferred"},
            ],
        }
        result = shop._validate_health_advice(advice, {"存在する"})
        assert len(result["reduce"]) == 1


class TestUISymmetry:
    def test_ko_ja_keys_match(self):
        assert set(shop.UI["ko"].keys()) == set(shop.UI["ja"].keys())
