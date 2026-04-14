import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(".env에 ANTHROPIC_API_KEY가 없어요.")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ── 외부 파일 로드 ─────────────────────────────────────────────────────────────

def load_file(path: str) -> str | None:
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return None


def is_trend_stale(path: str, days: int = 7) -> bool:
    """파일이 없거나 mtime이 N일보다 오래됐으면 True."""
    p = Path(path)
    if not p.exists():
        return True
    mtime = datetime.fromtimestamp(p.stat().st_mtime)
    return datetime.now() - mtime > timedelta(days=days)


def load_prices(path: str = "prices.json") -> dict | None:
    """가격 참고표 로드. 없으면 None."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def format_prices_for_prompt(prices: dict) -> str:
    """LLM 프롬프트에 끼워 넣을 참조표 문자열 생성."""
    if not prices or "items" not in prices:
        return ""
    lines = [f"# {prices.get('source', '価格参考表')}"]
    # 카테고리별로 묶어서 출력
    by_cat: dict[str, list] = {}
    for item in prices["items"]:
        by_cat.setdefault(item["category"], []).append(item)
    for cat, items in by_cat.items():
        lines.append(f"\n## {cat}")
        for it in items:
            lines.append(f"- {it['jp']}: 約{it['price']}円")
    return "\n".join(lines)


def validate_budget(budget: int, t: dict) -> bool:
    """예산 검증. 넷슈퍼 최소 주문금액(700엔 세전) 미만이면 False."""
    MIN_ORDER = 700
    if budget < MIN_ORDER:
        print(t["budget_too_low"])
        return False
    return True


def fetch_and_save_trend(t: dict, lang: str) -> str:
    """웹 검색으로 일본 슈퍼 최신 트렌드 가져와서 trend_{kr,jp}.md에 저장"""
    print(t["trend_search"])
    if lang == "ko":
        user_prompt = "日本の最新スーパーマーケット食品トレンド（2026年）をウェブ検索して、箇条書きで簡潔にまとめてください。韓国語で。"
        title = "일본 슈퍼 식품 트렌드"
        updated = "업데이트"
    else:
        user_prompt = "日本の最新スーパーマーケット食品トレンド（2026年）をウェブ検索して、箇条書きで簡潔にまとめてください。日本語で。"
        title = "日本スーパー食品トレンド"
        updated = "更新"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        # 날짜는 도구 버전 ID (릴리스 날짜)이며 검색 데이터 범위와 무관 — 실시간 웹 검색을 수행한다.
        # 최신 버전: web_search_20260209 (동적 필터링 지원, 토큰 절감)
        # 참고: https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system="あなたは日本の食品トレンドリサーチャーです。",
        messages=[{"role": "user", "content": user_prompt}],
    )
    trend_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            trend_text = block.text
            break

    today = datetime.now().strftime("%Y-%m-%d")
    content = f"# {title} ({today} {updated})\n\n{trend_text.strip()}\n"
    suffix = "kr" if lang == "ko" else "jp"
    Path(f"trend_{suffix}.md").write_text(content, encoding="utf-8")
    return content.strip()


# ── UI 텍스트 ─────────────────────────────────────────────────────────────────

UI = {
    "ko": {
        "title":         "🛒  넷슈퍼 장바구니 목록 생성기",
        "budget":        "이번 주 예산 (엔, 배송비 제외, 세전): ",
        "keyword_gen":   "\n⏳ 오늘의 추천 키워드 생성 중...",
        "keyword_head":  "💡 오늘의 추천 키워드",
        "trend_label":   "🔥 트렌드",
        "souzai_label":  "🍱 반찬/냉동",
        "pref_label":    "📌 내 취향",
        "random_label":  "🎲 알아서",
        "trend_search":  "  ⏳ 최신 트렌드 웹 검색 중...",
        "input_example": (
            "\n입력 예시:\n"
            "  번호 선택    →  3\n"
            "  자유 입력    →  매운 거 위주\n"
            "  번호 조합    →  1+2  또는  2+5+6\n"
        ),
        "input_prompt":  "→ ",
        "generating":    "\n⏳ 쇼핑 에이전트가 리스트를 생성 중...",
        "health_check":  "⏳ 건강 에이전트가 검토 중...",
        "shopper_says":  "🛒 쇼핑 에이전트: 요청하신 대로 완성해봤어요.",
        "prices_loading":"✔ 가격 참고표 적용 ({count}개 품목)",
        "prices_missing":"❌ prices.json 파일이 없어요. shop.py와 같은 폴더에 준비해주세요.",
        "trend_stale":   "⏳ {path}가 7일 이상 지났어요. 최신 트렌드 재검색 중...",
        "cart_saved":    "📄 저장됨: {path}",
        "budget_too_low":"❌ 예산이 너무 낮아요. 이온 넷슈퍼 최소 주문금액은 700엔(세전)이에요.",
        "result_disclaimer": "ℹ️  AI가 추정한 가격이라 예산과 정확히 맞지 않을 수 있어요.",
        "summary":       "💰 합계 {total}엔 / 예산 {budget}엔 (오차 {diff})",
        "summary_fee":   "📦 모두 세전 금액, 배송비는 별도예요.",
        "inferred_warn": "⚠️  가격의 절반 이상이 추정치예요.",
        "health_says":   "💬 건강 에이전트: ",
        "legend":        "   ❌ 삭제  ➖ 감소  ➕ 추가",
        "improved":      "⭐ 추천 목록",
        "budget_error":  "숫자로 입력해주세요. 예: 3000",
        "no_category":   "기타",
    },
    "ja": {
        "title":         "🛒  ネットスーパー 買い物リスト生成",
        "budget":        "今週の予算（円、配送料別、税抜）: ",
        "keyword_gen":   "\n⏳ 本日のおすすめキーワードを生成中...",
        "keyword_head":  "💡 本日のおすすめキーワード",
        "trend_label":   "🔥 トレンド",
        "souzai_label":  "🍱 惣菜・冷凍",
        "pref_label":    "📌 あなたの好み",
        "random_label":  "🎲 おまかせ",
        "trend_search":  "  ⏳ 最新トレンドをウェブ検索中...",
        "input_example": (
            "\n入力例:\n"
            "  番号選択    →  3\n"
            "  自由入力    →  辛めで\n"
            "  番号組み合わせ →  1+2  または  2+5+6\n"
        ),
        "input_prompt":  "→ ",
        "generating":    "\n⏳ ショッピングエージェントがリストを生成中...",
        "health_check":  "⏳ 健康エージェントが確認中...",
        "shopper_says":  "🛒 ショッピングエージェント: ご要望通り完成させました。",
        "prices_loading":"✔ 価格参考表を適用 ({count}品目)",
        "prices_missing":"❌ prices.json が見つかりません。shop.py と同じフォルダに用意してください。",
        "trend_stale":   "⏳ {path} が7日以上経過しています。最新トレンドを再検索中...",
        "cart_saved":    "📄 保存しました: {path}",
        "budget_too_low":"❌ 予算が低すぎます。ネットスーパーの最低注文金額は700円（税抜）です。",
        "result_disclaimer": "ℹ️  AIが推定した価格のため、予算とぴったり一致しない場合があります。",
        "summary":       "💰 合計 {total}円 / 予算 {budget}円 (差額 {diff})",
        "summary_fee":   "📦 すべて税抜、配送料は別途です。",
        "inferred_warn": "⚠️  価格の半分以上が推定値です。",
        "health_says":   "💬 健康エージェント: ",
        "legend":        "   ❌ 削除  ➖ 減量  ➕ 追加",
        "improved":      "⭐ おすすめリスト",
        "budget_error":  "数字で入力してください。例: 3000",
        "no_category":   "その他",
    },
}

# ── 시스템 프롬프트 ────────────────────────────────────────────────────────────

def system_shopper(lang: str, preferences_md: str | None, prices: dict | None) -> str:
    reply_lang = "韓国語" if lang == "ko" else "日本語"
    pref_block = ""
    if preferences_md:
        pref_block = f"""
