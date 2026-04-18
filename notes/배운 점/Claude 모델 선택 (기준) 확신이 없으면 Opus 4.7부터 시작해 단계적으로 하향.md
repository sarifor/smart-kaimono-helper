# 상세
Anthropic 공식 문서는 **"어떤 모델을 써야 할지 확신이 서지 않으면 가장 복잡한 작업을 기준으로 `Claude Opus 4.7`부터 시작"** 할 것을 권장한다. 모델 선택의 기준점은 프로젝트의 "평균 작업"이 아니라 **"가장 어려운 단일 호출"** 이다. 그 호출이 Opus급 추론을 요구하지 않는다고 판단되면, 더 저렴하고 빠른 `Sonnet 4.6` 또는 `Haiku 4.5`로 내려도 품질이 유지된다.

2026-04 기준 현행 모델 3종은 `Opus 4.7`(\$5/\$25 per MTok, 1M context, Adaptive thinking), `Sonnet 4.6`(\$3/\$15, 1M, Extended+Adaptive thinking), `Haiku 4.5`(\$1/\$5, 200k, Extended thinking)다. Opus 4.7은 직전 세대 Opus 4.6 대비 **"에이전트 코딩에서 단계적 도약"** 을 이뤘다고 공식 명시되어 있다. 단 Opus 4.7은 Extended thinking을 미지원이므로, **명시적** 사고 토큰 제어가 필요하면 **Sonnet 4.6**이 더 적합할 수 있다.

가격 차이는 입력·출력 모두 최대 5배. 재시도 루프가 있는 시스템에서는 "싼 모델 → 재시도 증가 → 결국 더 비쌈" 함정이 흔하므로, 토큰 단가만으로 판단하지 말고 **평균 호출 횟수까지 반영한 실질 비용**을 추산해야 한다.

```
검증 보고:
- Anthropic 공식 Models overview 페이지로 수치·인용 전부 확인
- 핵심 권고: "If you're unsure which model to use, consider starting with Claude Opus 4.7"
- 에이전트 코딩 개선: "step-change improvement in agentic coding" 원문 그대로 반영
- 수정 사항 없음
```

## 시나리오 (상황 서사)
`smart-kaimono-helper` 프로젝트를 시작하며 4개 에이전트의 모델을 골라야 했다. 가장 까다로운 쇼핑 에이전트(JSON 20개, 예산 맞춤)부터 `Opus 4.7`로 돌려 "이 정도면 충분하다"는 품질 상한선을 잡았다. 같은 입력을 `Sonnet 4.6`으로 낮춰도 결과가 거의 동일했고, `Haiku 4.5`로 더 내리니 예산 산수에서 오차가 커졌다. Sonnet에서 멈춰 4개 에이전트 전부 `claude-sonnet-4-6`으로 통일. Opus 대비 비용은 약 1/5 수준.

## 실전 체크리스트 (최대 3개)
- [ ] 프로젝트에서 **"가장 어려운 단일 호출"** 을 먼저 정의 (평균 아님).
- [ ] 그 호출을 `Opus 4.7`로 돌려 **품질 상한선** 확인 → `Sonnet 4.6` → `Haiku 4.5`로 내려가며 비교 → **납득 가능한 최저 지점**에서 멈춤.
- [ ] 재시도·검증 루프가 있으면 **평균 호출 횟수**까지 비용 계산에 포함.

## 함정 (2~3개)
- 단가만 보고 Haiku를 고르면 재시도 증가로 총비용이 역전될 수 있음.
- `Extended thinking`과 `Adaptive thinking`은 모델마다 지원 범위가 다름 — Opus 4.7은 Adaptive만 지원. 사고 토큰 제어가 필요하면 Sonnet 4.6.
- Legacy 모델(Opus 4.1, Sonnet 4, Haiku 3 등)은 deprecation 일정이 있음 — 프로젝트 시작 전 `model-deprecations` 페이지 확인.

## 복습 퀴즈 (3문항)
**Q1.** Anthropic 공식 문서가 "확신이 없을 때" 권장하는 시작 모델은 무엇인가?
**A1.** `Claude Opus 4.7`. 가장 복잡한 작업을 기준으로 Opus 4.7부터 시작해 단계적으로 낮추는 방식을 권장.

**Q2.** **사고 토큰을 명시적으로 제어**해야 하는 작업에 Opus 4.7과 Sonnet 4.6 중 어느 쪽이 더 적합한가?
**A2.** `Sonnet 4.6`. Opus 4.7은 `Adaptive thinking`만 지원하고 `Extended thinking`은 미지원.

**Q3.** "단가가 가장 싼 Haiku로 전부 돌리자"는 판단이 역효과를 낼 수 있는 대표 상황은?
**A3.** 재시도·검증 루프가 들어있는 시스템. 품질 하락이 호출 횟수를 늘려 **총비용이 오히려 증가**.

# 예시
**공식 문서 원문 인용**:
> If you're unsure which model to use, consider starting with Claude Opus 4.7 for the most complex tasks. It is our most capable generally available model, with a step-change improvement in agentic coding over Claude Opus 4.6.

`smart-kaimono-helper`는 쇼핑 에이전트가 가장 복잡하지만 "가격표 참고 + 산수 + JSON 생성" 수준이라 Opus급 불필요 판단. 4개 에이전트 전부 `claude-sonnet-4-6`으로 통일 (`shop.py` L85 등).

# 생각
(추후 보충)

----

# 관련

```
연결 후보:
- [[Claude API (방법) messages.create 기본 사용법]] — 모델 선택 이후 호출 단계
- [[max_tokens (기준) 입력 길이 대비 출력 한도 재산정]] — 모델 선택과 함께 다뤄야 하는 설정
- [[에이전트 체인 (아키텍처) LLM 호출 독립성과 상태 전달]] — smart-kaimono-helper 파생, 모델 혼합 전략과 연결
```

# 태그
#Claude #모델선택 #LLM #API #SKH

----

# 참고
https://platform.claude.com/docs/en/about-claude/models/overview
