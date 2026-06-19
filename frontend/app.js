// State management
let reviewHistory = [];
let currentInputSource = 'manual'; // 'manual' or 'github'

// Interactive presets (Code and corresponding pre-baked OpenAI response)
const SAMPLE_CODES = {
    "python-vuln": {
        name: "Python: SQL 인젝션 & 파일 자원 누수",
        code: `import sqlite3

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
`,
        review: `# 코드 리뷰 분석 요약

| 분류 | 개수 | 핵심 내용 요약 |
| :--- | :---: | :--- |
| ⚠️ **주의 버그 (Bug/Security)** | 2개 | SQL 인젝션 보안 취약점 존재 및 자원 누수 위험 |
| 💡 **단순 개선 (Refactoring/Style)** | 1개 | Pythonic한 예외 처리 및 자원 관리 패턴 전환 권장 |

---

## ⚠️ 주의 버그 (Bug Warning)

### 1. SQL Injection (보안 취약점)
* **이유**: 사용자 입력값 \`user_id\`를 f-string 문자열 포깝팅으로 쿼리에 직접 결합하여 SQL Injection 공격에 취약합니다. 입력값이 바인딩 매개변수로 안전하게 치환되도록 플레이스홀더(\`?\`) 방식을 적용해야 합니다.

⚠️ **기존 코드**
\`\`\`python
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
\`\`\`

💡 **개선 코드**
\`\`\`python
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
\`\`\`

---

### 2. 자원 누수 (Resource Leak)
* **이유**: 데이터베이스 커넥션 생성 후 예외가 발생할 경우 \`conn.close()\`가 호출되지 않은 채 종료되어 리소스 누수가 일어날 수 있습니다. Python의 \`contextlib\`이나 \`with\` 문(Context Manager)을 사용하는 구조로 코드를 재배치해야 합니다.

⚠️ **기존 코드**
\`\`\`python
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
row = cursor.fetchone()
conn.close()
return row
\`\`\`

💡 **개선 코드**
\`\`\`python
from contextlib import closing

with sqlite3.connect('users.db') as conn:
    with closing(conn.cursor()) as cursor:
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
\`\`\`

---

## 💡 단순 개선 (Improvement)

### 1. 파일 오픈 컨텍스트 매니저 사용
* **이유**: \`save_log\` 함수 내에서 파일을 열고 직접 \`f.close()\`를 호출하고 있습니다. 이 역시 중간에 에러가 발생할 시 파일 서술자(File Descriptor) 누수로 이어질 수 있으므로 파이썬의 표준 \`with open()\` 구조를 활용하는 것을 강력하게 권장합니다.

⚠️ **기존 코드**
\`\`\`python
def save_log(message):
    f = open("log.txt", "a")
    f.write(message + "\\n")
    f.close()
\`\`\`

💡 **개선 코드**
\`\`\`python
def save_log(message):
    with open("log.txt", "a") as f:
        f.write(message + "\\n")
\`\`\`
`
    },
    "js-perf": {
        name: "JavaScript: Memory Leak & 성능 루프",
        code: `// 비효율적인 루프 및 클로저 캡처
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
`,
        review: `# 코드 리뷰 분석 요약

| 분류 | 개수 | 핵심 내용 요약 |
| :--- | :---: | :--- |
| ⚠️ **주의 버그 (Bug/Security)** | 1개 | 루프 인덱스 바인딩 스코프 오류 및 불필요한 클로저 함수 선언 |
| 💡 **단순 개선 (Refactoring/Style)** | 1개 | 복잡한 인덱스 루프를 Modern JavaScript(for...of) 패턴으로 개선 |

---

## ⚠️ 주의 버그 (Bug Warning)

### 1. var 변수 스코프 캡처 오동작
* **이유**: 루프에서 \`var i\`를 선언하고 즉시 실행 함수(IIFE)로 래핑하여 내부 스코프를 나눴으나, 루프 블록 내에서 굳이 익명 함수를 중첩 생성하여 클로저를 반환함으로써 메모리 누수 위험이 있으며 구조가 매우 비효율적입니다. \`let\` 키워드를 사용해 블록 스코프를 지정하고 불필요한 즉시 실행 함수를 제거해야 합니다.

⚠️ **기존 코드**
\`\`\`javascript
for (var i = 0; i < arr.length; i++) {
    (function() {
        var item = arr[i];
        result.push(function() {
            return item * 2;
        });
    })();
}
\`\`\`

💡 **개선 코드**
\`\`\`javascript
for (let i = 0; i < arr.length; i++) {
    const item = arr[i];
    result.push(() => item * 2);
}
\`\`\`

---

## 💡 단순 개선 (Improvement)

### 1. Modern JavaScript Iteration 적용
* **이유**: 단순 요소 접근 시 인덱스 변수(\`i\`)를 관리하는 전통적인 \`for (var i = 0;...)\` 패턴은 실수를 유발하기 쉽고 코드가 장황해집니다. 배열 순회 시에는 가독성이 뛰어난 \`for...of\` 또는 \`forEach\` 구문을 사용하는 것이 유지보수 측면에서 매우 유리합니다.

⚠️ **기존 코드**
\`\`\`javascript
for (var i = 0; i < users.length; i++) {
    console.log("User Name: " + users[i].name);
}
\`\`\`

💡 **개선 코드**
\`\`\`javascript
for (const user of users) {
    console.log("User Name: " + user.name);
}
\`\`\`
`
    }
};

