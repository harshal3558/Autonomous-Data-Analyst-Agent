import os
import sys
import pandas as pd
from src.graph import create_agent_graph
import src.config as config

# Define Evaluation Benchmark Test Cases
BENCHMARK_CASES = [
    {
        "id": 1,
        "name": "Financial Analytics Case",
        "query": "Compare NVIDIA (NVDA) and Apple (AAPL) stock performance for the last 30 days. Calculate volatility, trace daily correlation, and plot the trends.",
        "expected_data": "get_stock_history"
    },
    {
        "id": 2,
        "name": "Local Climate Analytics Case",
        "query": "What is the weather trend in Tokyo today (Jun 21, 2026)? Fetch current details and check if there's any correlation with retail indices (mock retail data if needed) and plot it.",
        "expected_data": "get_weather"
    },
    {
        "id": 3,
        "name": "General Market/News Case",
        "query": "Search for the latest artificial intelligence news today on Jun 21, 2026. Compile the key takeaways and summarize the trend visually with a mock sentiment bar chart.",
        "expected_data": "web_search"
    }
]

def run_evaluation_suite():
    print("="*70)
    print("            AUTONOMOUS AGENT EVALUATION BENCHMARK SUITE")
    print("="*70)
    
    # 1. Verify API configuration
    if not config.GEMINI_API_KEY and not config.GROQ_API_KEY:
        print("[ERROR] No LLM API keys detected in your environment.")
        print("Please set GROQ_API_KEY in .env and configure it before running evaluations.")
        sys.exit(1)
        
    # 2. Compile LangGraph workflow
    try:
        graph = create_agent_graph()
    except Exception as e:
        print(f"[ERROR] Failed to compile LangGraph workflow: {e}")
        sys.exit(1)
        
    scores = []
    
    # 3. Iterate over test cases
    for case in BENCHMARK_CASES:
        print(f"\n[Case {case['id']}] Running: {case['name']}")
        print(f"Query: \"{case['query']}\"")
        
        # Clear output folder prior to run
        if os.path.exists(config.OUTPUT_DIR):
            for file in os.listdir(config.OUTPUT_DIR):
                try:
                    os.remove(os.path.join(config.OUTPUT_DIR, file))
                except Exception:
                    pass
                    
        # Set start state
        initial_state = {
            "query": case["query"],
            "current_date": "June 21, 2026",
            "plan": [],
            "collected_data": {},
            "execution_logs": [],
            "charts": [],
            "findings": "",
            "final_report": "",
            "errors": []
        }
        
        # Run agent
        try:
            final_state = graph.invoke(initial_state)
            
            # 4. Score metrics
            has_plan = len(final_state.get("plan", [])) > 0
            has_collected = len(final_state.get("collected_data", {})) > 0
            
            # Check execution logs for successful sandbox runs
            exec_logs = final_state.get("execution_logs", [])
            has_code_ran = len(exec_logs) > 0
            code_exec_success = any(log.get("success") for log in exec_logs) if exec_logs else False
            
            # Visual charts count
            charts = final_state.get("charts", [])
            has_charts = len(charts) > 0
            
            # Report structural checks
            report = final_state.get("final_report", "")
            has_report = len(report) > 0
            has_exec_summary = "executive summary" in report.lower()
            has_findings = "findings" in report.lower() or "key findings" in report.lower()
            has_patterns = "pattern" in report.lower() or "hidden patterns" in report.lower()
            has_suggestions = "suggestion" in report.lower() or "actionable suggestions" in report.lower()
            
            # Scorecard mapping
            case_scores = {
                "Case Name": case["name"],
                "Planning Metric (Pass/Fail)": "PASS" if has_plan else "FAIL",
                "Data Collection (Pass/Fail)": "PASS" if has_collected else "FAIL",
                "Sandbox Code Success (Pass/Fail)": "PASS" if code_exec_success else "FAIL",
                "Charts Created": f"PASS ({len(charts)} charts)" if has_charts else "FAIL",
                "Report Quality Score (0-4)": sum([has_exec_summary, has_findings, has_patterns, has_suggestions]),
                "Execution Status": "SUCCESS" if not final_state.get("errors") else "WARNING/ERRORS"
            }
            scores.append(case_scores)
            
            print(f"--> Done. Result: {case_scores['Execution Status']}. Report Quality Score: {case_scores['Report Quality Score (0-4)']}/4")
            
        except Exception as e:
            print(f"--> [FAILED] Execution crashed: {e}")
            scores.append({
                "Case Name": case["name"],
                "Planning Metric (Pass/Fail)": "FAIL",
                "Data Collection (Pass/Fail)": "FAIL",
                "Sandbox Code Success (Pass/Fail)": "FAIL",
                "Charts Created": "FAIL",
                "Report Quality Score (0-4)": 0,
                "Execution Status": f"CRASHED: {str(e)[:50]}"
            })
            
    # 5. Output Summary Scorecard
    print("\n" + "="*80)
    print("                      EVALUATION SCORECARD SUMMARY")
    print("="*80)
    df_scores = pd.DataFrame(scores)
    print(df_scores.to_string(index=False))
    print("="*80)
    
    # Save score results in outputs
    report_filepath = os.path.join(config.OUTPUT_DIR, "eval_benchmark_results.csv")
    df_scores.to_csv(report_filepath, index=False)
    print(f"Saved evaluation scorecard dataset to: {report_filepath}\n")

if __name__ == "__main__":
    run_evaluation_suite()
