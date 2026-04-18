# README-준비 <!-- omit in toc -->

----

## 목차 <!-- omit in toc -->

- [README.md 구조](#readmemd-구조)
- [기술 스택 - requirements.txt](#기술-스택---requirementstxt)
  - [역할](#역할)
  - [만드는 법](#만드는-법)
  - [Windows PowerShell 주의사항](#windows-powershell-주의사항)
- [사용 영상](#사용-영상)
- [LICENSE](#license)
  - [MIT 라이선스를 선택한 이유](#mit-라이선스를-선택한-이유)
  - [적용 방법](#적용-방법)

----

## README.md 구조

soft-alarm-timer 프로젝트의 README.md를 참고해서 비슷한 구조로 작성했다.

```
소개 → 주요 기능 → 기술 스택 → 설치 및 사용 방법 → 참고사항 → License
```

## 기술 스택 - requirements.txt

### 역할

`package.json`에 해당하는 Python의 의존성 파일.  
다른 환경에서 `pip install -r requirements.txt` 한 줄로 필요한 패키지를 한꺼번에 설치할 수 있다.

### 만드는 법

**자동 생성**:
```
pip freeze > requirements.txt
```
현재 환경에 설치된 패키지를 전부 뽑아준다. 단, 전역 환경이면 이 프로젝트와 무관한 패키지까지 다 들어간다.

**직접 작성** (의존성이 적을 때 권장):<br/>
필요한 패키지만 골라서 직접 쓴다.
이 프로젝트에선 직접 `import`하는 패키지만 명시했다.

- `json`, `os`, `pathlib` 같은 **표준 라이브러리는 제외** (Python에 기본 내장)
- 앱 실행에 필요한 것: `anthropic`, `python-dotenv`
- 테스트에 필요한 것: `pytest`, `pytest-cov`

### Windows PowerShell 주의사항

`pip freeze > requirements.txt`를 PowerShell에서 실행하면 **UTF-16으로 저장**되는 경우가 있다. 이러면 글자 사이에 공백이 들어가 `pip install -r`이 오류를 낸다. 의존성이 적을 때는 직접 작성하는 게 안전하다.

## 사용 영상
- [README-사용 영상 준비.md](./README-사용%20영상%20준비.md) 참고

## LICENSE

### MIT 라이선스를 선택한 이유

- 가장 널리 쓰이는 오픈소스 라이선스
- 조건이 단순함: 저작권 표시만 유지하면 누구든 자유롭게 사용·수정·배포 가능
- 상업적 이용도 허용
- GitHub에서 사실상 표준으로 취급됨

### 적용 방법

1. 프로젝트 루트에 `LICENSE` 파일 생성
2. MIT License 표준 텍스트 붙여넣기
3. `Copyright (c) 연도 이름` 부분만 본인 정보로 수정
4. `README.md`의 License 섹션에 명시

표준 텍스트는 [choosealicense.com](https://choosealicense.com/licenses/mit/)에서 확인할 수 있다.
