import argparse
from src.graph import create_agent_graph

def main():
    parser = argparse.ArgumentParser(description="Autonomous Data Analyst Agent CLI")
    parser.add_argument(
        "--query", 
        type=str, 
        required=True,
        help="The query, data analysis request, or questions you want analyzed."
    )
    parser.add_argument(
        "--date",
        type=str,
        default="June 21, 2026",
        help="Custom current date context for the agent (defaults to June 21, 2026)."
    )
    args = parser.parse_args()
    
    print(f"[*] Initializing Autonomous Data Analyst workflow...")
    print(f"[*] Query: '{args.query}'")
    print(f"[*] Date context: {args.date}")
    
    # Initialize the default graph state context
    initial_state = {
        "query": args.query,
        "current_date": args.date,
        "plan": [],
        "collected_data": {},
        "execution_logs": [],
        "charts": [],
        "findings": "",
        "final_report": "",
        "errors": []
    }
    
    # Compile graph and run
    graph = create_agent_graph()
    
    print("[*] Running multi-agent state machine. This may take a few moments...")
    final_state = graph.invoke(initial_state)
    
    print("\n" + "="*60)
    print("                FINAL DATA ANALYST REPORT")
    print("="*60)
    print(final_state.get("final_report", "No report compiled."))
    
    if final_state.get("charts"):
        print("\n" + "-"*40)
        print(f"Charts saved in output/ directory: {final_state['charts']}")
    
    if final_state.get("errors"):
        print("\n" + "-"*40)
        print("Warning: The following errors occurred during execution:")
        for err in final_state["errors"]:
            print(f" - {err}")
    print("="*60)

if __name__ == "__main__":
    main()
