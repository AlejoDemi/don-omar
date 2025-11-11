from typing import Dict, Any, TypedDict, List, Literal
import os
from .nodes.reviewer import review_objective
from .nodes.smart_obj import to_smart_objective
from .nodes.rag import retrieve_context
from .nodes.roadmap import build_roadmap
from langgraph.graph import StateGraph, START, END
from langsmith import traceable


class AgentState(TypedDict):
    objective: str
    skills: List[Dict[str, Any]]
    is_valid: bool
    status: str
    smart_objective: str
    context: str
    roadmap: str

@traceable
async def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviews the objective for technical relevance.
    Sets is_valid to True/False and updates status accordingly.
    """
    objective = state.get("objective", "")
    is_valid = await review_objective(objective)
    
    if not is_valid:
        return {
            **state,
            "is_valid": False,
            "status": "invalid_objective",
        }
    
    return {
        **state,
        "is_valid": True,
        "status": "ok",
    }


@traceable
async def to_smart_obj_node(state: AgentState) -> AgentState:
    """
    Transforms the raw objective into a SMART objective.
    """
    objective = state.get("objective", "")
    skills = state.get("skills", [])
    smart_text = await to_smart_objective(objective, skills)
    return {
        **state,
        "smart_objective": smart_text,
    }


@traceable
async def rag_node(state: AgentState) -> AgentState:
    """
    Retrieves supporting context from the vector DB based on the user's objective.
    Adds the concatenated context into the state.
    """
    objective = state.get("objective", "") or ""
    print(f"[RAG] Query (objective): {objective!r}")
    try:
        context = retrieve_context(objective, collection_name="docs", k=5)
    except Exception as e:
        print(f"[RAG] Error during semantic search: {e}")
        context = ""
    print(f"""[RAG] Context to inject into state:
{context}""")
    return {
        **state,
        "context": context,
    }


@traceable
async def roadmap_builder_node(state: AgentState) -> AgentState:
    """
    Generates a short roadmap based on the SMART objective and optional context.
    """
    smart = state.get("smart_objective", "") or ""
    ctx = state.get("context", "") or ""
    roadmap = await build_roadmap(smart, ctx)
    return {
        **state,
        "roadmap": roadmap or "",
    }


@traceable
def should_to_smart_obj(state: AgentState) -> Literal["to_smart_obj", "end"]:
    """
    After reviewer_node, if valid -> go to to_smart_obj, else -> end.
    """
    if state.get("is_valid", False):
        return "to_smart_obj"
    return "end"


workflow = StateGraph(AgentState)

workflow.add_node("reviewer", reviewer_node)
workflow.add_node("to_smart_obj", to_smart_obj_node)
workflow.add_node("rag", rag_node)
workflow.add_node("roadmap_builder", roadmap_builder_node)

workflow.add_edge(START, "reviewer")
workflow.add_conditional_edges(
    "reviewer",
    should_to_smart_obj,
    {
        "to_smart_obj": "to_smart_obj",
        "end": END
    }
)
workflow.add_edge("to_smart_obj", "rag")
workflow.add_edge("rag", "roadmap_builder")
workflow.add_edge("roadmap_builder", END)

app = workflow.compile()


@traceable
async def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the LangGraph workflow for reviewing, SMART-transforming and retrieving context.
    """
    initial_state: AgentState = {
        "objective": payload.get("objective", ""),
        "skills": payload.get("skills", []),
        "is_valid": False,
        "status": "",
        "smart_objective": "",
        "context": "",
        "roadmap": "",
    }
    
    result = await app.ainvoke(initial_state)
    
    smart_text = (result.get("smart_objective") or "").strip()
    roadmap = (result.get("roadmap") or "").strip()
    # Build a single response string. Append roadmap only if present.
    response_parts: List[str] = []
    if smart_text:
        response_parts.append("SMART objective:\n" + smart_text)
    if roadmap:
        response_parts.append("ROADMAP:\n" + roadmap)
    response = "\n\n".join(part for part in response_parts if part)

    print(f"""[PIPELINE] Built response:
{response}""")
    return {
        "status": result.get("status", "ok"),
        "response": response,
    }


