import os
from pydantic import BaseModel, Field
from src.config import get_llm, OUTPUT_DIR
from src.state import AnalystState
from src.tools import execute_python_code

class AnalystCode(BaseModel):
    python_code: str = Field(description="The complete self-contained Python script to execute. Do not include markdown code ticks (```) in this string.")
    explanation: str = Field(description="Short summary of the statistical analysis and charts this code generates.")

def analyst_node(state: AnalystState) -> dict:
    """
    Writes and runs Python data analysis code to process collected datasets, 
    compute indicators, and generate visualizations.
    If the code crashes, reads stderr and automatically attempts to debug and re-run.
    """
    llm = get_llm(temperature=0.1)
    
    # 1. Scan output directory to find actual files available for the pandas script
    available_files = []
    if os.path.exists(OUTPUT_DIR):
        available_files = [f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))]
        
    # 2. Extract text data summaries collected from APIs
    collected_summaries = []
    for k, v in state.get("collected_data", {}).items():
        # Exclude large raw outputs, just describe what was downloaded
        args = v.get("args", {})
        result_preview = str(v.get("result", ""))[:400]
        collected_summaries.append(f"- Data source: {k} (Args: {args})\n  Preview: {result_preview}...\n")
        
    collected_summary_str = "\n".join(collected_summaries) if collected_summaries else "None"
    
    execution_history = list(state.get("execution_logs", []))
    charts = list(state.get("charts", []))
    errors = list(state.get("errors", []))
    
    max_retries = 3
    for attempt in range(max_retries):
        print(f"[*] Analyst code execution attempt {attempt+1}/{max_retries}")
        
        # Build prompt showing available data and any past errors to fix
        past_attempts_str = ""
        if execution_history:
            last_run = execution_history[-1]
            past_attempts_str = f"""
--- PREVIOUS RUN FAILED ---
Code executed:
```python
{last_run['code']}
```
Stdout: {last_run['stdout']}
Stderr/Error: {last_run['stderr']}

Analyze the error above, correct the code imports, filepath handling, index alignment, or formatting, and rewrite the script.
"""
            
        prompt = f"""You are a Senior Data Analyst.
Today's date is: {state['current_date']}.

User Query: "{state['query']}"
Analysis Plan:
{chr(10).join(f' - {step}' for step in state['plan'])}

Files in output directory (you can read these directly inside your script using `path_join(OUTPUT_DIR, "filename")`):
{available_files}

Summarized API Data Gathered:
{collected_summary_str}
{past_attempts_str}

Your task is to write a complete Python script to perform the data analysis.
Constraints & Requirements:
1. Clean the data (e.g. handle NaNs, parse datetimes, align indices).
2. Calculate key summary metrics (correlations, averages, variances, indicators, anomalies).
3. Print descriptive statistics and analytical results to stdout (using standard `print()` statements).
4. Generate charts using `matplotlib` or `seaborn`.
5. IMPORTANT: Call `plt.show()` or `plt.savefig()` to save the figures. The sandbox intercepts these and automatically saves them to the `output/` directory as `chart_*.png`.
6. Write self-contained, valid Python 3 code. Use the global variables pre-loaded: `pd` (pandas), `np` (numpy), `plt` (matplotlib.pyplot), `sns` (seaborn), `OUTPUT_DIR` (path to output folder), `path_join` (path-joining function).
7. SECURITY WARNING: Do not attempt to import or reference 'os', 'sys', 'subprocess', or other forbidden modules. Direct file writes or shell calls will trigger a sandbox security block.

Write the complete code:
"""
        
        # Invoke LLM for code generation
        try:
            structured_llm = llm.with_structured_output(AnalystCode)
            decision = structured_llm.invoke(prompt)
            code_to_run = decision.python_code
        except Exception as e:
            print(f"[Warning] Analyst structured output failed ({e}). Falling back to markdown parsing.")
            # Fallback markdown regex parser
            fallback_prompt = prompt + "\nWrite the python code inside a standard markdown code block: ```python ... ```."
            response = llm.invoke(fallback_prompt)
            content = response.content.strip()
            if "```python" in content:
                code_to_run = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code_to_run = content.split("```")[1].split("```")[0].strip()
            else:
                code_to_run = content
                
        print(f"    Running code in execution sandbox...")
        # Run code in sandbox
        result = execute_python_code(code_to_run)
        
        # Log this attempt
        log_entry = {
            "attempt": attempt + 1,
            "code": code_to_run,
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "charts": result["charts"]
        }
        execution_history.append(log_entry)
        
        if result["success"]:
            print(f"    Execution SUCCESS. Generated charts: {result['charts']}")
            print(f"    Stdout output:\n{result['stdout']}")
            charts.extend(result["charts"])
            break
        else:
            print(f"    Execution FAILED. Stderr:\n{result['stderr']}")
            if attempt == max_retries - 1:
                errors.append(f"Analyst script failed after {max_retries} attempts. Last error: {result['stderr']}")
                
    return {
        "execution_logs": execution_history,
        "charts": list(set(charts)), # remove duplicates
        "findings": execution_history[-1]["stdout"] if execution_history else "",
        "errors": errors
    }