【ユーザーの好み・取向（必ず反映すること）】
{preferences_md}
"""
    price_block = ""
    if prices:
        price_block = f"""
【価格参考表（ネットスーパー実勢価格ベース・参考値・全て税抜）】
{format_prices_for_prompt(prices)}

※参考表にない商品は、類似商品から常識的に推論すること。
  例: バナナ1房=約165円 → マンゴー1個は約2倍の330円前後
  例: 一般的な葉物野菜1袋=100〜160円の範囲
※価格は全て本体価格（税抜）で扱うこと。
"""
    return f"""あなたは日本在住の一人暮らし向け食料品ショッピングアシスタントです。
ユーザーの予算と好みをもとに、ネットスーパーで買える商品リストを生成してください。
商品の選定・価格・数量はすべて日本の食品市場・日本語ウェブの情報を基準にしてください。
{pref_block}{price_block}
【入力について】
- ユーザーは韓国語・日本語・またはその混在で入力することがあります
- どの言語で入力されても、内容を正確に理解してください

【出力ルール】
- 商品名は必ず日本語で返す（ネットスーパーで検索できる表記）
- 翻訳は{reply_lang}で返す
- レトルト食品・冷凍食品・インスタント食品などの完成品を中心にする
- スーパーの惣菜や基本食材も適度に混ぜる
- **参考表にない商品も全体の2〜3割は含めること（日本のスーパーで実際に買える商品なら可）**
- **各商品に price_est（整数、円、税抜）を必ず付ける**
  - 参考表にある商品は参考表の価格を使う → price_source: "reference"
  - 参考表にない商品は類似商品から推論 → price_source: "inferred"
