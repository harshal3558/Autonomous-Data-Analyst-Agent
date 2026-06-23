# Autonomous Data Analyst Agent

An autonomous, multi-agent Data Analyst workflow built with Python, **LangGraph**, and **LangChain**. The system takes a user analysis request, reasons about data requirements, dynamically queries APIs (news, weather, yfinance, Kaggle, scraping), executes safe statistical calculations and Matplotlib plotting in a secured Python sandbox, detects anomalies/patterns, and compiles a comprehensive Markdown report.

A sleek, premium **Streamlit Web Dashboard** is provided to run queries, visualize graphs, preview downloaded datasets, and trace multi-agent execution step-by-step.

---

## 🛠️ Project Architecture

```
Autonomous-Data-Analyst-Agent/
├── .env.template               # Template for API keys
├── requirements.txt            # Project dependencies
├── Dockerfile                  # Containerization specification
├── main.py                     # CLI Entry point
├── app.py                      # Streamlit UI Dashboard
│
├── src/
│   ├── config.py               # Environment and LLM initialization
│   ├── state.py                # LangGraph State context
│   ├── graph.py                # Graph compilation
│   │
│   ├── agents/                 # Agent Nodes (Planner, Collector, Analyst, Reporter)
│   └── tools/                  # Integration tools (Search, Finance, Weather, Scraper, Kaggle, Sandbox)
│
├── output/                     # Generated charts, datasets, and markdown reports
├── verify_sandbox.py           # Automated test script for sandbox execution and guardrails
└── run_evals.py                # End-to-end benchmark evaluation suite
```

---

## 🛡️ Sandbox Security Guardrails

To prevent harmful operations from dynamically generated LLM code, our execution sandbox ([src/tools/sandbox.py](src/tools/sandbox.py)) passes all scripts through an **Abstract Syntax Tree (AST)** validator before running them:
* **Blocked Modules**: `os`, `sys`, `subprocess`, `shutil`, `socket`, `urllib`, `requests`, `builtins`, `ctypes`, `threading`, `multiprocessing`, `importlib`.
* **Blocked Built-ins**: `eval`, `exec`, `open`, `compile`, `getattr`, `setattr`, `delattr`, `globals`, `locals`.
* **Safe Utilities**: Direct access to `os` is blocked. A pre-loaded `path_join` function (aliasing `os.path.join`) is passed to the execution namespace so the analyst can join paths safely.

---

## 📊 Evaluation Framework (Evals)

You can benchmark the agent using the automated evaluation suite ([run_evals.py](run_evals.py)). It runs three benchmark queries and scores the outputs on a 0-5 criteria checklist:
1. **Planning**: Did the planner generate a valid roadmap?
2. **Collection**: Did the collector gather API / Search files?
3. **Execution**: Did the analyst script run in the sandbox successfully?
4. **Visuals**: Did the sandbox generate data plots?
5. **Report Quality (0-4)**: Check for key report sections (Summary, Findings, Patterns, Suggestions).

To run evaluations:
```bash
python run_evals.py
```
This prints the scorecard and saves the details to `output/eval_benchmark_results.csv`.

---

## 🚀 Setup & Installation

### 1. Configure API Keys
Copy the template to create a `.env` file:
```bash
cp .env.template .env
```
Open `.env` and fill in your keys (minimally, set `GEMINI_API_KEY`).

### 2. Run Locally
Install Python dependencies:
```bash
pip install -r requirements.txt
```

* **Launch Streamlit Dashboard**:
  ```bash
  streamlit run app.py
  ```
  Open `http://localhost:8501` to use the interactive interface.
* **Run CLI Interface**:
  ```bash
  python main.py --query "Compare NVIDIA (NVDA) and Apple (AAPL) stock performance for the last 30 days."
  ```

### 3. Run with Docker (Recommended for Safety)
You can run the agent inside an isolated Docker container:

* **Build the Docker Image**:
  ```bash
  docker build -t data-analyst-agent .
  ```
* **Run the Container**:
  ```bash
  docker run -d -p 8501:8501 --env-file .env data-analyst-agent
  ```
  Open `http://localhost:8501` in your browser.

---

## 🧪 Testing Verification
To test execution and ensure that both standard plotting and security blocks function as expected:
```bash
python verify_sandbox.py
```
Outputs should report `[SUCCESS]` for both sandbox runs and security block checks.
