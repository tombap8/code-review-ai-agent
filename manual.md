# CodeReview AI 사용 설명서 (manual.md)

본 설명서는 구축된 코드 리뷰 AI 에이전트를 **A) 로컬 Python/Flask 백엔드 서버**로 구동하는 방법과 **B) Streamlit Community Cloud**에 클라우드 배포하여 상용화하는 방법을 안내합니다.

---

## 🛠️ A. 로컬 백엔드 서버 구동 방법 (Flask + SQLite)

로컬에서 웹 사이트와 백엔드 서비스를 함께 테스트하려면 아래 단계를 따릅니다. (Python 3.10 이상 권장)

### 1단계: 가상환경 구성 및 패키지 인스톨
```bash
# 프로젝트 폴더로 이동 후 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\activate
# 가상환경 활성화 (Mac / Linux)
source venv/bin/activate

# 로컬 백엔드용 의존 라이브러리 설치
pip install -r backend/requirements.txt
```

### 2단계: Flask 서버 기동 및 브라우저 접속
```bash
python backend/app.py
```
* 서버가 켜지면 브라우저를 열어 **[http://localhost:5000](http://localhost:5000)**에 접속합니다. 모든 설정과 리뷰 이력은 백엔드 `backend/database.db` SQLite 파일에 영구 저장됩니다.

---

## ☁️ B. Streamlit Community Cloud 배포 방법 (클라우드 배포)

이 프로젝트는 Streamlit Cloud에 즉시 배포할 수 있는 **[streamlit_app.py](file:///c:/Users/tomba/OneDrive/문서/GitHub/code-review-ai-agent/streamlit_app.py)**를 지원합니다. 리포지토리가 이미 깃허브에 연결되어 있으므로 아래 설정만 완료하면 즉시 배포됩니다.

### 1단계: 깃허브 코드 푸시 (Push to GitHub)
생성된 아래의 새로운 배포용 파일들이 깃허브 리포지토리에 푸시되어 있는지 확인합니다.
- `streamlit_app.py`: 루트 경로에 배치된 Streamlit 배포 앱
- `requirements.txt`: 루트 경로에 배치된 Streamlit 패키지 의존성 파일 (`streamlit`, `requests` 탑재)

### 2단계: Streamlit Cloud 배포 설정
1. **[Streamlit Community Cloud](https://share.streamlit.io/)**에 로그인합니다.
2. 우측 상단의 **'Create app'** (또는 **'New app'**) 버튼을 누릅니다.
3. 배포 설정 페이지를 작성합니다:
   - **Repository**: 연결된 본 프로젝트 리포지토리 선택 (`code-review-ai-agent`)
   - **Branch**: 배포 대상 브라우저 브랜치 선택 (예: `main` 또는 `master`)
   - **Main file path**: **`streamlit_app.py`** 입력 (매우 중요)
4. 우측 하단의 **'Deploy!'** 버튼을 누릅니다.

### 3단계: 배포 완료 및 동작 확인
* 배포가 완료되면 `https://<your-app-name>.streamlit.app/` 형식의 고유 서브도메인 주소가 발급됩니다.
* **디자인 및 하이라이트 동기화**: Streamlit 내에서도 HTML/CSS 마크다운 렌더러를 통해 **라이트 테마**와 **수정 코드 라인 하이라이팅(형광 라임색)**이 로컬 버전과 완벽하게 동일한 비주얼로 표현됩니다.
* **데이터 보존**: 백엔드 SQLite DB 연동에 의해 데이터가 작동하며, 클라우드 서버 컨테이너가 유휴 상태로 진입해 자동 재시작되기 전까지 리뷰 이력과 설정 정보가 매끄럽게 유지됩니다.
