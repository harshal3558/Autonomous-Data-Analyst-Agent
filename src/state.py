from typing import TypedDict, List, Dict, Any

class AnalystState(TypedDict):
    """
    State representing the context of our Autonomous Data Analyst Agent.
    Tracks reasoning, collected data, executed code history, charts, and final output report.
    """
    query: str                          # User's query/prompt
    current_date: str                   # Today's date context
    plan: List[str]                     # Formulated research & analysis steps
    collected_data: Dict[str, Any]      # Collected texts, stock tickers, weather data, or csv file paths
    execution_logs: List[Dict[str, Any]]# Record of pandas analysis code run and its output/errors
    charts: List[str]                   # Names of generated charts stored in output/
    findings: str                       # Extracted intermediate findings
    final_report: str                   # Compiled senior data analyst markdown report
    errors: List[str]                   # Running logs of failures/errors
