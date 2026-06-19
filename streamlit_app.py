import streamlit as st
import sqlite3
import requests
import os
import re
from datetime import datetime
import difflib
from dotenv import load_dotenv

# ----------------------------------------------------
# 1. Streamlit Page Configuration & Injecting Style CSS
# ----------------------------------------------------
st.set_page_config(
    page_title="CodeReview AI - 스마트 코드 리뷰 에이전트",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Theme Rebrand and Code Diff Highlighting (Matching style.css exactly)
CUSTOM_CSS = """
<style>
    /* outfit Google font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Fira+Code:wght@400;500&display=swap');
    
    :root {
        --caution-bg: #fffbfb;
        --caution-border: rgba(239, 68, 68, 0.2);
        --caution-color: #7f1d1d;
        --improvement-bg: #fbfdfb;
        --improvement-border: rgba(16, 185, 129, 0.2);
        --improvement-color: #14532d;
        --table-th-bg: rgba(15, 23, 42, 0.02);
        --table-th-color: #0f172a;
        --table-td-color: #334155;
        --table-border: rgba(15, 23, 42, 0.08);
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --caution-bg: #2d1919;
            --caution-border: rgba(239, 68, 68, 0.4);
            --caution-color: #fca5a5;
            --improvement-bg: #14251c;
            --improvement-border: rgba(16, 185, 129, 0.4);
            --improvement-color: #a7f3d0;
            --table-th-bg: rgba(255, 255, 255, 0.04);
            --table-th-color: #f1f5f9;
            --table-td-color: #cbd5e1;
            --table-border: rgba(255, 255, 255, 0.1);
        }
    }
    
    .main .block-container {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }
    
    /* Headers styling */
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        color: var(--text-color) !important;
        font-weight: 700 !important;
    }
    
    /* Codeblock styling overrides */
    .caution-codeblock {
        border: 1px solid var(--caution-border) !important;
        background-color: var(--caution-bg) !important;
        border-radius: 0.75rem;
        padding: 1.25rem !important;
        position: relative;
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
        white-space: pre;
        overflow-x: auto;
        color: var(--text-color) !important;
    }
    
    .improvement-codeblock {
        border: 1px solid var(--improvement-border) !important;
        background-color: var(--improvement-bg) !important;
        border-radius: 0.75rem;
        padding: 1.25rem !important;
        position: relative;
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
        white-space: pre;
        overflow-x: auto;
        color: var(--text-color) !important;
    }
    
    /* Code Line Diff Highlighting Styles */
    .diff-line-removed {
        background-color: #fca5a5 !important; /* Stronger red tint */
        border-left: 3px solid #ef4444;
        display: inline-block;
        width: 100%;
        padding-left: 0.5rem;
        color: #7f1d1d !important;
    }
    
    .diff-line-added {
        background-color: lime !important; /* Vivid lime green */
        border-left: 3px solid #10b981;
        display: inline-block;
        width: 100%;
        padding-left: 0.5rem;
        color: #14532d !important;
        font-weight: 500;
    }
    
    @media (prefers-color-scheme: dark) {
        .diff-line-removed {
            background-color: rgba(239, 68, 68, 0.3) !important;
            color: #fca5a5 !important;
        }
        
        .diff-line-added {
            background-color: rgba(16, 185, 129, 0.3) !important;
            color: #a7f3d0 !important;
        }
    }
    
    /* Summary table customization */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5rem 0;
        font-size: 0.875rem;
    }
    
    th {
        background: var(--table-th-bg) !important;
        color: var(--table-th-color) !important;
        font-weight: 600;
        border: 1px solid var(--table-border) !important;
        padding: 0.75rem 1rem;
    }
    
    td {
        border: 1px solid var(--table-border) !important;
        padding: 0.75rem 1rem;
        color: var(--table-td-color) !important;
    }
    
    /* Sidebar styling overrides */
    .css-1542moe, .stSidebar {
        background-color: var(--secondary-background-color) !important;
        border-right: 1px solid var(--border-color, #e2e8f0);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Database Integration (SQLite)
# ----------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "database.db")

# Load environment variables from .env in project root directory
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_db_connection():
    # Make sure parent directory backend exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            bugs TEXT,
            improvements TEXT,
            htmlContent TEXT
        )
    ''')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'api_key'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('api_key', ?)", (DEFAULT_API_KEY,))
        cursor.execute("INSERT INTO settings (key, value) VALUES ('model', 'gpt-4o-mini')")
    conn.commit()
    conn.close()

init_db()

# DB Helpers
def get_db_setting(key, default):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default

def save_db_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def save_review_history(date, bugs, improvements, htmlContent):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (date, bugs, improvements, htmlContent) VALUES (?, ?, ?, ?)",
        (date, bugs, improvements, htmlContent)
    )
    conn.commit()
    conn.close()

def get_review_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, bugs, improvements, htmlContent FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_history_item(history_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()

def clear_all_history():
    conn = get_db_connection()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()

# ----------------------------------------------------
# 3. Code Diff Match and Highlight Engine (Replaces JS engine)
# ----------------------------------------------------
def highlight_code_lines_diff(old_code, new_code):
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    d = difflib.Differ()
    diff = list(d.compare(old_lines, new_lines))
    
    old_out = []
    new_out = []
    
    for line in diff:
        if line.startswith('- '):
            content = line[2:]
            # Escape HTML characters safely
            content_esc = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            old_out.append(f'<span class="diff-line-removed">{content_esc}</span>')
        elif line.startswith('+ '):
            content = line[2:]
            content_esc = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            new_out.append(f'<span class="diff-line-added">{content_esc}</span>')
        elif line.startswith('  '):
            content = line[2:]
            content_esc = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            old_out.append(content_esc)
            new_out.append(content_esc)
            
    return '\n'.join(old_out), '\n'.join(new_out)

def post_process_markdown_review(markdown_text):
    # Regex to find caution block and matching improvement block:
    # ⚠️ **기존 코드**
    # ```python
    # ...
    # ```
    # 💡 **개선 코드**
    # ```python
    # ...
    # ```
    pattern = r"⚠️ \*\*기존 코드\*\*\s*```[a-zA-Z]*\n(.*?)\n```\s*💡 \*\*개선 코드\*\*\s*```[a-zA-Z]*\n(.*?)\n```"
    
    def replace_match(match):
        old_code = match.group(1)
        new_code = match.group(2)
        
        # Calculate HTML diff lines
        highlighted_old, highlighted_new = highlight_code_lines_diff(old_code, new_code)
        
        html_output = f"""
<p><strong>⚠️ 기존 코드</strong></p>
<pre class="caution-codeblock"><code>{highlighted_old}</code></pre>
<p><strong>💡 개선 코드</strong></p>
<pre class="improvement-codeblock"><code>{highlighted_new}</code></pre>
"""
        return html_output

    processed_text = re.sub(pattern, replace_match, markdown_text, flags=re.DOTALL)
    return processed_text

# ----------------------------------------------------
# 4. GitHub Fetch logic
# ----------------------------------------------------
def fetch_github_source(url):
    # Public raw contents download
    pr_match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    file_match = re.search(r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
    
    try:
        if pr_match:
            owner, repo, number = pr_match.groups()
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
            headers = {"Accept": "application/vnd.github.diff"}
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.text, "Pull Request Diff 데이터를 성공적으로 로드했습니다!"
        elif file_match:
            owner, repo, branch, filepath = file_match.groups()
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filepath}"
            res = requests.get(raw_url, timeout=15)
            if res.status_code == 200:
                return res.text, "GitHub 소스코드 본문을 성공적으로 로드했습니다!"
        else:
            return None, "올바른 GitHub 파일 또는 PR 주소가 아닙니다."
            
        return None, f"불러오기 실패 (HTTP {res.status_code})"
    except Exception as e:
        return None, f"네트워크 오류 발생: {str(e)}"

# ----------------------------------------------------
# 5. Preset demos
# ----------------------------------------------------
PRESETS = {
    "Python: SQL 인젝션 & 파일 자원 누수": {
        "code": """import sqlite3

def get_user_data(user_id):
    # ⚠️ 취약점: SQL Injection 위험
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    row = cursor.fetchone()
    
    # ⚠️ 자원 누수: 예외 발생 시 close가 실행되지 않음
    conn.close()
    return row

def save_log(message):
    f = open("log.txt", "a")
    f.write(message + "\\n")
    f.close()
""",
        "review": """# 코드 리뷰 분석 요약

| 분류 | 개수 | 핵심 내용 요약 |
| :--- | :---: | :--- |
| ⚠️ **주의 버그 (Bug/Security)** | 2개 | SQL 인젝션 보안 취약점 존재 및 자원 누수 위험 |
| 💡 **단순 개선 (Refactoring/Style)** | 1개 | Pythonic한 예외 처리 및 자원 관리 패턴 전환 권장 |

---

## ⚠️ 주의 버그 (Bug Warning)

### 1. SQL Injection (보안 취약점)
* **이유**: 사용자 입력값 \`user_id\`를 f-string 문자열 포맷팅으로 쿼리에 직접 결합하여 SQL Injection 공격에 취약합니다. 입력값이 바인딩 매개변수로 안전하게 치환되도록 플레이스홀더(\`?\`) 방식을 적용해야 합니다.

⚠️ **기존 코드**
```python
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
```

💡 **개선 코드**
```python
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

---

### 2. 자원 누수 (Resource Leak)
* **이유**: 데이터베이스 커넥션 생성 후 예외가 발생할 경우 \`conn.close()\`가 호출되지 않은 채 종료되어 리소스 누수가 일어날 수 있습니다. Python의 \`contextlib\`이나 \`with\` 문(Context Manager)을 사용하는 구조로 코드를 재배치해야 합니다.

⚠️ **기존 코드**
```python
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
row = cursor.fetchone()
conn.close()
return row
```

💡 **개선 코드**
```python
from contextlib import closing

with sqlite3.connect('users.db') as conn:
    with closing(conn.cursor()) as cursor:
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
```

---

## 💡 단순 개선 (Improvement)

### 1. 파일 오픈 컨텍스트 매니저 사용
* **이유**: \`save_log\` 함수 내에서 파일을 열고 직접 \`f.close()\`를 호출하고 있습니다. 이 역시 중간에 에러가 발생할 시 파일 서술자(File Descriptor) 누수로 이어질 수 있으므로 파이썬의 표준 \`with open()\` 구조를 활용하는 것을 강력하게 권장합니다.

⚠️ **기존 코드**
```python
def save_log(message):
    f = open("log.txt", "a")
    f.write(message + "\\n")
    f.close()
```

💡 **개선 코드**
```python
def save_log(message):
    with open("log.txt", "a") as f:
        f.write(message + "\\n")
```
"""
    },
    "JavaScript: Memory Leak & 성능 루프": {
        "code": """// 비효율적인 루프 및 클로저 캡처
function processArray(arr) {
    let result = [];
    for (var i = 0; i < arr.length; i++) {
        // ⚠️ 루프 내 클로저 함수 생성 및 var 캡처로 인한 참조 오류 유발
        (function() {
            var item = arr[i];
            result.push(function() {
                return item * 2;
            });
        })();
    }
    return result;
}

function processUserData(users) {
    // 💡 굳이 매번 range(len) 처럼 index로 복잡하게 루프를 돌림
    for (var i = 0; i < users.length; i++) {
        console.log("User Name: " + users[i].name);
    }
}
""",
        "review": """# 코드 리뷰 분석 요약

| 분류 | 개수 | 핵심 내용 요약 |
| :--- | :---: | :--- |
| ⚠️ **주의 버그 (Bug/Security)** | 1개 | 루프 인덱스 바인딩 스코프 오류 및 불필요한 클로저 함수 선언 |
| 💡 **단순 개선 (Refactoring/Style)** | 1개 | 복잡한 인덱스 루프를 Modern JavaScript(for...of) 패턴으로 개선 |

---

## ⚠️ 주의 버그 (Bug Warning)

### 1. var 변수 스코프 캡처 오동작
* **이유**: 루프에서 \`var i\`를 선언하고 즉시 실행 함수(IIFE)로 래핑하여 내부 스코프를 나눴으나, 루프 블록 내에서 굳이 익명 함수를 중첩 생성하여 클로저를 반환함으로써 메모리 누수 위험이 있으며 구조가 매우 비효율적입니다. \`let\` 키워드를 사용해 블록 스코프를 지정하고 불필요한 즉시 실행 함수를 제거해야 합니다.

⚠️ **기존 코드**
```javascript
for (var i = 0; i < arr.length; i++) {
    (function() {
        var item = arr[i];
        result.push(function() {
            return item * 2;
        });
    })();
}
```

💡 **개선 코드**
```javascript
for (let i = 0; i < arr.length; i++) {
    const item = arr[i];
    result.push(() => item * 2);
}
```

---

## 💡 단순 개선 (Improvement)

### 1. Modern JavaScript Iteration 적용
* **이유**: 단순 요소 접근 시 인덱스 변수(\`i\`)를 관리하는 전통적인 \`for (var i = 0;...)\` 패턴은 실수를 유발하기 쉽고 코드가 장황해집니다. 배열 순회 시에는 가독성이 뛰어난 \`for...of\` 또는 \`forEach\` 구문을 사용하는 것이 유지보수 측면에서 매우 유리합니다.

⚠️ **기존 코드**
```javascript
for (var i = 0; i < users.length; i++) {
    console.log("User Name: " + users[i].name);
}
```

💡 **개선 코드**
```javascript
for (const user of users) {
    console.log("User Name: " + user.name);
}
```
"""
    }
}

# ----------------------------------------------------
# 6. Streamlit Layout Drawing
# ----------------------------------------------------
st.sidebar.title("🛡️ CodeReview AI")
st.sidebar.caption("스마트 코드 리뷰 에이전트 (Streamlit Cloud)")

# Sidebar Settings Section
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ API 설정")

# Get API key from environment variables with DB key as a fallback
api_key = DEFAULT_API_KEY
if not api_key:
    api_key = get_db_setting("api_key", "")

# Display API key status safely
if api_key:
    st.sidebar.info("🔑 API Key: 환경 변수(.env)에서 로드 완료")
else:
    st.sidebar.warning("⚠️ API Key: 환경 변수(.env) 설정 필요")

saved_model = get_db_setting("model", "gpt-4o-mini")
model_selector = st.sidebar.selectbox("AI 모델 지정", ["gpt-4o-mini", "gpt-4o"], index=0 if saved_model == "gpt-4o-mini" else 1)

if st.sidebar.button("설정 저장"):
    save_db_setting("model", model_selector)
    st.sidebar.success("SQLite DB에 설정이 저장되었습니다!")

st.sidebar.markdown("---")
st.sidebar.info("해당 설정 및 리뷰 기록은 로컬 `database.db`에 영구 보존됩니다. (Streamlit Cloud 배포 시 인스턴스가 리셋될 때까지 영구 유지)")

# Main Menu Tabs
menu_tab1, menu_tab2 = st.tabs(["📝 새 리뷰 분석", "📜 리뷰 이력"])

# --- TAB 1: NEW REVIEW ---
with menu_tab1:
    st.header("새 리뷰 작성 및 분석")
    
    # Input Selection
    input_source = st.radio("입력 소스 선택", ["직접 코드 입력", "GitHub URL 연동"], horizontal=True)
    
    code_input_val = ""
    
    if input_source == "GitHub URL 연동":
        st.subheader("GitHub URL 로드")
        github_url = st.text_input("GitHub URL 주소 (File Blob 또는 PR 주소)", placeholder="https://github.com/owner/repo/blob/main/main.py")
        if st.button("코드 가져오기 (Fetch)"):
            if github_url:
                fetched_code, msg = fetch_github_source(github_url)
                if fetched_code:
                    st.session_state["fetched_code_state"] = fetched_code
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("GitHub 주소를 기입해 주세요.")
                
        code_input_val = st.session_state.get("fetched_code_state", "")

    # Preset / Demo selector
    preset_choice = st.selectbox("💡 데모용 샘플 로드 (빠른 연동 체험)", ["선택 안 함"] + list(PRESETS.keys()))
    if preset_choice != "선택 안 함":
        code_input_val = PRESETS[preset_choice]["code"]
        st.session_state["fetched_code_state"] = code_input_val

    # Main text editor
    code_to_review = st.text_area("소스 코드 입력창", value=code_input_val, height=300)
    
    col_clear, col_run = st.columns([1, 6])
    with col_clear:
        if st.button("초기화"):
            st.session_state["fetched_code_state"] = ""
            st.rerun()
            
    with col_run:
        if st.button("AI 리뷰 분석 실행", type="primary"):
            if not code_to_review.strip():
                st.warning("분석할 소스코드를 입력해 주세요.")
            else:
                # Execution
                with st.spinner("AI 에이전트가 코드를 정밀 분석 중입니다..."):
                    # Check if it is a preset and code matches, run mock review
                    is_preset = False
                    for name, preset_data in PRESETS.items():
                        if preset_choice == name and preset_data["code"] == code_to_review:
                            is_preset = True
                            review_markdown = preset_data["review"]
                            break
                            
                    if not is_preset:
                        # Call Real OpenAI
                        try:
                            system_prompt = """너는 풀스택 시니어 소프트웨어 엔지니어이자 코드 리뷰 전문가이다. 
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
- 모든 설명은 한글(Korean)로 작성해라."""
                            
                            response = requests.post(
                                "https://api.openai.com/v1/chat/completions",
                                headers={
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {api_key}"
                                },
                                json={
                                    "model": model_selector,
                                    "messages": [
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": f"아래 코드에 대해 리뷰를 해줘:\n\n{code_to_review}"}
                                    ],
                                    "temperature": 0.1
                                },
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                review_markdown = response.json()['choices'][0]['message']['content']
                            else:
                                err_msg = response.json().get('error', {}).get('message', '알 수 없는 오류')
                                st.error(f"OpenAI API 오류: {err_msg}")
                                review_markdown = None
                        except Exception as e:
                            st.error(f"통신 중 예외 발생: {str(e)}")
                            review_markdown = None
                            
                    if review_markdown:
                        # Post process markdown review for custom line highlighting
                        html_review = post_process_markdown_review(review_markdown)
                        
                        # Store in session state for rendering and saving
                        st.session_state["latest_review"] = html_review
                        st.session_state["latest_review_md"] = review_markdown

    # Render results if present
    if "latest_review" in st.session_state:
        st.markdown("---")
        st.subheader("코드 분석 결과 리포트")
        
        # Save to DB button
        if st.button("DB에 저장"):
            # Parse metrics
            bug_count = "0개"
            improvement_count = "0개"
            
            # Simple text parsing for bug counts
            bugs_match = re.search(r"주의 버그 \(Bug/Security\)\s*\|\s*(\d+개)", st.session_state["latest_review_md"])
            imps_match = re.search(r"단순 개선 \(Refactoring/Style\)\s*\|\s*(\d+개)", st.session_state["latest_review_md"])
            
            if bugs_match: bug_count = bugs_match.group(1)
            if imps_match: improvement_count = imps_match.group(1)
            
            save_review_history(
                datetime.now().strftime("%Y. %m. %d. %p %I:%M:%S"),
                bug_count,
                improvement_count,
                st.session_state["latest_review"]
            )
            st.success("SQLite DB에 리뷰 결과가 영구 저장되었습니다!")
            
        # Display the custom rendered review report with line diff highlights
        st.markdown(st.session_state["latest_review"], unsafe_allow_html=True)
        
        # Celebrate if 0 bugs!
        if "| ⚠️ **주의 버그 (Bug/Security)** | 0개" in st.session_state["latest_review_md"]:
            st.balloons()

# --- TAB 2: REVIEW HISTORY ---
with menu_tab2:
    st.header("저장된 리뷰 히스토리 (SQLite DB)")
    
    col_refresh, col_clear_all = st.columns([1, 6])
    with col_refresh:
        if st.button("이력 새로고침"):
            st.rerun()
    with col_clear_all:
        if st.button("전체 이력 삭제", type="secondary"):
            clear_all_history()
            st.success("데이터베이스의 모든 리뷰 기록이 삭제되었습니다.")
            st.rerun()
            
    history_items = get_review_history()
    
    if not history_items:
        st.info("저장된 코드 리뷰 기록이 없습니다.")
    else:
        for item in history_items:
            # Create a card-like layout for each history item
            with st.expander(f"📅 {item['date']} | ⚠️ 버그: {item['bugs']} | 💡 개선: {item['improvements']}"):
                col_del, _ = st.columns([1, 8])
                with col_del:
                    if st.button("삭제", key=f"del_{item['id']}"):
                        delete_history_item(item['id'])
                        st.success("삭제 완료!")
                        st.rerun()
                
                # Render content
                st.markdown(item['htmlContent'], unsafe_allow_html=True)
