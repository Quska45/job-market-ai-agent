# Collector App

채용공고 수집 실행 프로그램입니다.

초기 목표는 사람인에서 공개 공고를 읽기 전용으로 수집하고, 표준 JSON으로 저장하는 것입니다.

## 실행 목표

```powershell
python apps/collector/collect_saramin.py --keyword AI --max-jobs 20
```

## 출력 예시

```text
data/raw/saramin/2026-07-17_AI.json
```

## 수집 원칙

- 로그인 없이 공개 페이지에서만 수집합니다.
- 요청 수를 제한합니다.
- 요청 사이에 딜레이를 둡니다.
- 실패한 상세 페이지는 로그로 남기고 다음 공고를 처리합니다.
- 등록, 수정, 지원, 스크랩 같은 사용자 행동은 하지 않습니다.

