# 프로젝트 계획

## 문제 정의

AI 관련 채용공고는 빠르게 늘고 있지만, 공고마다 요구하는 기술, 경력 수준, 직무 범위가 다릅니다. 사람이 매일 여러 사이트를 확인하고 흐름을 정리하는 것은 비효율적입니다.

이 프로젝트는 채용공고를 자동으로 수집하고 분석해서 다음 질문에 답할 수 있게 만드는 것을 목표로 합니다.

- 요즘 AI Engineer 공고에서 가장 자주 요구하는 기술은 무엇인가?
- 주니어가 지원 가능한 공고는 얼마나 있는가?
- RAG, LangGraph, MLOps 같은 키워드는 얼마나 자주 등장하는가?
- 내 현재 학습 방향과 채용시장 요구사항 사이의 차이는 무엇인가?
- 오늘 새로 올라온 중요한 공고는 무엇인가?

## 사용자 시나리오

### 데일리 브리핑

사용자는 매일 아침 신규 공고 수, 주요 직무 유형, 급상승 기술 키워드, 추천 학습 액션을 받습니다.

### 질의응답

사용자는 CLI 또는 웹 UI에서 질문합니다.

예:

- 최근 7일간 AI Engineer 공고에서 가장 많이 나온 기술 알려줘.
- RAG 경험을 요구하는 회사만 보여줘.
- 주니어가 지원 가능한 공고를 골라줘.
- 백엔드 개발자가 AI Engineer로 전환하려면 어떤 기술을 우선 공부해야 해?

### 관심 조건 알림

사용자는 관심 조건을 설정합니다.

예:

- 직무: AI Engineer, LLM Engineer
- 경력: 신입, 주니어, 3년 이하
- 기술: Python, FastAPI, RAG, LangGraph
- 지역: 서울, 원격

조건에 맞는 신규 공고가 나오면 알림을 받습니다.

## 시스템 구성

초기 구조:

```text
collector -> normalizer -> database -> llm analyzer -> report/question answering
```

확장 구조:

```text
scheduler
  -> collectors
  -> deduplication
  -> LLM analysis
  -> embeddings
  -> trend aggregation
  -> notification agent
  -> Q&A agent
```

## 추천 기술 스택

- Language: Python
- API: FastAPI
- Crawler: httpx, BeautifulSoup, Playwright
- Scheduler: APScheduler
- Database: PostgreSQL
- Vector Search: pgvector
- LLM: OpenAI API
- Agent Workflow: 직접 구현 후 LangGraph로 확장
- Notification: Discord Webhook 또는 Telegram Bot
- Test: pytest
- Deployment: Docker Compose

## 개발 순서

1. 프로젝트 골격과 데이터 모델 정의
2. 한 사이트 대상 수집기 구현
3. 중복 제거와 저장
4. LLM 분석 파이프라인 구현
5. 일일 리포트 생성
6. CLI 질의응답 구현
7. RAG 검색 추가
8. 알림 기능 추가
9. 웹 UI 또는 API 서버 추가
10. 운영 품질 개선

## 주의할 점

- 처음부터 여러 사이트를 붙이지 않는다.
- 처음부터 완전한 agent framework를 쓰지 않는다.
- 크롤링보다 데이터 모델과 분석 파이프라인을 먼저 안정화한다.
- LLM 응답은 반드시 JSON schema나 Pydantic 모델로 검증한다.
- 채용공고 원문을 그대로 신뢰하지 않고, source URL과 수집 시간을 함께 저장한다.