// Initial Setup - Load settings and history from Python Backend sqlite db
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    
    // Sync settings and history from Flask server
    loadSettingsFromServer();
    loadHistoryFromServer();
});

// Sync current API config from Flask Server
async function loadSettingsFromServer() {
    try {
        const response = await fetch("/api/settings");
        if (!response.ok) throw new Error("서버로부터 설정을 읽어오는데 실패했습니다.");
        const data = await response.json();
        
        document.getElementById("model-selector").value = data.model || "gpt-4o-mini";
        
        // Render API Key loading status on sidebar status
        const sidebarKeyEl = document.getElementById("api-status-key-label");
        if (data.has_api_key) {
            sidebarKeyEl.innerText = "API Key: 로드 완료 (.env)";
        } else {
            sidebarKeyEl.innerText = "API Key: 설정 필요 (.env)";
        }
    } catch (error) {
        console.error(error);
    }
}

// Sync saved review history list from Flask Server SQLite DB
async function loadHistoryFromServer() {
    try {
        const response = await fetch("/api/history");
        if (!response.ok) throw new Error("이력 데이터를 조회하는 중 백엔드 오류가 발생했습니다.");
        reviewHistory = await response.json();
        renderHistory();
    } catch (error) {
        console.error(error);
    }
}

// Save settings to Flask SQLite DB
async function saveSettings() {
    const model = document.getElementById("model-selector").value;

    try {
        const response = await fetch("/api/settings", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ model: model })
        });

        if (!response.ok) throw new Error("백엔드에 설정을 저장하지 못했습니다.");
        const result = await response.json();
        alert(result.message || "설정이 데이터베이스에 저장되었습니다!");
        
        // Refresh settings UI
        loadSettingsFromServer();
    } catch (error) {
        alert("설정 저장 오류: " + error.message);
    }
}

// Toggle input source between manual and github
function toggleInputSource(source) {
    currentInputSource = source;
    const btnManual = document.getElementById("btn-input-manual");
    const btnGithub = document.getElementById("btn-input-github");
    const githubSection = document.getElementById("github-url-section");
    const inputTitle = document.getElementById("input-title-label");

    if (source === 'manual') {
        btnManual.className = "pb-3 px-4 text-sm font-semibold border-b-2 border-brand-500 text-brand-600 focus:outline-none transition-all duration-300";
        btnGithub.className = "pb-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-600 focus:outline-none transition-all duration-300";
        githubSection.classList.add("hidden");
        inputTitle.innerText = "소스 코드 입력창";
    } else {
        btnManual.className = "pb-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-600 focus:outline-none transition-all duration-300";
        btnGithub.className = "pb-3 px-4 text-sm font-semibold border-b-2 border-brand-500 text-brand-600 focus:outline-none transition-all duration-300";
        githubSection.classList.remove("hidden");
        inputTitle.innerText = "가져온 소스 코드 확인 및 편집";
    }
}

