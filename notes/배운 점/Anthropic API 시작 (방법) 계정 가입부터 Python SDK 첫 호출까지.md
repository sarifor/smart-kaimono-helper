# 상세
Anthropic API(Claude API)를 처음 쓰려면 **"콘솔 가입 → API 키 발급 → 결제 설정 → SDK 설치 → 첫 호출"** 5단계를 거친다. `console.anthropic.com`에서 가입 후 `Settings → API Keys → Create Key`로 키를 발급받는데, **키는 발급 시점에 단 한 번만 전체 문자열이 노출**되므로 즉시 `.env` 파일이나 비밀 관리 서비스에 저장해야 한다. 결제 수단은 `Settings → Billing`에서 등록하며, 신규 가입 시 소액의 무료 크레딧이 지급된다.

Python SDK는 `pip install anthropic`(Python 3.9+)로 설치한다. 공식 권장은 `python-dotenv`로 `.env`에 `ANTHROPIC_API_KEY`를 두고 환경변수로 로드하는 방식이다. 동기 클라이언트는 `Anthropic`, 비동기는 `AsyncAnthropic`을 사용하며, 첫 호출은 `client.messages.create(model=..., max_tokens=..., messages=[...])` 형태다. 응답의 `message.content[0].text`로 본문을, `message.usage`로 토큰 사용량을 얻는다.

SDK는 기본적으로 **자동 재시도 2회**(지수 백오프)와 **10분 기본 타임아웃**을 적용한다. 오류는 HTTP 상태에 따라 `APIConnectionError`, `RateLimitError`(429), `AuthenticationError`(401), `APIStatusError` 등으로 세분화되므로 최소한 연결·레이트·기타 세 갈래의 예외 경로를 확보해두는 것이 안전하다.

추가로 알아두면 좋은 두 가지가 있다. 최신 모델은 **thinking 모드**를 지원한다 — Sonnet 4.6은 `Extended thinking`과 `Adaptive thinking`을 모두, Opus 4.7은 `Adaptive thinking`만, Haiku 4.5는 `Extended thinking`만 지원하므로 복잡한 추론 작업에서 해당 옵션으로 품질을 끌어올릴 수 있다. `anthropic-version` 헤더는 SDK가 자동으로 `2023-06-01`로 설정하며, beta 기능을 쓸 때만 `betas=[...]` 파라미터나 커스텀 헤더로 조정한다. 일반 호출 중에는 기본값을 유지하는 편이 안전하다.

```
검증 보고:
- note.com(일본어)으로 가입·키 발급·결제 단계 흐름 확인
- 공식 Python SDK 문서로 Python 3.9+ 요건, 기본 사용 패턴, 에러 타입, 재시도/타임아웃 기본값, .env 권장 사항 교차 검증
- 수정 사항: note.com 예시의 구버전 모델 ID(`claude-sonnet-4-5-20250929`)를 현행 `claude-opus-4-7` 기준으로 일반화
```

## 시나리오 (비유)
`console.anthropic.com`에 가입하면 **회원카드(API 키)** 한 장을 받는다. 이 카드는 발급 **순간에만** 전체 번호가 보이므로, 받자마자 **지갑(`.env` 파일)** 에 넣는다. 그 다음 `pip install anthropic`로 주문 앱을 깔고 `messages.create`로 첫 호출을 넣으면 응답과 토큰 영수증이 돌아온다. 카드를 잃어버리면 폐기(revoke) 후 재발급 말고는 방법이 없다.

## 실전 체크리스트 (최대 3개)
- [ ] API 키 발급 **직후** `.env`에 저장 + `.gitignore`에 `.env` 추가 확인.
- [ ] `Billing → Usage limits`로 **월 상한** 설정 — 실수·무한 루프로 폭주하는 사고 방지.
- [ ] 첫 호출은 `max_tokens=100~200`으로 테스트 + `RateLimitError`·`APIConnectionError` 예외 경로 확보.

## 함정 (2~3개)
- API 키는 **1회만 전체 노출**. 깃·슬랙·스샷 등에 단 한 번이라도 찍히면 즉시 revoke 후 재발급 대상.
- `stream=False` 상태에서 `max_tokens`를 크게 잡으면 네트워크 idle 타임아웃으로 **요청이 유실되거나 재시도 2회가 모두 청구**될 수 있다.
- 기본 재시도 2회 탓에 rate limit 시 체감보다 호출이 쌓인다 — 비용 추정에 반영 필요.

## 복습 퀴즈 (3문항)
**Q1.** API 키는 발급 후 몇 번 전체가 노출되는가?
**A1.** 단 **1회**. 생성 시점에만 전체 문자열이 표시되고, 이후엔 앞부분만 보인다.

**Q2.** 동기 클라이언트 `Anthropic`과 비동기 `AsyncAnthropic`은 어떤 상황에서 각각 쓰는가?
**A2.** 단순 스크립트·CLI는 동기, 웹 서버나 여러 호출을 병렬 처리하는 I/O 대기 환경은 비동기.

**Q3.** 새 프로젝트에서 키 관리로 **가장 먼저** 해야 할 두 가지는?
**A3.** (1) `.env`에 `ANTHROPIC_API_KEY` 저장, (2) `.gitignore`에 `.env` 등록. 순서를 지켜야 깃 히스토리 노출을 막는다.

# 예시
**공식 Python SDK 기본 호출**:
```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
message = client.messages.create(
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
    model="claude-opus-4-7",
)
print(message.content[0].text)
print(message.usage)  # Usage(input_tokens=..., output_tokens=...)
```

`smart-kaimono-helper`는 루트 `.env`에 키를 두고 `shop.py` 상단에서 `load_dotenv()`로 로드해 4개 에이전트(`claude-sonnet-4-6`)가 공유한다.

# 생각
(추후 보충)

----

# 관련

```
연결 후보:
- [[Claude 모델 선택 (기준) 확신이 없으면 Opus 4.7부터 시작해 단계적으로 하향]] — API 설정 직후 바로 이어지는 의사결정
- [[python-dotenv (방법) .env 파일로 환경변수를 소스와 분리]] — 키 관리 표준 방식
- [[Rate limiting (기준) 지수 백오프와 재시도 설계]] — RateLimitError 대응 전략
```

# 태그
#AnthropicAPI #Claude #Python #SDK #API

----

# 참고
https://note.com/ai__worker/n/nbc960e49f683
https://platform.claude.com/docs/en/api/sdks/python
