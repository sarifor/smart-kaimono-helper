# 상세
`browser-use`는 **AI 에이전트가 웹 브라우저를 조작**하도록 만드는 Python 라이브러리다. 내부적으로 `Playwright`를 통해 `Chromium`을 구동하고, LLM이 **화면 스크린샷(비전)** 과 **HTML 구조**를 함께 입력받아 클릭·입력·스크롤 같은 액션을 생성하면 그것을 실제 브라우저에 실행시킨다. MIT 라이선스, Python 3.11+ 필요.

지원 LLM은 자체 모델 `ChatBrowserUse`, Gemini, Claude, Ollama 기반 로컬 모델 등 다수. 주요 기능은 **비전+HTML 결합 판단, 멀티탭 관리, 요소 추적, 커스텀 액션, 자동 복구(auto-recovery)** 다. 공식 유스케이스에 **온라인 쇼핑 자동화**가 명시되어 있어 장바구니 담기는 기능적으로 가능하지만, **결제 단계는 자동화 비권장**(금전적 실수 시 복구 불가).

보안상 `sensitive_data` 필드로 자격정보를 LLM 프롬프트에서 격리하고, `allowed_domains`로 접근 도메인을 화이트리스트로 제한하는 것이 권장된다. LLM이 의도치 않게 관계없는 사이트에 자격정보를 입력하는 사고를 막기 위함이다.

```
검증 보고:
- GitHub 공식 README로 정의·라이선스·Chromium/Playwright·Python 3.11+ 확인
- Keywalker 블로그(일본어)로 기능·보안·사례 교차 검증
- "쇼핑몰 장바구니 자동 담기"는 README의 "online shopping automation"에 명시 — 기능적으로 가능하나 결제 단계는 비권장
- YouTube 영상은 페이지 메타데이터만으로 내용 추출 불가 — 직접 확인 필요
- 수정 사항 없음 (사용자가 질문 형태로 제시)
```

## 시나리오 (비유)
**운전 보조 기능이 있는 스마트 자동차**를 떠올려 보자. 차체는 Playwright(일반 브라우저 자동화), 운전사는 LLM이다. 운전사는 앞 유리(스크린샷)와 내비(HTML 구조)를 보며 "여기서 왼쪽", "이 버튼 클릭"을 실행한다. 운전은 맡길 수 있지만 **결제창에서 결제 버튼을 직접 누르게 하는 건 금지** — 실수하면 환불 불가 사고가 난다. 그래서 주차장(장바구니)까지만 맡기고 **마지막 결제는 사람이** 한다.

## 실전 체크리스트 (최대 3개)
- [ ] 작업에 **LLM 판단**이 정말 필요한지 먼저 확인. 단순 DOM 스크래핑이면 `Playwright` 단독이 더 싸고 안정적.
- [ ] `sensitive_data` + `allowed_domains` 설정을 **반드시** 먼저 잡고 실행.
- [ ] 스크린샷 기반이라 입력 토큰 급증 — 호출당 비용·월 예산 미리 추산. 결제 단계는 자동화 제외.

## 함정 (2~3개)
- 소형 파라미터 모델에서는 작업이 중간에 끊기거나 의도와 다르게 동작. 10단계 이상 복잡 워크플로우는 공식도 "의도대로 안 될 수 있음"을 인정.
- 스크린샷+HTML 동시 전송으로 **토큰 비용이 빠르게 누적**. "싼 모델이면 괜찮겠지"가 아니라 실제 호출당 토큰을 먼저 측정.
- LLM이 자격정보를 다른 폼에 잘못 입력하는 보안 사고 가능성 — `allowed_domains`로 사전 차단 필수.

## 복습 퀴즈 (3문항)
**Q1.** browser-use는 내부적으로 어떤 브라우저 자동화 엔진과 브라우저를 사용하는가?
**A1.** `Playwright`를 통해 `Chromium`을 구동한다.

**Q2.** LLM이 의도치 않게 관계없는 사이트에 자격정보를 입력하는 사고를 막기 위한 **공식 권장 설정 두 가지**는?
**A2.** `sensitive_data`(자격정보를 LLM 프롬프트에서 격리) + `allowed_domains`(접근 도메인 화이트리스트).

**Q3.** browser-use로 쇼핑몰 자동화를 한다면 어디까지 자동화하고 어디서 멈춰야 하는가?
**A3.** **장바구니 담기까지는 OK, 결제 확정은 금지**. 결제 실수는 복구 불가이므로 사람이 수행.

# 예시
**공식 기본 코드 (GitHub README)**:
```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def main():
    browser = Browser()
    agent = Agent(
        task="Find the number of stars of the browser-use repo",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()

asyncio.run(main())
```

설치: `uv init && uv add browser-use && uv sync` (Python 3.11+).

# 생각
(추후 보충)

----

# 관련

```
연결 후보:
- [[Playwright (정의) 크롬/파이어폭스 자동화 라이브러리]] — browser-use의 하부 엔진
- [[LLM 에이전트 (아키텍처) 스크린샷 + HTML 결합 판단]] — 작동 방식이 여기 속함
- [[smart-kaimono-helper (확장 아이디어) 장바구니 자동 담기 연결안]] — 기존 프로젝트의 다음 단계
```

# 태그
#browserUse #브라우저자동화 #LLM #Python #AI

----

# 참고
https://github.com/browser-use/browser-use<br/>
https://www.keywalker.co.jp/blog/browser-use-automation.html<br/>
https://www.youtube.com/watch?v=WyBmGkO-Oo8
