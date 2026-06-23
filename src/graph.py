from langgraph.graph import StateGraph, START, END
from src.state import AnalystState
from src.agents import planner_node, collector_node, analyst_node, reporter_node

def create_agent_graph():
    """
    Creates and compiles the StateGraph workflow of our data analyst agent.
    """
    # Initialize StateGraph with our custom state schema
    workflow = StateGraph(AnalystState)
    
    # Add nodes for each agent role
    workflow.add_node("planner", planner_node)
    workflow.add_node("collector", collector_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define linear sequential edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "collector")
    workflow.add_edge("collector", "analyst")
    workflow.add_edge("analyst", "reporter")
    workflow.add_edge("reporter", END)
    
    # Compile and return the runnable graph
    return workflow.compile()
