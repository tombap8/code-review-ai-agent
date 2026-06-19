# 소규모 코드 리뷰 AI 에이전트 (MVP) - Development & Engineering Specification

---

## 🎭 에이전트 페르소나 (Persona)

* **역할**: 시니어 백엔드 엔지니어 및 AI/프롬프트 엔지니어
* **핵심 가치**: 
  - 브라우저 클라이언트보다 안전하고 독립적인 백엔드 아키텍처 및 REST API 보장.
  - 데이터 지속성(Persistence) 확보를 위한 SQLite 스키마 디자인 및 영속 데이터베이스 수립.
  - CORS 보안 이슈 해결 및 단일 구동 진입점 제공을 통한 DX 극대화.

---

## 🏗️ 2단계 시스템 아키텍처

```
[개발자 브라우저]
       │  (Static File Serve: index.html, style.css, app.js)
       ▼
[Flask 백엔드 (app.py)] ➔ [SQLite (database.db)]
       │
       ├─➔ [OpenAI API (GPT-4o-mini)]
       └─➔ [GitHub API / Rawcontent Fetch]
```

---

## 💾 데이터베이스 스키마 디자인 (SQLite DB)

백엔드 구동 시 자동으로 `backend/database.db` 파일이 생성되며, 아래 테이블 스키마가 초기화됩니다.

### 1. 설정 테이블 (`settings`)
사용자 인증 키 및 모델 구성 정보를 기록합니다.

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :---: | :---: | :--- |
| `key` | TEXT | PRIMARY KEY | 설정 키값 (예: 'api_key', 'model') |
| `value` | TEXT | - | 설정 데이터 값 |

### 2. 이력 테이블 (`history`)
분석이 완료된 리포트 데이터를 저장합니다.

| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :---: | :---: | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 각 저장 리뷰 일련번호 |
| `date` | TEXT | - | 리뷰 저장 일시 (포맷: YYYY. MM. DD. 오전/오후 HH:MM:SS) |
| `bugs` | TEXT | - | 검출된 주의 버그 개수 (예: "2개") |
| `improvements` | TEXT | - | 검출된 단순 개선 제안 개수 (예: "1개") |
| `htmlContent` | TEXT | - | PrismJS 및 JsDiff 포맷이 모두 래핑된 최종 HTML 리포트 본문 |

---

## 🔌 REST API 명세서 (API Specification)

모든 API 응답 포맷은 `application/json`입니다.

| 기능 | HTTP 메서드 | 엔드포인트 | 요청 바디 (Request Body) | 응답 바디 (Response Body) |
| :--- | :---: | :--- | :--- | :--- |
| **설정 조회** | GET | `/api/settings` | 없음 | `{"api_key": "...", "model": "..."}` |
| **설정 저장** | POST | `/api/settings` | `{"api_key": "...", "model": "..."}` | `{"status": "success", "message": "..."}` |
| **이력 전체 조회** | GET | `/api/history` | 없음 | `[{"id": 1, "date": "...", "bugs": "...", "improvements": "...", "htmlContent": "..."}]` |
| **이력 개별 저장** | POST | `/api/history` | `{"date": "...", "bugs": "...", "improvements": "...", "htmlContent": "..."}` | `{"status": "success", "id": 1}` |
| **이력 개별 삭제** | DELETE | `/api/history/<id>` | 없음 | `{"status": "success", "message": "..."}` |
| **이력 전체 삭제** | DELETE | `/api/history` | 없음 | `{"status": "success", "message": "..."}` |
| **코드 분석 실행** | POST | `/api/review` | `{"code": "..."}` | `{"review": "마크다운 결과물..."}` |

---

## ✍️ 시스템 프롬프트 엔지니어링 (OpenAI API)

백엔드에서 OpenAI API(`POST /v1/chat/completions`) 호출 시 탑재하는 프롬프트 가이드라인입니다.

```markdown
너는 풀스택 시니어 소프트웨어 엔지니어이자 코드 리뷰 전문가이다. 
제시된 코드 Diff 또는 전체 소스코드를 정밀하게 분석하여 다음 기준에 따라 리뷰를 수행하라.

[리뷰 기준]
1. ⚠️ 주의 버그: 메모리 누수, 예외 처리 누락, 널 포인터 역참조, 잘못된 비즈니스 로직 등 실제 시스템 장애를 유발할 수 있는 사항.
2. 💡 단순 개선: 비효율적인 알고리즘(시간/공간 복잡도), 리팩토링(중복 제거, 함수 분할), 최신 언어 스펙 활용 등 권장되는 사항.

[출력 포맷 가이드라인]
너는 작성된 결과를 출력할 때 반드시 별도 설계서(webd.md)에 정의된 양식을 철저히 준수해야 한다.
- 최상단에 마크다운 테이블 형식의 요약표를 제공할 것.
- ⚠️와 💡 이모지를 상황에 맞게 올바르게 사용할 것.
- 코드 변경 제안은 반드시 아래의 형태로 작성할 것 (마크다운의 헤더 및 이모지 정확히 일치):
  ⚠️ **기존 코드**
  ```(언어명)
  (기존 코드 내용)
  ```
  
  💡 **개선 코드**
  ```(언어명)
  (개선 제안 코드 내용)
  ```

[제약 사항]
- 변경점이 없거나 완벽한 코드에 대해서는 무리하게 지적하지 마라.
- 반드시 수정 이유(Why)를 명확히 설명할 것.
- 모든 설명은 한글(Korean)로 작성해라.
```
