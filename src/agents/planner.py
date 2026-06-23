from pydantic import BaseModel, Field
from typing import List
from src.config import get_llm
from src.state import AnalystState

class AnalystPlan(BaseModel):
    steps: List[str] = Field(description="Step-by-step actions for data gathering, cleaning, analysis, and plotting.")

def planner_node(state: AnalystState) -> dict:
    """
    Analyzes the user's query and constructs a detailed, step-by-step plan for gathering 
    data and executing the required data analysis.
    """
    llm = get_llm(temperature=0.1)
    
    prompt = f"""You are a Lead Data Analyst Planner.
Today's date is: {state['current_date']}.

User Query:
"{state['query']}"

Based on the query, formulate a step-by-step analysis plan. 
Determine:
1. What external data we need to retrieve (e.g. stock prices using yfinance, local weather, news via web search, specific Kaggle datasets, or web scraping).
2. What specific metrics, trends, correlations, or anomalies we should analyze.
3. What charts/plots (e.g., lines, bars, heatmaps) will represent the data best.

Your response should detail a clear execution roadmap.
"""
    
    # Try structured output first, with standard parsing fallback
    try:
        structured_llm = llm.with_structured_output(AnalystPlan)
        plan_obj = structured_llm.invoke(prompt)
        steps = plan_obj.steps
    except Exception as e:
        print(f"[Warning] Planner structured output failed ({e}). Falling back to raw text parsing.")
        fallback_prompt = prompt + "\nProvide your answer in raw JSON with a single key 'steps' which contains an array of strings. Do not include markdown formatting other than raw JSON."
        response = llm.invoke(fallback_prompt)
        content = response.content.strip()
        # strip markdown blocks if model returns them
        if content.startswith("```json"):
            content = content.replace("```json", "", 1)
        if content.endswith("```"):
            content = content[:-3]
        try:
            import json
            data = json.loads(content.strip())
            steps = data.get("steps", [content])
        except Exception:
            steps = [s.strip() for s in content.split("\n") if s.strip()]
            
    print(f"[*] Planner formulated plan:\n" + "\n".join(f" - {s}" for s in steps))
    return {"plan": steps}
