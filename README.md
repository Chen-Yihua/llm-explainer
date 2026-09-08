# LLM API Integration

本專案為 **L\*LM**（以大型語言模型回答主動自動機學習中的成員查詢與等價查詢，驅動 L\* 系列演算法收斂）方法之實作，並包含以此方法為基礎延伸的相關實驗。專案由兩部分構成：**Java** 模組負責 OpenAI／Gemini API 的客戶端呼叫，**Python** 模組則整合 AALpy 與 diss 函式庫，完成自動機學習與策略合成。

## 實驗總覽

| 實驗 | 位置 | 說明 |
|---|---|---|
| 機器人格子世界規則學習 | [python/experiments/robot_test_with_diss.py](python/experiments/robot_test_with_diss.py) | 主實驗，為 L\*LM 方法之核心示範：以 LLM 回答成員查詢與等價查詢，透過 aalpy 的 L\* 演算法學習出描述機器人格子世界規則的 DFA，並交由 `diss` 進行策略合成。已以模擬（mock）LLM 完整驗證執行流程 |
| Tomita grammar 學習 | [python/experiments/tomita_test.py](python/experiments/tomita_test.py) | 採用不同技術路線之實驗，改以 `lstar` 函式庫（而非 aalpy）驅動 L\*LM 學習，透過 `Client.py` 呼叫 OpenAI／Gemini 回應查詢。不涉及 `diss`（原檔名 `tomita_test_with_diss.py` 與實際內容不符，已更名）。已以模擬（mock）LLM 驗證 `test_tomita_1`、`test_tomita_2` 皆可完整跑通 |
| Java 版 LLM API 呼叫測試 | [java/src/test/java/](java/src/test/java/) | `ChatGPTClientTest.java`、`GeminiClientTest.java`，用於驗證 OpenAI／Gemini API 呼叫本身，不涉及自動機學習流程 |

各實驗共用的基礎邏輯（LLM 客戶端、SUL／等價查詢 Oracle 之封裝、DFA 格式轉換工具等）統一置於 [python/lib/](python/lib/)，詳見下方「Usage」與「補充說明」。

---

## 目錄結構

```
.
├── Dockerfile               # 容器化執行環境設定
├── requirements.txt         # Python 套件相依清單
├── java/                    # Java（Maven）專案
│   ├── pom.xml
│   ├── credentials/         # Google Cloud 金鑰等機密檔案（已納入 .gitignore，需自行建立）
│   └── src/
│       ├── main/
│       │   ├── java/        # Java 主程式
│       │   └── resources/   # config.json（API 金鑰，Java／Python 共用）、logback.xml
│       └── test/
│           └── java/        # Java 測試（ChatGPTClientTest、GeminiClientTest 等）
├── python/                  # Python 自動機學習實驗
│   ├── experiments/         # 實驗入口（可直接執行之腳本）
│   ├── lib/                 # 共用模組（由實驗入口呼叫，不直接執行）
│   └── tests/               # Python 測試腳本
├── data/                    # LLM 生成之測試資料集（Positive／Negative examples）
├── cache/                   # 執行期間產生之快取（cache.pkl、diss shelve database，已納入 .gitignore）
├── log/                     # 各學習演算法之執行輸出紀錄（run_*.txt）
└── docs/                    # 專案文件（prompt 設計紀錄等）
```

---

## Requirements

**Java 環境**
1. JDK 23 或更新版本
2. Maven 3.9.9 或更新版本
3. IDE：建議使用 VS Code（安裝 Java 擴充套件）或 IntelliJ IDEA
4. HTTP 客戶端：OkHttp
5. JSON 處理：Gson

**Python 環境**
1. Python 3.10
2. 套件相依請參見 [requirements.txt](requirements.txt)（包含 aalpy、diss、dfa 等自動機學習相關函式庫）

亦可直接使用 [Dockerfile](Dockerfile) 建置容器化執行環境。

---

## Usage

### 步驟 1：取得專案原始碼

```bash
git clone https://github.com/Chen-Yihua/llm-api-integration.git
cd llm-api-integration
```

### 步驟 2：設定憑證與 API 金鑰

於 `java/` 目錄下建立 `credentials/` 資料夾，並置入所需之 Google Cloud 金鑰檔案。

`java/src/main/resources/config.json` 為 Java 與 Python 共用之設定檔，內容須包含正確的 API 金鑰，格式如下：

```json
{
  "OPENAI_API_KEY": "sk-xxxxxx",
  "GEMINI_API_KEY": "AI-xxxxxx"
}
```

### 步驟 3：建置與執行（Java）

以 Maven 安裝專案相依套件：

```bash
cd java
mvn clean install
```

於 IDE 中重新載入專案：
- VS Code：於專案目錄中找到 `pom.xml`，點選右鍵並選擇 Reload Project
- IntelliJ IDEA：於 Maven 工具視窗點選 Reload All Maven Projects

執行主程式（如 `ChatGPTClientTest.java`、`GeminiClientTest.java`）時，**須以專案根目錄作為工作目錄**，因程式碼中採用相對於根目錄之路徑（例如 `java/src/main/resources/config.json`）。

### 步驟 4：建置與執行（Python）

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

執行 Python 腳本時，**同樣須以專案根目錄作為工作目錄**（`data/`、`cache/`、`java/src/main/resources/config.json` 皆為相對於根目錄之路徑）。可執行之實驗入口統一置於 `python/experiments/`，例如：

```bash
python python/experiments/robot_test_with_diss.py
```

`python/lib/` 內為各實驗入口所依賴之共用模組，依職責劃分如下：

| 模組 | 職責 |
|---|---|
| `Client.py` | OpenAI／Gemini API 客戶端 |
| `automaton_learning.py` | LLM 驅動之自動機學習核心邏輯（`LLMAutomatonSUL`、`ChatGPTEqOracle`、`robot.learning`，三者於流程中緊密協作，故合併於同一模組） |
| `dfa_utils.py` | DFA 建構與格式轉換工具函式（`aalpy_dfa_to_dict`、`get_target_dfa` 等） |
| `create_test_dataset.py` | 測試資料集之產生與讀寫 |
| `tee.py` | 同步輸出至終端機與檔案之工具類別 |

上述模組僅供程式內部呼叫，不作為獨立執行進入點。

亦可直接以 Docker 執行：

```bash
docker build -t llm-api-integration .
docker run --rm llm-api-integration
```

---

## 補充說明

- `log/` 目錄下之檔案為各學習演算法（L*、KV、Alergia、PAPNI 等）之執行輸出紀錄，供結果比對之用。
- `cache/` 與 `data/` 之內容於執行期間由程式讀寫；`cache/` 已納入 `.gitignore`，不受版本控制。
- `docs/備註.txt` 記錄產生測試資料時所使用之完整 LLM prompt。
- `automaton_learning.py` 中之 `robot` class 係由 `robot_test_with_diss.py` 以函式庫方式呼叫（`automaton_learning.robot.learning(client, params, mq_prompt, alphabet, automaton_type, sul, eq_oracle)`），不支援獨立執行。
- `dfa_utils.py` 中之 `learn_dfa_from_examples`、`extend_dfa_with_examples`、`get_target_dfa` 目前未被任何實驗入口呼叫，屬尚未整合之範例／備用程式碼。
