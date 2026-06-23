from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
import os
from src.config import get_llm
from src.state import AnalystState
from src.tools import (
    web_search,
    get_stock_history,
    get_company_info,
    get_company_financials,
    get_weather,
    scrape_url,
    search_kaggle_datasets,
    download_kaggle_dataset
)

# Pydantic model for the collector to decide on the next tool execution
class CollectorDecision(BaseModel):
    tool_name: Literal[
        "web_search", 
        "get_stock_history", 
        "get_company_info", 
        "get_company_financials", 
        "get_weather", 
        "scrape_url", 
        "search_kaggle_datasets", 
        "download_kaggle_dataset",
        "DONE"
    ] = Field(description="Name of the tool to run, or 'DONE' if all necessary data has been collected.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments for the tool. Empty dict if DONE. E.g. {'query': 'Tokyo GDP 2026'} or {'ticker': 'MSFT', 'period': '3mo'} or {'location': 'London'}."
    )
    reasoning: str = Field(description="Explanation of why this tool call or DONE is selected.")

def extract_location_from_query(query: str, llm) -> str:
    prompt = f"""Given the user query: "{query}"
Identify and extract the primary city or location name mentioned for weather lookup.
Return ONLY the name of the city (e.g., "London", "Tokyo", "New York"). If no specific location is mentioned or it is generic, return "New York" as a default.
Do not include any other text, quotes, or punctuation."""
    try:
        response = llm.invoke(prompt)
        loc = response.content.strip().replace('"', '').replace("'", "")
        if loc:
            return loc
    except Exception:
        pass
    return "New York"

def extract_ticker_from_query(query: str, llm) -> str:
    prompt = f"""Given the user query: "{query}"
Identify and extract the primary stock ticker or company name mentioned.
Return ONLY the ticker symbol in uppercase (e.g., "AAPL", "NVDA", "MSFT"). If no stock is mentioned, return "SPY" as a default.
Do not include any other text, quotes, or punctuation."""
    try:
        response = llm.invoke(prompt)
        ticker = response.content.strip().replace('"', '').replace("'", "")
        if ticker:
            return ticker
    except Exception:
        pass
    return "SPY"

def extract_json(text: str) -> str:
    text = text.strip()
    if "```json" in text:
        try:
            return text.split("```json")[1].split("```")[0].strip()
        except IndexError:
            pass
    elif "```" in text:
        try:
            return text.split("```")[1].split("```")[0].strip()
        except IndexError:
            pass
            
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace+1]
        
    return text

