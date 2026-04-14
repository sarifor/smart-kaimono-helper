# 테스트 실행 가이드 <!-- omit in toc -->

----

## 목차 <!-- omit in toc -->

- [설치](#설치)
- [기본 테스트 (mock만, 무료)](#기본-테스트-mock만-무료)
- [스모크 테스트 (실제 API 호출, 비용 발생)](#스모크-테스트-실제-api-호출-비용-발생)
- [커버리지](#커버리지)

----

## 설치

```bash
pip install pytest pytest-cov
```

## 기본 테스트 (mock만, 무료)

```bash
pytest -v
```

API 호출 없이 모든 단위/통합 테스트를 실행합니다.

## 스모크 테스트 (실제 API 호출, 비용 발생)

```bash
pytest -m smoke -v
```

`.env`에 `ANTHROPIC_API_KEY`가 설정되어 있어야 합니다.
한국어/일본어 각 1회씩 실제 API를 호출합니다 (몇 센트 수준).

## 커버리지

```bash
pytest --cov=shop -v
```
