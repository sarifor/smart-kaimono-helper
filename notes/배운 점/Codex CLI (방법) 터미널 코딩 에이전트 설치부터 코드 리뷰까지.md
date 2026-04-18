# 상세
Codex CLI는 OpenAI가 만든 **터미널 기반 코딩 에이전트**다. `npm i -g @openai/codex`로 설치하고, ChatGPT Plus 이상 플랜 계정 또는 OpenAI API 키로 인증한다. macOS·Linux를 공식 지원하며 Windows는 WSL2에서 작동한다. 설치 후 `codex`를 실행하면 전체화면 TUI(Terminal UI) 세션이 시작되고, 코드베이스 읽기·파일 편집·셸 명령 실행이 모두 가능하다. 비대화형 자동 실행이 필요하면 `codex exec "작업"` 형태로 쓴다.

세션 안에서 슬래시 커맨드로 기능을 전환한다. `/review`로 코드 리뷰 프리셋을 열면 "기본 브랜치 대비", "미커밋 변경사항", "특정 커밋", "커스텀 지침" 네 가지 중 선택해 리뷰를 시작한다. `/permissions`(또는 시작 시 `--approval-mode` 플래그)로 실행 권한을 **Auto**(기본, 편집·명령 즉시 실행) / **Read-only**(열람 전용, 변경은 승인 후) / **Full Access**(제한 없음) 세 단계로 제어한다. 파일 지목은 `@파일명` 퍼지 검색, 셸 명령은 라인 앞에 `!` 접두어를 붙인다. 이전 세션 재개는 `codex resume`으로 문맥을 유지한다.

Claude Code 내에서는 터미널 전환 없이 `codex:rescue` 스킬로 Codex 서브에이전트에 작업을 위임할 수 있다. Claude Code가 진단·수정 요청을 Codex에게 전달하고 결과를 받아 표시하는 구조다. `codex:setup`으로 로컬 CLI 준비 상태 확인과 리뷰 게이트(stop-time review) 설정을 할 수 있고, `codex:gpt-5-4-prompting`은 Codex와 GPT-5.4에 최적화된 프롬프트 작성 가이드다.

```
검증 보고:
- github.com/openai/codex README로 설치·인증·Apache-2.0 라이선스 확인
- developers.openai.com/codex/cli 및 /cli/features로 슬래시 커맨드·승인 모드·/review 프리셋 확인
- Claude Code 내 codex:* 스킬 연동은 클로드 코드의 현재 세션 스킬 목록 기반 — 공식 외부 문서 직접 링크 미확인, 추후 검증 필요
- Windows 미지원(WSL2 권장)은 공식 문서 명시 사항
```

## 시나리오 (상황 서사)
`smart-kaimono-helper` v1 완성 후 배포 전 코드 점검을 하려 한다. 터미널에서 프로젝트 루트에 서서 `codex`를 실행한다. 세션이 열리면 `/permissions`로 **Read-only** 모드를 선택하고, `/review`를 입력해 "기본 브랜치 대비"를 고른다. Codex가 main과의 차이를 읽고 "apply_health의 중복 삭제 로직은 count 기반 처리로 잘 잡혔으나, 동일 이름 3개 이상인 케이스 테스트가 없습니다"라고 피드백한다. `@tests/test_unit.py`로 파일을 참조해 "이 케이스 테스트 추가해줘"라고 입력하자, Read-only 모드라 수정 전 승인 창이 뜬다. 확인 후 파일이 바뀐다.

## 실전 체크리스트 (최대 3개)
- [ ] 코드 리뷰 목적이면 세션 시작 직후 `/permissions` → **Read-only** 전환 — Auto 기본값에서는 제안 승인 시 파일이 즉시 수정됨.
- [ ] **어느 경로를 쓸지 먼저 결정**: "허락 후 수정"을 확실히 원하면 경로 B(Codex CLI 직접 + Read-only). 경로 A(Claude Code 세션)는 권한 설정에 따라 Edit이 자동 허용될 수 있음.
- [ ] 긴 리뷰 지침은 세션 안에서 **Ctrl+G**로 에디터를 열어 작성 — 한 줄 입력보다 구조적인 지시 전달 가능.