- **合計が予算の90〜110%になるように品数・数量を調整する（予算・価格は全て税抜、配送料は含まない）**
- 同じ商品を複数入れたい場合は数量をまとめて1行にする（✕ カップ麺 1個 を3行 → ○ カップ麺 3個 を1行、price_estも合計にする）
- 予算が余りすぎる場合は品数を増やすか、既存商品の数量を増やして予算に近づける
- 目安: 予算1000円→5〜7品、3000円→8〜12品、5000円→12〜15品、7000円以上→15〜20品
- 必ずJSON形式のみで返す:
{{"comment": "ユーザーのリクエストへの一言リアクション（{reply_lang}・1文）", "items": [商品リスト]}}
- commentはユーザーの入力内容・気分に合わせた短い感想（{reply_lang}のみ・1文・他の言語を混ぜない）
- items配列の各要素は以下の形式:
  {{"jp": "日本語商品名", "kr": "翻訳", "category": "カテゴリ", "price_est": 180, "price_source": "reference"}}
- categoryは以下から選ぶ: 惣菜, 冷凍食品, インスタント, 主食, 野菜・果物, 乳製品・卵, 缶詰・瓶詰, 間食, その他
例: {{"comment": "辛いもの尽くしで揃えてみました！", "items": [{{"jp": "だし巻き卵 惣菜", "kr": "계란말이 반찬", "category": "惣菜", "price_est": 250, "price_source": "reference"}}]}}"""


def system_health(lang: str, prices: dict | None) -> str:
    reply_lang = "韓国語" if lang == "ko" else "日本語"
    price_block = ""
    if prices:
        price_block = f"""

【価格参考表（ネットスーパー実勢価格ベース・参考値・全て税抜）】
{format_prices_for_prompt(prices)}

※参考表にある商品は参考表の価格をそのまま使う → price_source: "reference"
※参考表にない商品は類似商品から推論 → price_source: "inferred"
"""
    return f"""あなたは栄養士の健康アドバイザーです。
ショッピングリストを見て、健康面で気になる点があれば軽くツッコミを入れてください。
商品の評価はすべて日本の食品・栄養基準をもとに行ってください。
{price_block}
【ルール】
- 不足している栄養素（野菜・タンパク質など）や偏りがあれば指摘
- 必ず1〜2品は追加商品を提案する（野菜・果物・タンパク質など）
- 具体的にどの商品を追加・削除すればいいか提案する
- **commentは必ず以下の2文構成で{reply_lang}のみで書く（他の言語の文字を絶対に混ぜないこと）**:
  * 1文目: ショッピングエージェントへの一言（良い部分は認めつつ、どこが問題かを指摘）
  * 2文目: その問題の理由と、どう改善するかの具体的な提案
  * 例（日本語）: "タンパク質と野菜はしっかり入っていますね！ただ、卵系の商品が3つも重複していて間食も2つ入っています。炭水化物が多めなので、緑黄色野菜を1袋追加してバランスを取りましょう。"
  * 例（韓国語）: "단백질과 채소는 잘 챙겼네요! 다만 튀김류가 겹치고 간식도 2개라 지방 과잉이 걱정돼요. 고로케를 빼고 시금치 1봉지를 추가해서 비타민을 보충해 보세요."
  * ⚠ 韓国語モードでは日本語文字（カタカナ・ひらがな）を絶対に使わないこと。商品名は必ず韓国語訳で書く（例: カット野菜→컷 야채、冷凍うどん→냉동 우동）
- ツッコミは控えめに。全部否定せず、ちょっと改善するイメージ
- **removeする商品の合計金額に近い金額分をadd/reduceで補填すること（予算を大きく減らさない）**
- **commentで述べた削除・追加・減量の内容とremove/add/reduceの内容を完全に一致させること**
- **数量を減らしたい場合はremoveではなくreduceを使う**（removeは完全削除のみ）
- addする商品のcategoryは必ず以下から選ぶ（他の値は禁止）:
  惣菜, 冷凍食品, インスタント, 主食, 野菜・果物, 乳製品・卵, 缶詰・瓶詰, 間食, その他
- **add/reduceする商品には price_est（整数、円、税抜）と price_source（"reference" または "inferred"）を必ず付ける**
- 出力はJSON形式のみ:
{{
  "comment": "一言ツッコミ（{reply_lang}）",
  "add": [{{"jp": "追加商品名", "kr": "翻訳", "category": "カテゴリ", "price_est": 150, "price_source": "inferred"}}],
  "remove": ["完全に削除する商品名（任意）"],
  "reduce": [{{"from": "元の商品名", "jp": "新しい商品名（数量変更後）", "kr": "翻訳", "category": "カテゴリ", "price_est": 295, "price_source": "reference"}}]
}}
例: ハーゲンダッツ4個→2個にしたい場合:
  "reduce": [{{"from": "ハーゲンダッツ ミニカップ 4個", "jp": "ハーゲンダッツ ミニカップ 2個", "kr": "하겐다즈 미니컵 2개", "category": "間食", "price_est": 590, "price_source": "reference"}}]"""


def system_keywords(lang: str) -> str:
    reply_lang = "韓国語" if lang == "ko" else "日本語"
    return f"""あなたは日本在住の一人暮らし向け食料品ショッピングアシスタントです。
