import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama

from llmops_common.config.settings import settings
from review_lab.tools.analyzers import analyze_style, analyze_security, analyze_performance

# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    code_snippet: str
    next_agent: str
    active_agent: str  # Tracks which agent is currently executing or waiting for a tool
    final_review: str

# 2. Tool Integration & LLM Setup
tools = [analyze_security, analyze_style, analyze_performance]
tool_node = ToolNode(tools)

llm = ChatOllama(
    base_url=settings.OLLAMA_HOST,
    model=settings.OLLAMA_DEFAULT_MODEL,
    temperature=0.1
)

# 3. Specialist Agents
def security_node(state: AgentState):
    """Specialist agent for security vulnerabilities."""
    sys_msg = SystemMessage(
        content="You are a strict Security Review Agent. Use the 'analyze_security' tool to scan the code. "
                "If you receive tool results, provide a brief and concise summary of the security findings."
    )
    tool_llm = llm.bind_tools([analyze_security])
    
    messages = state["messages"]
    # If starting fresh or not returning from a tool, inject the prompt
    if not messages or (messages[-1].type != "tool" and not getattr(messages[-1], "tool_calls", None)):
         prompt = f"Analyze this code for security issues:\n\n{state['code_snippet']}"
         messages = list(messages) + [HumanMessage(content=prompt)]
         
    response = tool_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "active_agent": "security_node"}

def style_node(state: AgentState):
    """Specialist agent for PEP 8 and style guidelines."""
    sys_msg = SystemMessage(
        content="You are a Python Style Agent. Use the 'analyze_style' tool to check the code. "
                "If you receive tool results, provide a brief summary of the style issues."
    )
    tool_llm = llm.bind_tools([analyze_style])
    
    messages = state["messages"]
    if state.get("active_agent") != "style_node":
         prompt = f"Analyze this code for style issues:\n\n{state['code_snippet']}"
         messages = list(messages) + [HumanMessage(content=prompt)]
         
    response = tool_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "active_agent": "style_node"}

def performance_node(state: AgentState):
    """Specialist agent for algorithmic complexity."""
    sys_msg = SystemMessage(
        content="You are a Performance Agent. Use the 'analyze_performance' tool to check the code. "
                "If you receive tool results, provide a brief summary of the performance bottlenecks."
    )
    tool_llm = llm.bind_tools([analyze_performance])
    
    messages = state["messages"]
    if state.get("active_agent") != "performance_node":
         prompt = f"Analyze this code for performance issues:\n\n{state['code_snippet']}"
         messages = list(messages) + [HumanMessage(content=prompt)]
         
    response = tool_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "active_agent": "performance_node"}

# 4. Supervisor Node (Deterministic Routing Loop)
def supervisor_node(state: AgentState):
    """
    Acts as the main router. Determines whether to execute a tool, 
    return to the calling agent, or proceed to the next phase in the pipeline.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"next_agent": "security_node"}
        
    last_message = messages[-1]
    
    # Check if the LLM requested to call a tool
    if getattr(last_message, "tool_calls", None):
        return {"next_agent": "tools"}
        
    # Check if a tool just finished execution; route back to the agent that requested it
    if last_message.type == "tool":
        return {"next_agent": state.get("active_agent")}
        
    # If no tool operations are pending, proceed sequentially
    active = state.get("active_agent")
    if active == "security_node":
        return {"next_agent": "style_node"}
    elif active == "style_node":
        return {"next_agent": "performance_node"}
    elif active == "performance_node":
        return {"next_agent": "summarizer_node"}
        
    return {"next_agent": "summarizer_node"}

# 5. Summarizer Node
def summarizer_node(state: AgentState):
    """Compiles the analytical reports into a final Markdown PR comment."""
    sys_msg = SystemMessage(
        content="You are the Lead Code Reviewer. Summarize the tool findings from the previous agents "
                "into a single, highly professional GitHub PR comment."
    )
    
    # Filter only AI responses (summaries) to prevent context window overflow from raw tool outputs
    summaries = [msg.content for msg in state["messages"] if msg.type == "ai" and not getattr(msg, "tool_calls", None)]
    context = "\n\n".join(summaries)
    
    prompt = f"Here are the sub-agent summaries:\n{context}\n\nWrite the final markdown PR comment."
    response = llm.invoke([sys_msg, HumanMessage(content=prompt)])
    
    return {"final_review": response.content, "next_agent": END}

# 6. Graph Construction
def build_review_graph():
    workflow = StateGraph(AgentState)
    
    # Register all nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("security_node", security_node)
    workflow.add_node("style_node", style_node)
    workflow.add_node("performance_node", performance_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("summarizer_node", summarizer_node)
    
    # Graph Entry
    workflow.set_entry_point("supervisor")
    
    # Supervisor conditional routing logic
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_agent"],
        {
            "security_node": "security_node",
            "style_node": "style_node",
            "performance_node": "performance_node",
            "tools": "tools",
            "summarizer_node": "summarizer_node",
            END: END
        }
    )
    
    # Force all operational nodes to return to the supervisor for evaluation
    for node in ["security_node", "style_node", "performance_node", "tools"]:
        workflow.add_edge(node, "supervisor")
        
    return workflow.compile()