# 데이터 모델 초안

## jobs

채용공고 원문과 기본 정보를 저장합니다.

```text
id
source
source_job_id
company
title
location
employment_type
experience_level_raw
salary_raw
description
url
posted_at
deadline
collected_at
content_hash
created_at
updated_at
```

## job_analyses

LLM이 분석한 구조화 결과를 저장합니다.

```text
id
job_id
role_category
seniority
required_skills
preferred_skills
domain
summary
fit_for_beginner
remote_policy
analysis_model
analysis_prompt_version
created_at
```

## job_embeddings

검색과 RAG에 사용할 embedding을 저장합니다.

```text
id
job_id
chunk_index
chunk_text
embedding
embedding_model
created_at
```

## collection_runs

수집 실행 이력을 저장합니다.

```text
id
source
started_at
finished_at
status
found_count
new_count
updated_count
error_message
```

## user_preferences

알림 조건을 저장합니다.

```text
id
name
role_categories
skills
seniority
locations
keywords
notification_channel
enabled
created_at
updated_at
```

