import os
from src.config import get_llm, OUTPUT_DIR
from src.state import AnalystState

def reporter_node(state: AnalystState) -> dict:
    """
    Compiles all gathered insights, statistical outputs, and visual charts into a 
    polished, professional Senior Data Analyst Markdown report.
    """
    llm = get_llm(temperature=0.2)
    
    # 1. Format the visual charts as markdown image links
    chart_markdown = ""
    if state.get("charts"):
        chart_markdown = "### Visual Charts Generated\n"
        for chart_name in state["charts"]:
            chart_markdown += f"![{chart_name}]({chart_name})\n\n"
            
    # 2. Extract stdout and text data previews
    analyst_findings = state.get("findings", "No stdout findings captured.")
    
    collected_summary = []
    for k, v in state.get("collected_data", {}).items():
        args = v.get("args", {})
        result_preview = str(v.get("result", ""))[:300]
        collected_summary.append(f"- **{k}** (Parameters: {args}):\n  {result_preview}...\n")
        
    collected_str = "\n".join(collected_summary) if collected_summary else "No external API data collected."
    
    prompt = f"""You are a Senior Data Analyst. Write a comprehensive, high-fidelity research report based on the compiled analysis.
Today's date is: {state['current_date']}.

User Query: "{state['query']}"

Data Gathered from APIs:
{collected_str}

Statistical Analyst Node stdout Output:
```text
{analyst_findings}
```

Your report must be structured professionally and contain:
1. **Executive Summary**: A concise answer to the user's primary query, outlining today's state (Jun 21, 2026).
2. **Key Findings**: Detailed discussion of metrics, figures, and calculations.
3. **Hidden Patterns**: Highlight any anomalies, correlations, variance spikes, or interesting insights discovered in the data.
4. **Actionable Suggestions for Improvement**: Concrete business or technical recommendations.

Include standard headings (use #, ##, etc.) and write in a premium, professional communication style. Do not invent charts, but refer to the charts generated: {state.get('charts', [])}.

Write the final markdown report below:
"""

    response = llm.invoke(prompt)
    report_content = response.content.strip()
    
    # Append the chart markdown to the end of the report if not already included
    if chart_markdown and "### Visual Charts Generated" not in report_content:
        report_content += "\n\n" + chart_markdown
        
    # Also save the report as a markdown file in output folder
    report_filepath = os.path.join(OUTPUT_DIR, "analysis_report.md")
    try:
        with open(report_filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[*] Saved final markdown report to: {report_filepath}")
    except Exception as e:
        print(f"[Warning] Failed to write report file: {e}")
        
    return {"final_report": report_content}