今日の日付・曜日・季節をもとに、ショッピングのインスピレーションになるキーワードを3つ提案してください。

【ルール】
- 季節感・曜日・気分・ライフスタイルをランダムに混ぜる
- 毎回違うキーワードになるようにする
- 各キーワードは短く（10文字以内）
- 出力はJSON配列のみ（3つ）。各要素は {{"jp": "日本語キーワード", "kr": "翻訳（{reply_lang}）", "type": "normal"}}
例: [{{"jp": "疲れ気味な日に", "kr": "피곤한 날에", "type": "normal"}}]"""


# ── 함수 ──────────────────────────────────────────────────────────────────────

def _parse_llm_json(response, label: str):
    """LLM 응답에서 텍스트 추출 + JSON 파싱. 앞뒤 잡음(설명·코멘트)에도 내성."""
    raw = ""
    for block in response.content:
        if hasattr(block, "text"):
            raw = block.text
            break
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    if not raw:
        raise RuntimeError(f"{label}: 빈 응답")

    # 첫 JSON 시작 위치 (`[` 또는 `{`) 탐색 — 앞에 설명이 붙어도 대응
    start = next((i for i, c in enumerate(raw) if c in "[{"), -1)
    if start < 0:
        preview = raw[:300]
        raise RuntimeError(f"{label}: JSON 시작 문자(`[` 또는 `{{`)를 찾지 못함\n응답 일부: {preview}")

    # raw_decode: 앞에서부터 유효한 JSON만 파싱하고 뒤에 남은 텍스트는 무시
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[start:])
        return obj
    except json.JSONDecodeError as e:
        # 길면 앞뒤만 보여줘서 어디가 문제인지 감 잡기 쉽게
        if len(raw) > 500:
            preview = f"{raw[:200]}\n...(중략)...\n{raw[-200:]}"
        else:
            preview = raw
        raise RuntimeError(
            f"{label}: JSON 파싱 실패 ({e.msg})\n응답 일부:\n{preview}"
        ) from e


def generate_keywords(today_str: str, lang: str, trend_md: str,
                      preferences_md: str | None, t: dict) -> list[dict]:
    # 1~3: 계절/트렌드 반영 키워드
    trend_context = f"\n\n【トレンド情報】\n{trend_md}"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system_keywords(lang),
        messages=[{"role": "user", "content": f"今日は{today_str}です。{trend_context}\n\nJSON配列のみ返してください。"}],
    )
    keywords = _parse_llm_json(response, "키워드 생성" if lang == "ko" else "キーワード生成")

    # 4: 트렌드
    keywords.append({
        "ko": {"jp": "今週のトレンド食品", "kr": "이번 주 트렌드 식품", "type": "trend"},
        "ja": {"jp": "今週のトレンド食品", "kr": "今週のトレンド食品", "type": "trend"},
    }[lang])

    # 5: 반찬/냉동
    keywords.append({
        "ko": {"jp": "今週のおすすめ惣菜・冷凍食品", "kr": "이번 주 추천 반찬·냉동식품", "type": "souzai"},
        "ja": {"jp": "今週のおすすめ惣菜・冷凍食品", "kr": "今週のおすすめ惣菜・冷凍食品", "type": "souzai"},
    }[lang])

    # 6: 개인 취향 (preferences_md 있을 때만)
    if preferences_md:
        keywords.append({
            "ko": {"jp": "あなたの好みベースで", "kr": "내 취향 기반 추천", "type": "pref"},
            "ja": {"jp": "あなたの好みベースで", "kr": "あなたの好みベースで", "type": "pref"},
        }[lang])

    # 마지막: 알아서 해줘 (선택 시 앞의 것 중 랜덤으로 대체됨)
    keywords.append({
        "ko": {"jp": "おまかせ", "kr": "알아서 해줘", "type": "random"},
        "ja": {"jp": "おまかせ", "kr": "おまかせ", "type": "random"},
    }[lang])

    return keywords


def parse_input(raw: str, keywords: list[dict]) -> str:
    """번호, 번호 조합(1+2), 자유 텍스트 모두 처리"""
    raw = raw.strip()

    # 번호 조합: 1+2+3
    if "+" in raw and all(p.strip().isdigit() for p in raw.split("+")):
        indices = [int(p.strip()) for p in raw.split("+")]
        parts = []
        for idx in indices:
            if 1 <= idx <= len(keywords):
                parts.append(keywords[idx - 1]["jp"])
        return "、".join(parts)

    # 단일 번호
    if raw.isdigit() and 1 <= int(raw) <= len(keywords):
        return keywords[int(raw) - 1]["jp"]

    # 자유 텍스트
    return raw


def display_preferences(raw: str, keywords: list[dict], lang: str) -> str:
    """표시용: lang=ko면 kr 버전으로 키워드 치환."""
    raw = raw.strip()
    field = "kr" if lang == "ko" else "jp"
    sep = ", " if lang == "ko" else "、"

    if "+" in raw and all(p.strip().isdigit() for p in raw.split("+")):
        indices = [int(p.strip()) for p in raw.split("+")]
        parts = [keywords[idx - 1][field] for idx in indices if 1 <= idx <= len(keywords)]
        return sep.join(parts)

    if raw.isdigit() and 1 <= int(raw) <= len(keywords):
        return keywords[int(raw) - 1][field]

    return raw


def generate_original(budget: int, preferences: str, lang: str, preferences_md: str | None, prices: dict | None) -> tuple[list[dict], str]:
    target_min = int(budget * 0.9)
    target_max = int(budget * 1.1)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_shopper(lang, preferences_md, prices),
        messages=[{"role": "user", "content": f"予算: {budget}円（税抜、食品のみ、配送料は別）\n目標合計: {target_min}〜{target_max}円\n要望: {preferences}\n\nJSON形式のみ返してください。"}],
    )
    result = _parse_llm_json(response, "쇼핑 에이전트" if lang == "ko" else "ショッピングエージェント")
    if isinstance(result, dict) and "items" in result:
        return result["items"], result.get("comment", "")
    return result, ""


def _comment_suggests_changes(comment: str) -> bool:
    """comment 텍스트가 삭제/감소를 언급하는지 휴리스틱 판별."""
    action_words = ["빼", "줄이", "줄여", "삭제", "제거", "대신",
                    "減ら", "削除", "抜", "除く", "代わり", "減量"]
    return any(w in comment for w in action_words)


def _validate_health_advice(advice: dict, original_names: set[str]) -> dict:
    """remove/reduce가 실제 원본 아이템을 참조하는지 검증."""
    advice.setdefault("remove", [])
    advice.setdefault("reduce", [])
    advice.setdefault("add", [])
    advice["remove"] = [n for n in advice["remove"] if n in original_names]
    advice["reduce"] = [r for r in advice["reduce"]
                        if isinstance(r, dict) and r.get("from") in original_names]
    return advice


def health_check(items: list[dict], budget: int, lang: str, prices: dict | None) -> dict:
    if lang == "ko":
        item_list = [f"{i['jp']}({i.get('kr', '')})" for i in items]
    else:
        item_list = [i["jp"] for i in items]

    label = "건강 에이전트" if lang == "ko" else "健康エージェント"
    user_msg = f"予算: {budget}円\nリスト: {item_list}\n\nJSON形式のみで返してください。"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_health(lang, prices),
        messages=[{"role": "user", "content": user_msg}],
    )
    advice = _parse_llm_json(response, label)

    # 검증: 존재하지 않는 아이템 필터링
    original_names = {item["jp"] for item in items}
    advice = _validate_health_advice(advice, original_names)

    # comment가 삭제/감소를 언급하는데 실제 action이 비어있으면 → 1회 재시도
    has_actions = bool(advice.get("remove")) or bool(advice.get("reduce"))
    if _comment_suggests_changes(advice.get("comment", "")) and not has_actions:
        names_list = "\n".join(f"- {n}" for n in sorted(original_names))
        retry_msg = ("commentで削除・減量について言及していますが、removeやreduceが空です。\n"
                     "以下の商品名リストから正確な名前をコピーしてremove/reduceに入れてください:\n"
                     f"{names_list}\n\n"
                     "commentの内容に合わせて同じJSON形式で返してください。")
        response2 = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_health(lang, prices),
            messages=[
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": json.dumps(advice, ensure_ascii=False)},
                {"role": "user", "content": retry_msg},
            ],
        )
        advice = _parse_llm_json(response2, label)
        advice = _validate_health_advice(advice, original_names)

    return advice


def apply_health(items: list[dict], advice: dict) -> list[dict]:
    remove_counts: dict[str, int] = {}
    for name in advice.get("remove", []):
        remove_counts[name] = remove_counts.get(name, 0) + 1

    reduce_map: dict[str, dict] = {}
    for entry in advice.get("reduce", []):
        if isinstance(entry, dict) and "from" in entry:
            reduce_map[entry["from"]] = entry

    updated = []
    for item in items:
        jp = item["jp"]
        if jp in reduce_map:
            new = reduce_map.pop(jp)
            updated.append({
                "jp": new.get("jp", jp),
                "kr": new.get("kr", item.get("kr", "")),
                "category": new.get("category", item.get("category", "")),
                "price_est": new.get("price_est", item.get("price_est", 0)),
                "price_source": new.get("price_source", item.get("price_source", "")),
                "status": "reduced",
            })
        elif jp in remove_counts and remove_counts[jp] > 0:
            updated.append({**item, "status": "removed"})
            remove_counts[jp] -= 1
        else:
            updated.append({**item, "status": "kept"})
    for item in advice.get("add", []):
        if isinstance(item, dict) and item["jp"] not in [i["jp"] for i in updated if i.get("status") != "removed"]:
            updated.append({**item, "status": "added"})
    return updated


def print_table_by_category(items: list[dict], lang: str = "ko", show_status: bool = False, no_category_label: str = "기타"):
    cat_map = _get_cat_map(lang)
    # その他 헤더만 사용자 지정 라벨로 덮어씌움
    cat_map = {**cat_map, "その他": f"📦 {no_category_label}"}
    groups: dict[str, list] = {}
    for item in items:
        cat = item.get("category", "その他")
        # cat_map에 없는 카테고리는 その他로 정규화 (헤더 중복 방지)
        if cat not in cat_map:
            cat = "その他"
        groups.setdefault(cat, []).append(item)

    num = 1
    for cat_key, cat_label in cat_map.items():
        if cat_key not in groups:
            continue
        print(f"\n{cat_label}")
        for item in groups[cat_key]:
            jp = item.get("jp", "")
            kr = item.get("kr", "")
            label = f"{jp} ({kr})" if lang == "ko" else jp
            # 가격 표시
            price = item.get("price_est")
            src = item.get("price_source", "")
            price_str = ""
            if isinstance(price, (int, float)) and price > 0:
                inferred_tag = " (추정)" if lang == "ko" else " (推定)"
                marker = inferred_tag if src == "inferred" else ""
                price_str = f"  ~{int(price)}円{marker}"
            if show_status:
                status = item.get("status", "kept")
                prefix = "❌" if status == "removed" else "➖" if status == "reduced" else "➕" if status == "added" else "  "
                print(f"  {num:>2}. {prefix} {label}{price_str}")
            else:
                print(f"  {num:>2}. {label}{price_str}")
            num += 1


def print_summary(items: list[dict], budget: int, t: dict):
    """예산 대비 합계 요약 출력 (removed 제외). 배송비는 별도."""
    visible = [i for i in items if i.get("status") != "removed"]
    total = sum(int(i.get("price_est") or 0) for i in visible)
    if total <= 0:
        return
    gap = total - budget
    if gap > 0:
        diff = f"+{gap}엔" if "엔" in t["summary"] else f"+{gap}円"
    elif gap < 0:
        diff = f"{gap}엔" if "엔" in t["summary"] else f"{gap}円"
    else:
        diff = "±0엔" if "엔" in t["summary"] else "±0円"
    print(t["summary"].format(total=total, budget=budget, diff=diff))
    print(t["summary_fee"])
    # 추정 비율 경고
    inferred = sum(1 for i in visible if i.get("price_source") == "inferred")
    if inferred > 0 and inferred * 2 > len(visible):
        print(t["inferred_warn"])


# 카테고리 라벨 맵 (print_table_by_category와 공유용)
def _get_cat_map(lang: str) -> dict:
    if lang == "ko":
        return {
            "惣菜":       "🍱 반찬",
            "冷凍食品":   "🧊 냉동식품",
            "インスタント": "🍜 인스턴트",
            "主食":       "🍚 주식",
            "野菜・果物": "🥦 야채·과일",
            "乳製品・卵": "🥚 유제품·달걀",
            "缶詰・瓶詰": "🥫 캔·통조림",
            "間食":       "🍬 간식",
            "その他":     "📦 기타",
        }
    return {
        "惣菜":       "🍱 惣菜",
        "冷凍食品":   "🧊 冷凍食品",
        "インスタント": "🍜 インスタント",
        "主食":       "🍚 主食",
        "野菜・果物": "🥦 野菜・果物",
        "乳製品・卵": "🥚 乳製品・卵",
        "缶詰・瓶詰": "🥫 缶詰・瓶詰",
        "間食":       "🍬 お菓子",
        "その他":     "📦 その他",
    }


def save_cart_markdown(lang: str, budget: int, preferences_display: str,
                       shopper_comment: str, advice: dict, improved: list[dict]) -> Path:
    """결과를 carts/cart_YYYY-MM-DD_HHMMSS.md에 저장 (개선 목록만)."""
    carts_dir = Path("carts")
    carts_dir.mkdir(exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    display_time = now.strftime("%Y-%m-%d %H:%M:%S")
    filepath = carts_dir / f"cart_{timestamp}.md"

    cat_map = _get_cat_map(lang)
    inferred_tag = " (추정)" if lang == "ko" else " (推定)"

    def format_items(items: list[dict], show_status: bool) -> str:
        groups: dict[str, list] = {}
        for item in items:
            cat = item.get("category", "その他")
            if cat not in cat_map:
                cat = "その他"
            groups.setdefault(cat, []).append(item)

        lines = []
        for cat_key, cat_label in cat_map.items():
            if cat_key not in groups:
                continue
            lines.append(f"\n### {cat_label}")
            for item in groups[cat_key]:
                jp = item.get("jp", "")
                kr = item.get("kr", "")
                label = f"{jp} ({kr})" if lang == "ko" else jp
                price = item.get("price_est")
                src = item.get("price_source", "")
                price_str = ""
                if isinstance(price, (int, float)) and price > 0:
                    marker = inferred_tag if src == "inferred" else ""
                    price_str = f" — ~{int(price)}円{marker}"
                if show_status:
                    status = item.get("status", "kept")
                    prefix = "❌ " if status == "removed" else "➖ " if status == "reduced" else "➕ " if status == "added" else ""
                    lines.append(f"- {prefix}{label}{price_str}")
                else:
                    lines.append(f"- {label}{price_str}")
        return "\n".join(lines)

    def summary_md(items: list[dict]) -> str:
        visible = [i for i in items if i.get("status") != "removed"]
        total = sum(int(i.get("price_est") or 0) for i in visible)
        gap = total - budget
        if gap > 0:
            diff = f"+{gap}"
        elif gap < 0:
            diff = f"{gap}"
        else:
            diff = "±0"
        if lang == "ko":
            return f"**합계**: {total}엔 / 예산 {budget}엔 (오차 {diff}엔)"
        return f"**合計**: {total}円 / 予算 {budget}円 (差額 {diff}円)"

    shopper_block_ko = f"\n## 🛒 쇼핑 에이전트의 코멘트\n> {shopper_comment}\n" if shopper_comment else ""
    shopper_block_ja = f"\n## 🛒 ショッピングエージェントのコメント\n> {shopper_comment}\n" if shopper_comment else ""

    if lang == "ko":
        content = f"""# 🛒 장바구니 - {display_time}

