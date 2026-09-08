# LLM API Integration

結合 **Java**（OpenAI / Gemini API 客戶端）與 **Python**（AALpy / diss 自動機學習實驗）的專案：
用 LLM 回答成員查詢（membership query）與等價查詢（equivalence query），學習出描述系統行為的 DFA / VPA / 機器人格子世界策略。

Java 與 Python 各自獨立成頂層資料夾，彼此不互相巢狀。

---

## 目錄結構

```
.
├── Dockerfile               # 打包整個專案的執行環境
├── requirements.txt         # Python 套件需求
├── java/                    # Java（Maven）專案
│   ├── pom.xml
│   ├── credentials/         # Google Cloud 金鑰等機密檔案（已加入 .gitignore，需自行建立）
│   └── src/
│       ├── main/
│       │   ├── java/        # Java 主程式
│       │   └── resources/   # config.json（API 金鑰，Java/Python 共用）、logback.xml
│       └── test/
│           └── java/        # Java 測試（ChatGPTClientTest、GeminiClientTest...）
├── python/                  # Python 自動機學習實驗
│   ├── experiments/         # 實驗入口（直接執行的腳本）
│   ├── lib/                 # 共用方法／模組（被實驗入口呼叫，不直接執行）
│   └── tests/               # Python 測試腳本
├── data/                    # LLM 生成的測試資料（Positive/Negative examples）
├── cache/                   # 執行期產生的快取（cache.pkl、diss shelve DB，已加入 .gitignore）
├── log/                     # 各學習演算法的執行輸出紀錄（run_*.txt）
└── docs/                    # 專案筆記（prompt 設計等）
```

---

## Requirements

**Java 端**
1. JDK 23 或更新版本
2. Maven 3.9.9 或更新版本
3. IDE：建議使用 VS Code（需安裝 Java 擴充套件）或 IntelliJ IDEA
4. HTTP 客戶端庫：OkHttp
5. JSON 處理：Gson

**Python 端**
1. Python 3.10
2. 套件需求見 [requirements.txt](requirements.txt)（含 aalpy、diss、dfa 等自動機學習相關套件）

也可以直接使用 [Dockerfile](Dockerfile) 建置好的容器環境。

---

## Usage

### 步驟 1：複製專案

```bash
git clone https://github.com/Chen-Yihua/llm-api-integration.git
cd llm-api-integration
```

### 步驟 2：設定環境

在 `java/` 資料夾中新增一個 `credentials/` 資料夾，並放入所需的 Google Cloud 金鑰檔案。

確保 `java/src/main/resources/config.json` 的內容包含正確的 API 金鑰（Java 和 Python 共用同一份設定），例如：

```json
{
  "OPENAI_API_KEY": "sk-xxxxxx",
  "GEMINI_API_KEY": "AI-xxxxxx"
}
```

### 步驟 3：建置與執行（Java）

使用 Maven 安裝專案依賴：

```bash
cd java
mvn clean install
```

在 IDE 中重新載入專案：
- VSCode：在專案目錄中找到 `pom.xml` 文件 > 右鍵選擇 Reload Project
- IntelliJ IDEA：點擊 Maven 工具窗口的 Reload All Maven Projects

**請在專案根目錄下**用 IDE 或命令列運行主程式（測試檔內用的是相對於根目錄的路徑，例如 `java/src/main/resources/config.json`），例如 `ChatGPTClientTest.java` 或 `GeminiClientTest.java`。

### 步驟 4：安裝並執行 Python 環境

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**請在專案根目錄下執行 Python 腳本**（`data/`、`cache/`、`java/src/main/resources/config.json` 皆為相對於根目錄的路徑）。實際可執行的實驗入口在 `python/experiments/`，例如：

```bash
python python/experiments/robot_test_with_diss.py
```

`python/lib/` 底下都是被實驗入口呼叫的共用模組，依性質分成幾個檔案：
- `Client.py` — OpenAI / Gemini API 客戶端
- `automaton_learning.py` — LLM 驅動的自動機學習機制（`LLMAutomatonSUL`、`ChatGPTEqOracle`、`robot.learning` 三者緊密搭配使用，合併在同一檔案）
- `dfa_utils.py` — DFA 建構／格式轉換的工具函式（`aalpy_dfa_to_dict`、`get_target_dfa` 等）
- `create_test_dataset.py` — 測試資料集的產生與讀寫
- `tee.py` — 同時輸出到終端機與檔案的小工具

這些都不是用來直接執行的。

或直接使用 Docker：

```bash
docker build -t llm-api-integration .
docker run --rm llm-api-integration
```

---

## 其他說明

- `log/` 內的檔案是各次自動機學習演算法（L*、KV、Alergia、PAPNI...）的執行輸出，方便比對結果。
- `cache/` 與 `data/` 中的內容會在執行過程中被程式讀寫，`cache/` 已加入 `.gitignore` 不會被版本控制。
- `docs/備註.txt` 記錄了生成測試資料時使用的完整 LLM prompt。
- `automaton_learning.py` 裡的 `robot` class 是被 `robot_test_with_diss.py` 當函式庫呼叫的（`automaton_learning.robot.learning(client, params, mq_prompt, alphabet, automaton_type, sul, eq_oracle)`），不能單獨執行。
- `dfa_utils.py` 裡的 `learn_dfa_from_examples`、`extend_dfa_with_examples`、`get_target_dfa` 目前沒有任何實驗入口在使用，是尚未串接的範例／備用程式碼。
- `python/experiments/tomita_test_with_diss.py` 是另一組實驗，走的是不同的技術路線（`lstar`／`lstar_llm` 套件、打本機的 `http://127.0.0.1:8080/completion`），不是 `robot_test_with_diss.py` 那條 aalpy + diss + OpenAI/Gemini 的主線，需要另外跑一個本機的 completion server 才能用。

## 已知問題

- **`venv/` 是搬移過來的虛擬環境**：`pyvenv.cfg` 一度殘留建立時的舊路徑，`venv/bin/python3` symlink 也曾經失效導致整個 Python 環境無法執行，目前已修正為指向本機的 `/home/user/miniconda3/bin/python3.10`（版本相符）。如果之後又把整個專案搬到別的路徑／機器，**建議直接刪掉 `venv/` 重新用 `requirements.txt` 建立**，不要沿用搬移後的 venv，才不會又踩到同樣的 symlink 失效問題。
- **`pip check` 顯示版本衝突但目前可正常運行**：`diss`、`dfa-identify`、`lazytree`、`lstar`、`py-aiger-bdd/bv/dfa` 都宣告需要 `attrs<23.0`，但目前裝的是 `attrs 25.3.0`；`py-aiger-bdd/bv/dfa/gridworld/ptltl` 都宣告需要 `py-aiger<7.0.0`，但目前裝的是 `py-aiger 7.0.0`。實測跑過完整的機器人格子世界學習流程沒有出錯，暫時保留現況、未強制降版本，但如果之後遇到難以解釋的行為，這是優先排查的方向。