## 함정 (2~3개)
- **Auto 모드가 기본값**이라 `/review` 후 제안을 승인하면 파일이 즉시 수정된다. 리뷰 전용이라면 반드시 **Read-only**로 전환하고 시작.
- `codex exec "작업"`은 비대화형 자동 실행 — 검토 없이 파일을 바꾸므로, 내용 파악 전인 코드베이스에 바로 쓰면 의도치 않은 변경이 생길 수 있음.
- `codex resume`으로 세션을 재개할 때 세션 이후 파일이 바뀌었다면, Codex가 오래된 문맥을 기반으로 판단할 수 있음 — 중요한 변경이 있었다면 새 세션이 더 안전.
- **경로 A(codex:rescue)에서 "허락 후 수정"을 기대하면 안 됨** — Claude Code의 Edit 도구 권한이 자동 허용으로 설정되어 있으면 확인 창 없이 파일이 바뀐다. 파일 수정 전 승인을 보장하려면 경로 B + `/permissions` → Read-only 조합이 확실.

## 복습 퀴즈 (3문항)
**Q1.** Codex CLI에서 코드 리뷰를 시작하는 슬래시 커맨드와, 선택 가능한 리뷰 기준 4가지는?
**A1.** `/review`. ① 기본 브랜치 대비 ② 미커밋 변경사항 ③ 특정 커밋 ④ 커스텀 지침.

**Q2.** Auto 모드와 Read-only 모드의 동작 차이는? 리뷰 목적이면 어느 쪽을 써야 하는가?
**A2.** Auto는 파일 편집·명령 실행을 즉시 허용, Read-only는 열람만 허용(변경은 승인 후). 리뷰 목적이면 **Read-only**.

**Q3.** Claude Code 세션 안에서 코드 진단·수정을 Codex에 위임하려면 어떤 스킬을 사용하는가?
**A3.** `codex:rescue`. Claude Code가 요청을 Codex 서브에이전트에 전달하고 결과를 받아 표시한다.

# 예시
**경로 A — Claude Code 세션 안에서 리뷰 요청 (추가 설치 불필요)**

Claude Code 프롬프트에 아래처럼 입력한다:
```
이 프로젝트 코드 리뷰해줘. 파일 수정 전에 반드시 내 허락 받아야 해.
```
`codex:rescue`는 **proactive 스킬**이라 Codex를 명시하지 않아도 된다. Claude Code가 "두 번째 진단 패스가 필요하다", "규모가 크다"고 판단하면 자동으로 Codex에 위임한다. 확실히 Codex를 쓰고 싶다면 "Codex에게 맡겨줘" 또는 `/codex:rescue`라고 명시하면 강제 호출된다.

파일 수정은 Claude Code의 Edit 도구 호출 시 권한 창이 뜨는 경우에만 허락/거부가 가능하다. **권한 설정에 따라 자동 허용될 수 있으므로** "반드시 허락 후 수정"이 중요하다면 경로 B를 쓸 것.

---

**경로 B — Codex CLI 직접 실행 (파일 수정 차단 확실)**

```bash
# 1. 프로젝트 루트에서 Codex TUI 세션 시작 (Windows는 WSL2 안에서)
codex

# ── 세션 안 ──────────────────────────────────────────
# 2. 파일 수정 차단 모드로 전환 ← 핵심
/permissions   →  Read-only 선택

# 3. 코드 리뷰 시작
/review        →  "기본 브랜치 대비" 선택

# 4. 특정 파일 지목해 추가 질문
@shop.py apply_health 함수 엣지케이스 있는지 확인해줘

# 5. 수정이 필요하다고 판단되면 → 모드 올리고 직접 허락 후 적용
/permissions   →  Auto 선택
apply_health에 동일 이름 3개 케이스 테스트 추가해줘
# ─────────────────────────────────────────────────────

# 비대화형 단발 실행이 필요한 경우 (주의: 검토 없이 실행됨)
codex exec "shop.py의 TODO 주석 전부 찾아서 목록으로 출력해줘"
```

# 생각
(추후 보충)

----

# 관련

```
연결 후보:
- [[Claude Code (방법) CLI 에이전트로 코딩 작업 위임]] — codex:rescue로 연동되는 상위 도구
- [[코드 리뷰 (기준) 자동화 도구와 리뷰 범위 설정]] — /review 프리셋 선택 판단 기준
- [[MCP (정의) Model Context Protocol로 에이전트 도구 확장]] — Codex의 써드파티 도구 통합 기반
```

# 태그
#CodexCLI #OpenAI #코드리뷰 #터미널에이전트 #SKH

----

# 참고
https://github.com/openai/codex<br/>
https://developers.openai.com/codex/cli<br/>
https://developers.openai.com/codex/cli/features
