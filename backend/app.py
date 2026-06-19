import os
import sqlite3
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Configure static folders to robustly point to frontend/ relative to app.py
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')

# Load environment variables from .env in project root directory
load_dotenv(os.path.join(os.path.dirname(backend_dir), '.env'))

# User's default API key
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# SQLite configuration
db_path = os.path.join(backend_dir, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Settings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # History table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            bugs TEXT,
            improvements TEXT,
            htmlContent TEXT
        )
    ''')
    
    # Pre-populate settings if empty
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'api_key'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('api_key', ?)", (DEFAULT_API_KEY,))
        cursor.execute("INSERT INTO settings (key, value) VALUES ('model', 'gpt-4o-mini')")
    
    conn.commit()
    conn.close()

# Initialize SQLite database
init_db()

# ----------------------------------------------------
# Static Routing
# ----------------------------------------------------
@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

# ----------------------------------------------------
# API Routes
# ----------------------------------------------------

# 1. Settings Endpoints
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    settings_dict = {row['key']: row['value'] for row in rows}
    # Return masked API key for security if requested, but for simplicity of this app
    # we return it directly. The client side hides the key anyway.
    return jsonify(settings_dict)

@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.json
    api_key = data.get('api_key', '').strip()
    model = data.get('model', 'gpt-4o-mini').strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('api_key', ?)", (api_key,))
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('model', ?)", (model,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Settings saved successfully"})

# 2. History Endpoints
@app.route('/api/history', methods=['GET'])
def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, bugs, improvements, htmlContent FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        history_list.append({
            "id": row["id"],
            "date": row["date"],
            "bugs": row["bugs"],
            "improvements": row["improvements"],
            "htmlContent": row["htmlContent"]
        })
    return jsonify(history_list)

@app.route('/api/history', methods=['POST'])
def add_history():
    data = request.json
    date = data.get('date')
    bugs = data.get('bugs')
    improvements = data.get('improvements')
    html_content = data.get('htmlContent')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (date, bugs, improvements, htmlContent) VALUES (?, ?, ?, ?)",
        (date, bugs, improvements, html_content)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return jsonify({"status": "success", "id": new_id})

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history_item(history_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "History item deleted"})

@app.route('/api/history', methods=['DELETE'])
def clear_all_history():
    conn = get_db_connection()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "All history logs cleared"})

# 3. Code Review AI Analysis Endpoint
@app.route('/api/review', methods=['POST'])
def run_review():
    data = request.json
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # Retrieve current API credentials from SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'api_key'")
    row_key = cursor.fetchone()
    cursor.execute("SELECT value FROM settings WHERE key = 'model'")
    row_model = cursor.fetchone()
    conn.close()

    api_key = row_key['value'] if row_key else DEFAULT_API_KEY
    model = row_model['value'] if row_model else "gpt-4o-mini"

    if not api_key:
        return jsonify({"error": "OpenAI API Key is missing in database settings"}), 400

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

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"아래 코드에 대해 리뷰를 해줘:\n\n{code}"}
                ],
                "temperature": 0.1
            },
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', f"HTTP 오류 {response.status_code}")
            return jsonify({"error": f"OpenAI API 오류: {error_msg}"}), 500
            
        result_data = response.json()
        review_text = result_data['choices'][0]['message']['content']
        return jsonify({"review": review_text})
        
    except Exception as e:
        return jsonify({"error": f"백엔드 요청 처리 중 예외 발생: {str(e)}"}), 500

if __name__ == '__main__':
    # Start server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