def collector_node(state: AnalystState) -> dict:
    """
    An autonomous collection agent that loops, executing tools sequentially, 
    until it decides it has gathered all the necessary data.
    """
    llm = get_llm(temperature=0.1)
    
    # Store tools mapping
    tools_map = {
        "web_search": web_search,
        "get_stock_history": get_stock_history,
        "get_company_info": get_company_info,
        "get_company_financials": get_company_financials,
        "get_weather": get_weather,
        "scrape_url": scrape_url,
        "search_kaggle_datasets": search_kaggle_datasets,
        "download_kaggle_dataset": download_kaggle_dataset,
    }
    
    collected = dict(state.get("collected_data", {}))
    history = [] # Tracks the collector loop steps for the prompt context
    errors = list(state.get("errors", []))
    
    max_iterations = 5
    for i in range(max_iterations):
        print(f"[*] Collector loop iteration {i+1}/{max_iterations}")
        
        # Build prompt showing the plan, current collected items and history of operations
        history_str = "\n".join([
            f"Step {idx+1}: Called {h['tool']} with {h['args']}\nResult Summary: {h['result'][:250]}..."
            for idx, h in enumerate(history)
        ]) if history else "None"
        
        prompt = f"""You are an Autonomous Data Collector Agent.
Today's date is: {state['current_date']}.

User Query: "{state['query']}"
Analysis Plan:
{chr(10).join(f' - {step}' for step in state['plan'])}

Available Tools & Signature:
- `web_search(query: str)`: Searches Google/web.
- `get_stock_history(ticker: str, period: str = '1mo')`: Downloads stock price CSV.
- `get_company_info(ticker: str)`: Gets company financial profile (P/E ratio, market cap).
- `get_company_financials(ticker: str)`: Gets recent income/balance/cash flow statements.
- `get_weather(location: str)`: Fetches weather data for a city.
- `scrape_url(url: str)`: Reads full text page of any web link.
- `search_kaggle_datasets(query: str)`: Searches for CSV files on Kaggle.
- `download_kaggle_dataset(dataset_id: str)`: Downloads dataset files.

Already Gathered Data Summary:
{list(collected.keys())}

Action History:
{history_str}

Decide:
What is the next tool to run to gather data for the plan? 
If you have collected enough info to answer the query, perform cleaning, analysis and plotting, output 'DONE'.
"""
        
        # Structured LLM invocation
        try:
            structured_llm = llm.with_structured_output(CollectorDecision)
            decision = structured_llm.invoke(prompt)
        except Exception as e:
            print(f"[Warning] Collector structured output failed ({e}). Falling back to JSON parsing.")
            # Fallback text reasoning + manual parser
            fallback_prompt = prompt + "\nRespond in JSON format matching the schema: {'tool_name': '...', 'arguments': {...}, 'reasoning': '...'}. Do not add markdown boxes."
            response = llm.invoke(fallback_prompt)
            content = extract_json(response.content)
            try:
                import json
                data = json.loads(content)
                decision = CollectorDecision(
                    tool_name=data.get("tool_name", "DONE"),
                    arguments=data.get("arguments", {}),
                    reasoning=data.get("reasoning", "Parsed fallback")
                )
            except Exception:
                # Absolute fallback
                decision = CollectorDecision(tool_name="DONE", arguments={}, reasoning="Fallback parsing failed")

        print(f"    Reasoning: {decision.reasoning}")
        if decision.tool_name == "DONE":
            print("    Decision: Collection complete.")
            break
            
        tool_name = decision.tool_name
        args = decision.arguments
        
        if tool_name not in tools_map:
            print(f"    Error: Selected invalid tool name '{tool_name}'")
            continue
            
        # Execute tool
        print(f"    Executing tool: {tool_name} with args {args}")
        try:
            tool_fn = tools_map[tool_name]
            
            # Auto-resolve missing or generic parameters
            if tool_name == "get_weather":
                location = args.get("location")
                if not location or str(location).strip().lower() in ["", "the location", "location", "none"]:
                    extracted = extract_location_from_query(state["query"], llm)
                    args["location"] = extracted
                    print(f"    [Resolved Location] Auto-extracted location '{extracted}' from query")
            elif tool_name in ["get_stock_history", "get_company_info", "get_company_financials"]:
                ticker = args.get("ticker")
                if not ticker or str(ticker).strip().lower() in ["", "the stock", "stock", "ticker", "none", "company"]:
                    extracted = extract_ticker_from_query(state["query"], llm)
                    args["ticker"] = extracted
                    print(f"    [Resolved Ticker] Auto-extracted ticker '{extracted}' from query")
                    
            result = tool_fn(**args)
            
            # Store in collected dataset state
            data_key = f"{tool_name}_{len(history)}"
            collected[data_key] = {
                "args": args,
                "result": result
            }
            
            history.append({
                "tool": tool_name,
                "args": args,
                "result": result
            })
        except Exception as e:
            err_msg = f"Failed to execute {tool_name} with {args}: {e}"
            print(f"    Error: {err_msg}")
            errors.append(err_msg)
            history.append({
                "tool": tool_name,
                "args": args,
                "result": f"Error: {e}"
            })
            
    return {
        "collected_data": collected,
        "errors": errors
    }
