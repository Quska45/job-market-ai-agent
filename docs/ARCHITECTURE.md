# 아키텍처

이 저장소는 여러 실행 프로그램을 하나의 프로젝트에서 함께 관리합니다.

## 구조

```text
apps/
  collector/      # 채용공고 수집 실행 프로그램
  analyzer/       # LLM 기반 공고 분석 실행 프로그램
  qa/             # 저장된 공고 기반 질문 응답 프로그램
  notifier/       # 데일리 브리핑과 관심 조건 알림 프로그램
  api/            # 나중에 붙일 FastAPI 서버

src/job_market_ai_agent/
  core/           # 공통 모델, 해시, 텍스트 정규화
  collectors/     # 사이트별 크롤러
  storage/        # JSON, DB 저장소
  analysis/       # LLM 분석
  retrieval/      # 검색, embedding, RAG
  agents/         # workflow agent
  notifications/  # Discord, Telegram, Email 알림

tests/
  core/
  collectors/
  storage/
```

## 설계 원칙

- `apps/`는 실행 진입점만 둡니다.
- 실제 비즈니스 로직은 `src/job_market_ai_agent/` 아래에 둡니다.
- 크롤러, 분석기, 알림기는 같은 `JobPosting` 모델을 사용합니다.
- 처음 저장소는 JSON 파일이고, 이후 PostgreSQL로 확장합니다.
- 사이트별 파서는 실패해도 전체 수집을 중단하지 않게 만듭니다.

## 프로그램별 역할

### collector

사람인 등 채용 사이트에서 공고를 수집합니다.

초기 범위:

- 사람인 1개 사이트
- 지역 전체
- IT 전체
- 키워드 기반 검색
- 최대 수집 개수 제한
- JSON 저장

### analyzer

수집된 공고 원문을 LLM으로 분석합니다.

분석 대상:

- 직무 유형
- 경력 수준
- 기술스택
- 주니어 적합도
- 요약

### qa

저장된 공고를 기반으로 질문에 답합니다.

초기에는 DB/JSON 검색으로 시작하고, 이후 embedding 기반 RAG로 확장합니다.

### notifier

매일 신규 공고와 트렌드를 요약해서 알림을 보냅니다.

초기 알림 채널은 Discord Webhook을 우선 후보로 둡니다.

### api

CLI 프로그램이 안정화된 뒤 FastAPI 서버로 확장합니다.