// Fetch Code/Diff from GitHub URL
async function fetchGitHubCode() {
    const urlInput = document.getElementById("github-url-input").value.trim();
    const statusEl = document.getElementById("github-fetch-status");
    
    if (!urlInput) {
        alert("GitHub URL 주소를 입력해주세요!");
        return;
    }

    statusEl.innerText = "GitHub로부터 코드를 불러오는 중...";
    statusEl.className = "text-xs text-brand-500 font-semibold";
    statusEl.classList.remove("hidden");

    try {
        let fetchUrl = "";
        let isPr = false;

        const prMatch = urlInput.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
        const fileMatch = urlInput.match(/github\.com\/([^\/]+)\/([^\/]+)\/blob\/([^\/]+)\/(.+)/);

        if (prMatch) {
            isPr = true;
            const owner = prMatch[1];
            const repo = prMatch[2];
            const number = prMatch[3];
            fetchUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;
        } else if (fileMatch) {
            const owner = fileMatch[1];
            const repo = fileMatch[2];
            const branch = fileMatch[3];
            const filePath = fileMatch[4];
            fetchUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${filePath}`;
        } else {
            throw new Error("올바른 GitHub 파일 URL 또는 Pull Request URL 형식이 아닙니다.");
        }

        let response;
        if (isPr) {
            response = await fetch(fetchUrl, {
                headers: {
                    "Accept": "application/vnd.github.diff"
                }
            });
        } else {
            response = await fetch(fetchUrl);
        }

        if (!response.ok) {
            throw new Error(`불러오기 실패 (HTTP ${response.status}). 저장소가 Public 상태이고 URL이 올바른지 확인해 주세요.`);
        }

        const content = await response.text();
        document.getElementById("code-input").value = content;
        
        statusEl.innerText = "성공적으로 코드를 불러왔습니다!";
        statusEl.className = "text-xs text-emerald-600 font-semibold";
    } catch (error) {
        console.error(error);
        statusEl.innerText = `오류: ${error.message}`;
        statusEl.className = "text-xs text-red-500 font-semibold";
        alert(`코드 불러오기 실패:\n${error.message}\n\n만약 CORS 정책에 의해 차단된 경우, 코드 내용을 직접 복사하여 아래 입력창에 붙여넣어 주세요.`);
    }
}

// Tab Switch Logic
function switchTab(tabId) {
    const tabs = ['new-review', 'history', 'settings', 'report-view'];
    tabs.forEach(id => {
        const btn = document.getElementById(`tab-${id}`);
        const content = document.getElementById(`content-${id}`);
        
        if (btn) btn.classList.remove('active');
        if (content) content.classList.add('hidden');
    });
    
    const targetBtn = document.getElementById(`tab-${tabId}`);
    const targetContent = document.getElementById(`content-${tabId}`);
    
    if (targetBtn) targetBtn.classList.add('active');
    if (targetContent) targetContent.classList.remove('hidden');
    
    const titles = {
        'new-review': '새 리뷰 작성',
        'report-view': '리뷰 리포트 상세',
        'history': '리뷰 히스토리 목록',
        'settings': '환경 설정'
    };
    document.getElementById("workspace-title").innerText = titles[tabId] || 'CodeReview AI';
}

function clearInput() {
    document.getElementById("code-input").value = "";
    document.getElementById("sample-selector").value = "";
    document.getElementById("github-url-input").value = "";
    document.getElementById("github-fetch-status").classList.add("hidden");
}

function loadSampleCode() {
    const preset = document.getElementById("sample-selector").value;
    if (SAMPLE_CODES[preset]) {
        document.getElementById("code-input").value = SAMPLE_CODES[preset].code;
    } else {
        document.getElementById("code-input").value = "";
    }
}

async function runCodeReview() {
    const code = document.getElementById("code-input").value.trim();
    if (!code) {
        alert("분석할 소스 코드를 먼저 입력해주세요!");
        return;
    }

    const overlay = document.getElementById("loading-overlay");
    const stepEl = document.getElementById("loading-step");
    overlay.classList.remove("hidden");

    const steps = [
        "Diff 코드를 토큰화하고 의미 분석 구조를 생성 중...",
        "백엔드 Python API를 통해 OpenAI 분석 처리 중...",
        "디프 하이라이터 렌더링 중..."
    ];

    let stepIdx = 0;
    stepEl.innerText = steps[stepIdx];
    const stepInterval = setInterval(() => {
        if (stepIdx < steps.length - 1) {
            stepIdx++;
            stepEl.innerText = steps[stepIdx];
        }
    }, 1500);

    try {
        const selectedPreset = document.getElementById("sample-selector").value;
        let finalReviewText = "";

        // Instant preset evaluation
        if (selectedPreset && SAMPLE_CODES[selectedPreset] && SAMPLE_CODES[selectedPreset].code === code) {
            await new Promise(resolve => setTimeout(resolve, 2000));
            finalReviewText = SAMPLE_CODES[selectedPreset].review;
        } else {
            // Real API Call to Flask Python Backend /api/review
            const response = await fetch("/api/review", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ code: code })
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || "백엔드 분석 중 오류가 발생했습니다.");
            }
            finalReviewText = result.review;
        }

        clearInterval(stepInterval);
        overlay.classList.add("hidden");

        displayReviewResult(finalReviewText);
        
        if (finalReviewText.includes("| ⚠️ **주의 버그 (Bug/Security)** | 0개")) {
            triggerConfetti();
        }

    } catch (error) {
        clearInterval(stepInterval);
        overlay.classList.add("hidden");
        console.error(error);
        alert("리뷰 작성 중 에러가 발생했습니다: " + error.message);
    }
}

// Display & Format Markdown with visual line diff highlighting
function displayReviewResult(markdownText) {
    let rawHtml = marked.parse(markdownText);
    
    const tempContainer = document.createElement("div");
    tempContainer.innerHTML = rawHtml;
    
    const paragraphs = tempContainer.querySelectorAll("p");
    let cautionPreElements = [];
    
    paragraphs.forEach(p => {
        const text = p.innerText || "";
        if (text.includes("⚠️ 기존 코드")) {
            let nextPre = p.nextElementSibling;
            while (nextPre && nextPre.tagName !== "PRE") {
                nextPre = nextPre.nextElementSibling;
            }
            if (nextPre) {
                nextPre.classList.add("caution-codeblock");
                cautionPreElements.push(nextPre);
            }
        } else if (text.includes("💡 개선 코드")) {
            let nextPre = p.nextElementSibling;
            while (nextPre && nextPre.tagName !== "PRE") {
                nextPre = nextPre.nextElementSibling;
            }
            if (nextPre) {
                nextPre.classList.add("improvement-codeblock");
            }
        }
    });

    const outputEl = document.getElementById("markdown-output");
    outputEl.innerHTML = tempContainer.innerHTML;
    
    Prism.highlightAllUnder(outputEl);

    // Perform Line-by-Line diff highlighting
    cautionPreElements.forEach(cautionPre => {
        let improvementPre = cautionPre.nextElementSibling;
        while (improvementPre && !improvementPre.classList.contains("improvement-codeblock")) {
            improvementPre = improvementPre.nextElementSibling;
        }

        if (improvementPre) {
            const cautionCodeEl = cautionPre.querySelector("code");
            const improvementCodeEl = improvementPre.querySelector("code");

            if (cautionCodeEl && improvementCodeEl) {
                const rawOldCode = cautionCodeEl.innerText;
                const rawNewCode = improvementCodeEl.innerText;

                const diffLines = Diff.diffLines(rawOldCode, rawNewCode);
                
                let oldLineFlags = [];
                let newLineFlags = [];

                diffLines.forEach(part => {
                    const lines = part.value.split("\n");
                    if (lines[lines.length - 1] === "") lines.pop();

                    if (part.removed) {
                        lines.forEach(() => oldLineFlags.push(true));
                    } else if (part.added) {
                        lines.forEach(() => newLineFlags.push(true));
                    } else {
                        lines.forEach(() => {
                            oldLineFlags.push(false);
                            newLineFlags.push(false);
                        });
                    }
                });

                // Wrap Prism HTML strings with line highlighters
                const oldHtmlLines = cautionCodeEl.innerHTML.split("\n");
                const highlightedOldHtml = oldHtmlLines.map((line, idx) => {
                    if (oldLineFlags[idx]) {
                        return `<span class="diff-line-removed">${line}</span>`;
                    }
                    return line;
                }).join("\n");
                cautionCodeEl.innerHTML = highlightedOldHtml;

                const newHtmlLines = improvementCodeEl.innerHTML.split("\n");
                const highlightedNewHtml = newHtmlLines.map((line, idx) => {
                    if (newLineFlags[idx]) {
                        return `<span class="diff-line-added">${line}</span>`;
                    }
                    return line;
                }).join("\n");
                improvementCodeEl.innerHTML = highlightedNewHtml;
            }
        }
    });

    switchTab('report-view');
}

// Save active report to Flask Server SQLite database
async function saveReportToHistory() {
    const htmlContent = document.getElementById("markdown-output").innerHTML;
    if (!htmlContent || htmlContent.trim() === "") {
        alert("이력에 저장할 분석 결과가 없습니다!");
        return;
    }

    const tableEl = document.querySelector("#markdown-output table");
    let bugCount = "?";
    let improvementCount = "?";
    
    if (tableEl) {
        const cells = tableEl.querySelectorAll("td");
        if (cells.length >= 4) {
            bugCount = cells[1].innerText;
            improvementCount = cells[3].innerText;
        }
    }

    const payload = {
        date: new Date().toLocaleString("ko-KR"),
        bugs: bugCount,
        improvements: improvementCount,
        htmlContent: htmlContent
    };

    try {
        const response = await fetch("/api/history", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("백엔드 데이터베이스 저장 실패");
        const result = await response.json();
        
        if (result.status === "success") {
            alert("SQLite 데이터베이스에 리뷰 결과가 영구 저장되었습니다!");
            loadHistoryFromServer();
        }
    } catch (error) {
        alert("이력 저장 실패: " + error.message);
    }
}

// Render History items fetched from server SQLite DB
function renderHistory() {
    const container = document.getElementById("history-list");
    if (reviewHistory.length === 0) {
        container.innerHTML = `
            <div class="text-center py-20 text-slate-400">
                <i data-lucide="archive" class="w-12 h-12 mx-auto mb-4 stroke-1"></i>
                <p>저장된 이전 코드 리뷰 기록이 없습니다.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = reviewHistory.map(item => `
        <div class="glass-card p-5 flex items-center justify-between border-slate-200/60 hover:border-slate-300/80 transition-all duration-300">
            <div class="space-y-1">
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-brand-600 font-semibold font-mono">${item.date}</span>
                </div>
                <div class="flex items-center space-x-4 mt-2">
                    <span class="text-xs px-2.5 py-0.5 bg-red-500/10 border border-red-500/20 text-red-600 rounded-full font-medium">
                        ⚠️ 버그: ${item.bugs}
                    </span>
                    <span class="text-xs px-2.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-full font-medium">
                        💡 개선: ${item.improvements}
                    </span>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <button onclick="loadHistoryItem(${item.id})" class="px-4 py-2 bg-brand-500/10 border border-brand-500/20 hover:bg-brand-600 text-brand-600 hover:text-white rounded-lg text-xs font-semibold transition-all duration-300">
                    리포트 보기
                </button>
                <button onclick="deleteHistoryItem(${item.id})" class="p-2 border border-slate-200 text-slate-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all duration-300">
                    <i data-lucide="x" class="w-3.5 h-3.5"></i>
                </button>
            </div>
        </div>
    `).join("");

    lucide.createIcons();
}

function loadHistoryItem(id) {
    const item = reviewHistory.find(h => h.id === id);
    if (item) {
        const outputEl = document.getElementById("markdown-output");
        outputEl.innerHTML = item.htmlContent;
        switchTab('report-view');
    }
}

// Delete item from SQLite DB via Flask API
async function deleteHistoryItem(id) {
    if (confirm("이 리뷰 기록을 삭제하시겠습니까?")) {
        try {
            const response = await fetch(`/api/history/${id}`, {
                method: "DELETE"
            });
            if (!response.ok) throw new Error("삭제 작업 백엔드 오류");
            const result = await response.json();
            
            if (result.status === "success") {
                loadHistoryFromServer();
            }
        } catch (error) {
            alert("기록 삭제 오류: " + error.message);
        }
    }
}

// Clear all logs in SQLite via Flask API
async function clearHistory() {
    if (confirm("정말로 모든 리뷰 이력을 삭제하시겠습니까? (SQLite DB 복구 불가)")) {
        try {
            const response = await fetch("/api/history", {
                method: "DELETE"
            });
            if (!response.ok) throw new Error("전체 삭제 작업 백엔드 오류");
            const result = await response.json();
            
            if (result.status === "success") {
                loadHistoryFromServer();
            }
        } catch (error) {
            alert("전체 이력 삭제 실패: " + error.message);
        }
    }
}

function copyFullReport() {
    const text = document.getElementById("markdown-output").innerText;
    if (!text || text.trim() === "") {
        alert("복사할 내용이 없습니다!");
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        alert("클립보드에 리뷰 리포트가 복사되었습니다!");
    }).catch(err => {
        alert("복사 중 에러가 발생했습니다: " + err);
    });
}


function triggerConfetti() {
    const duration = 2 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
        confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
}