- **예산**: {budget:,}엔 (세전, 배송비 제외)
- **요청**: {preferences_display}
- **언어**: 한국어
{shopper_block_ko}
## 💬 건강 에이전트의 코멘트
> {advice.get('comment', '')}

## ⭐ 추천 목록
{format_items(improved, show_status=True)}

{summary_md(improved)}

📦 모두 세전 금액, 배송비는 별도예요.

---
*Generated at {display_time}*
"""
    else:
        content = f"""# 🛒 買い物リスト - {display_time}

- **予算**: {budget:,}円 (税抜、配送料別)
- **リクエスト**: {preferences_display}
- **言語**: 日本語
{shopper_block_ja}
## 💬 健康エージェントのコメント
> {advice.get('comment', '')}

## ⭐ おすすめリスト
{format_items(improved, show_status=True)}

{summary_md(improved)}

📦 すべて税抜、配送料は別途です。

---
*Generated at {display_time}*
"""

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. 언어 선택
    print("언어 선택 / 言語選択")
    print("  [1] 한국어  [2] 日本語")
    lang_input = input("→ ").strip()
    lang = "ja" if lang_input == "2" else "ko"
    t = UI[lang]

    # 2. 예산 입력
    print("\n" + t["title"])
    print("=" * 50)
    while True:
        budget_str = input(t["budget"]).strip()
        try:
            budget = int(budget_str)
        except ValueError:
            print(t["budget_error"])
            continue
        if validate_budget(budget, t):
            break

    # 3. 파일 로드 (언어+예산 입력 후)
    suffix = "kr" if lang == "ko" else "jp"
    pref_path = f"preferences_{suffix}.md"
    trend_path = f"trend_{suffix}.md"

    preferences_md = load_file(pref_path)
    prices = load_prices("prices.json")
    if not prices or "items" not in prices:
        print(t["prices_missing"])
        return

    # trend: 없거나 7일 이상 지났으면 재생성
    existing_trend = load_file(trend_path)
    if not existing_trend or is_trend_stale(trend_path, days=7):
        if Path(trend_path).exists():
            print(t["trend_stale"].format(path=trend_path))
        trend_md = fetch_and_save_trend(t, lang)
    else:
        trend_md = existing_trend

    # 4. 키워드 생성
    now = datetime.now()
    weekday_jp = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    weekday_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    month = now.month
    season_jp = "春" if month in [3,4,5] else "夏" if month in [6,7,8] else "秋" if month in [9,10,11] else "冬"
    season_ko = "봄" if month in [3,4,5] else "여름" if month in [6,7,8] else "가을" if month in [9,10,11] else "겨울"
    # LLM용(프롬프트 내부)은 항상 일본어
    today_str = f"{now.month}月{now.day}日（{weekday_jp[now.weekday()]}）、{season_jp}"
    # 화면 표시용
    today_display = (
        f"{now.month}월 {now.day}일 ({weekday_ko[now.weekday()]}), {season_ko}"
        if lang == "ko"
        else today_str
    )

    print(t["keyword_gen"])
    try:
        keywords = generate_keywords(today_str, lang, trend_md, preferences_md, t)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        print("다시 시도해주세요." if lang == "ko" else "もう一度お試しください。")
        return

    # 5. 키워드 출력
    print(f"\n{t['keyword_head']} ({today_display})")
    for i, kw in enumerate(keywords, 1):
        kw_type = kw.get("type", "normal")
        text = kw["kr"] if lang == "ko" else kw["jp"]
        if kw_type == "trend":
            print(f"  {i}. [{t['trend_label']}] {text}")
        elif kw_type == "souzai":
            print(f"  {i}. [{t['souzai_label']}] {text}")
        elif kw_type == "pref":
            print(f"  {i}. [{t['pref_label']}] {text}")
        elif kw_type == "random":
            print(f"  {i}. [{t['random_label']}] {text}")
        else:
            print(f"  {i}. {text}")

    # 6. 입력 예시 + 입력받기
    print(t["input_example"])
    raw_input_val = input(t["input_prompt"]).strip()

    # "알아서 해줘" 타입 해결: 해당 인덱스를 앞쪽에서 랜덤으로 뽑아 치환
    random_idx = next((i + 1 for i, kw in enumerate(keywords) if kw.get("type") == "random"), None)

    def resolve_random(token: str) -> str:
        if random_idx and token.strip() == str(random_idx):
            # 랜덤 후보: 자기 자신 제외한 앞쪽 전부
            candidates = [i + 1 for i, kw in enumerate(keywords) if kw.get("type") != "random"]
            picked = random.choice(candidates)
            kw = keywords[picked - 1]
            text = kw["kr"] if lang == "ko" else kw["jp"]
            msg = f"  🎲 알아서 → {picked}번 ({text})" if lang == "ko" else f"  🎲 おまかせ → {picked}番 ({text})"
            print(msg)
            return str(picked)
        return token

    if "+" in raw_input_val and all(p.strip().isdigit() for p in raw_input_val.split("+")):
        raw_input_val = "+".join(resolve_random(p) for p in raw_input_val.split("+"))
    else:
        raw_input_val = resolve_random(raw_input_val)

    preferences = parse_input(raw_input_val, keywords)
    prefs_display = display_preferences(raw_input_val, keywords, lang)


    # 선택한 키워드 타입에 따라 로드 상태 표시
    selected_indices = []
    if raw_input_val.isdigit():
        selected_indices = [int(raw_input_val)]
    elif "+" in raw_input_val and all(p.strip().isdigit() for p in raw_input_val.split("+")):
        selected_indices = [int(p.strip()) for p in raw_input_val.split("+")]
    shown_files = set()
    for idx in selected_indices:
        if 1 <= idx <= len(keywords):
            kw_type = keywords[idx - 1].get("type", "normal")
            if kw_type == "trend" and trend_md and "trend" not in shown_files:
                shown_files.add("trend")
                print(f"  ✔ {trend_path} 로드됨" if lang == "ko" else f"  ✔ {trend_path} を読み込みました")
            elif kw_type == "pref" and preferences_md and "pref" not in shown_files:
                shown_files.add("pref")
                print(f"  ✔ {pref_path} 로드됨" if lang == "ko" else f"  ✔ {pref_path} を読み込みました")

    # 7. 목록 생성 (에러 처리 포함)
    print(t["prices_loading"].format(count=len(prices["items"])))
    print(t["generating"])
    try:
        original, shopper_comment = generate_original(budget, preferences, lang, preferences_md, prices)
        print(t["health_check"])
        advice = health_check(original, budget, lang, prices)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        print("다시 시도해주세요." if lang == "ko" else "もう一度お試しください。")
        return

    improved = apply_health(original, advice)

    # 8. 출력 (개선 목록만)
    print(f"\n{t['result_disclaimer']}")
    if shopper_comment:
        shopper_label = "🛒 쇼핑 에이전트: " if lang == "ko" else "🛒 ショッピングエージェント: "
        print(f"\n{shopper_label}{shopper_comment}")
    else:
        print(f"\n{t['shopper_says']}")
    print(f"{t['health_says']}{advice.get('comment', '')}")
    print(t["legend"])

    visible = [i for i in improved if i.get("status") != "removed"]
    print("\n" + "=" * 50)
    print(t["improved"])
    print("=" * 50)
    print_table_by_category(improved, lang=lang, show_status=True, no_category_label=t["no_category"])
    print()
    print_summary(improved, budget, t)
    print("\n" + "=" * 50)

    # 9. 마크다운 저장
    try:
        saved_path = save_cart_markdown(lang, budget, prefs_display, shopper_comment, advice, improved)
        print(t["cart_saved"].format(path=saved_path))
    except OSError as e:
        print(f"⚠️  저장 실패: {e}")


if __name__ == "__main__":
    main()