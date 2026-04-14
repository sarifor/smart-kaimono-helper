# smart-kaimono-helper <!-- omit in toc -->

**Language** | 한국어 | [日本語](README_ja.md)

----

## 목차 <!-- omit in toc -->

- [소개](#소개)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
  - [개발 환경](#개발-환경)
  - [라이브러리](#라이브러리)
  - [AI 모델](#ai-모델)
- [설치 및 사용 방법](#설치-및-사용-방법)
  - [전제 조건](#전제-조건)
  - [설치](#설치)
  - [사용 방법](#사용-방법)
- [동작 화면](#동작-화면)
- [참고사항](#참고사항)
- [License](#license)

----

## 소개

일본 넷슈퍼 장바구니 목록을 AI가 대신 짜주는 CLI 도구입니다.<br/>
예산을 입력하면 트렌드·취향을 반영한 장바구니를 만들고, 건강 균형까지 검토해줍니다.<br/>
타깃 유저는 일본 거주 한국인, 일본인, 기타 일본어 사용자입니다. 따라서 한국어·일본어를 모두 지원합니다.

## 주요 기능

| 기능 | 설명 |
|---|---|
| 🔑 키워드 추천 | 오늘의 날짜·계절·트렌드를 반영한 쇼핑 키워드 7개 제안 |
| 🛒 장바구니 생성 | 예산 ±10% 이내로 맞춘 상품 목록 생성 |
| 🥗 건강 검토 | 영양 균형을 보고 추가·삭제·감량 제안 |
| 📄 결과 저장 | `carts/` 폴더에 마크다운 파일로 자동 저장 |
| 🌐 트렌드 갱신 | 일본 슈퍼 트렌드를 웹 검색으로 7일마다 자동 업데이트 |
| 🇰🇷🇯🇵 이중 언어 | 한국어·일본어 선택 가능 |

## 기술 스택

### 개발 환경
- Windows 11 Pro / Python 3.12.6
- Mac/Linux는 미검증
- Claude Code
  - 코딩: Claude Opus 4.6 (thinking: high)
  - 문서 작성: Claude Sonnet 4.6 (thinking: auto)

### 라이브러리
- anthropic 0.76.0
- python-dotenv 1.2.1
- pytest 9.0.3 (개발용)
- pytest-cov 7.1.0 (개발용)

### AI 모델
- [Claude Sonnet 4.6](https://www.anthropic.com/claude/sonnet) (Anthropic)

## 설치 및 사용 방법

### 전제 조건

- Python이 설치되어 있어야 합니다.
- [Anthropic 콘솔](https://console.anthropic.com)에서 API 키를 발급받아야 합니다.

### 설치

1. 터미널(cmd / PowerShell)을 열고 프로젝트를 저장할 경로로 이동합니다.
   ```
   cd 원하는 경로
   ```
2. 이 저장소를 클론합니다.
   ```
   git clone https://github.com/Sarifor/smart-kaimono-helper.git
   ```
3. 의존성을 설치합니다.
   ```
   pip install -r requirements.txt
   ```
4. 프로젝트 루트에 `.env` 파일을 만들고 API 키를 입력합니다.
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

### 사용 방법

1. 터미널(cmd / PowerShell)을 열고 프로젝트 폴더로 이동합니다.
   ```
   cd smart-kaimono-helper
   ```
2. 앱을 실행합니다.
   ```
   python shop.py
   ```
3. 언어를 선택합니다 (한국어 / 日本語)
4. 예산을 입력합니다 (엔, 세전, 배송비 제외)
5. 추천 키워드 중 하나를 고르거나 직접 입력합니다
6. 장바구니 목록이 생성되고 `carts/` 폴더에 저장됩니다 (앱 자동 종료)

## 동작 화면

(추가 예정)

## 참고사항

- 가격은 전부 세전 기준이며, 배송비는 별도입니다.
- 최소 주문금액은 700엔입니다.
- API 비용은 생성 1회당 약 $0.03~0.08 수준입니다. 자세한 내용은 `API-COST.md`를 참고하세요.
- 취향을 반영하려면 `preferences_kr.md` (한국어) 또는 `preferences_jp.md` (일본어)를 직접 수정하세요.
- 트렌드 내용을 커스텀하려면 `trend_kr.md` (한국어) 또는 `trend_jp.md` (일본어)를 직접 수정하세요. 7일이 지나면 웹 검색으로 자동 갱신됩니다.

## License

MIT License
