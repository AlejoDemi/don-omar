from typing import Dict, Any, TypedDict, List, Literal
import os
from .nodes.reviewer import review_objective
from .nodes.smart_obj import to_smart_objective
from .nodes.rag import retrieve_context
from .nodes.roadmap import build_roadmap
from .nodes.final_assignment import build_final_assignment
from langgraph.graph import StateGraph, START, END
from langsmith import traceable


class AgentState(TypedDict):
    objective: str
    skills: List[Dict[str, Any]]
    is_valid: bool
    status: str
    deadline: str  # Plazo para alcanzar el objetivo (ej: "1 mes", "2 semanas", "3 meses")
    smart_objective: str
    context: str
    roadmap: str
    final_assignment: str

@traceable
async def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviews the objective for technical relevance and extracts deadline.
    Sets is_valid to True/False, extracts deadline, and updates status accordingly.
    """
    print("\n" + "="*60)
    print("🔍 [STEP 1/4] REVIEWER NODE")
    print("="*60)
    
    objective = state.get("objective", "")
    print(f"📝 Input: {len(objective)} chars | Preview: '{objective[:80]}...'")
    
    is_valid, deadline = await review_objective(objective)
    
    if not is_valid:
        print(f"❌ Status: REJECTED")
        print(f"⏰ Deadline detected: {deadline}")
        print(f"➡️  Next: END (invalid objective)")
        return {
            **state,
            "is_valid": False,
            "status": "invalid_objective",
            "deadline": deadline,
        }
    
    print(f"✅ Status: ACCEPTED")
    print(f"⏰ Deadline: {deadline}")
    print(f"➡️  Next: SMART OBJECTIVE NODE")
    return {
        **state,
        "is_valid": True,
        "status": "ok",
        "deadline": deadline,
    }


@traceable
async def to_smart_obj_node(state: AgentState) -> AgentState:
    """
    Transforms the raw objective into a SMART objective with deadline.
    """
    print("\n" + "="*60)
    print("✨ [STEP 2/4] SMART OBJECTIVE NODE")
    print("="*60)
    
    objective = state.get("objective", "")
    skills = state.get("skills", [])
    deadline = state.get("deadline", "1 mes")
    
    print(f"📋 Skills count: {len(skills)}")
    print(f"⏰ Deadline: {deadline}")
    print(f"🔄 Generating SMART objective...")
    
    smart_text = await to_smart_objective(objective, skills, deadline)
    
    print(f"✅ Generated: {len(smart_text)} chars")
    print(f"➡️  Next: RAG NODE")
    
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
    print("\n" + "="*60)
    print("🔍 [STEP 3/4] RAG NODE (Semantic Search)")
    print("="*60)
    
    objective = state.get("objective", "") or ""
    print(f"🔎 Query: '{objective[:80]}...'")
    print(f"🗄️  Collection: docs | k=5")
    
    try:
        context = retrieve_context(objective, collection_name="docs", k=1)
        context_length = len(context) if context else 0
        print(f"✅ Retrieved: {context_length} chars of context")
    except Exception as e:
        print(f"❌ Error: {e}")
        context = ""
        print(f"⚠️  Using empty context (fallback)")
    
    print(f"➡️  Next: ROADMAP BUILDER NODE")
    
    return {
        **state,
        "context": context,
    }


@traceable
async def roadmap_builder_node(state: AgentState) -> AgentState:
    """
    Generates a short roadmap based on the SMART objective, optional context, user skills, and deadline.
    """
    print("\n" + "="*60)
    print("🗺️  [STEP 4/4] ROADMAP BUILDER NODE")
    print("="*60)
    
    smart = state.get("smart_objective", "") or ""
    ctx = state.get("context", "") or ""
    skills = state.get("skills", [])
    deadline = state.get("deadline", "1 mes")
    
    print(f"📋 Skills: {len(skills)}")
    print(f"📝 SMART objective: {len(smart)} chars")
    print(f"📚 Context: {len(ctx)} chars")
    print(f"⏰ Deadline: {deadline}")
    print(f"🔄 Building roadmap...")
    
    roadmap = await build_roadmap(smart, ctx, skills, deadline)
    
    print(f"✅ Generated: {len(roadmap)} chars")
    print(f"➡️  Next: FINAL ASSIGNMENT NODE")
    
    return {
        **state,
        "roadmap": roadmap or "",
    }


@traceable
async def final_assignment_node(state: AgentState) -> AgentState:
    """
    Assigns the final assignment to the user based on roadmap and skills.
    Must return a moderately detailed, point-by-point assignment.
    """
    roadmap = state.get("roadmap", "") or ""
    skills = state.get("skills", [])
    print("\n" + "="*60)
    print("🧪  [FINAL] FINAL ASSIGNMENT NODE")
    print("="*60)
    print(f"📚 Roadmap length: {len(roadmap)} chars | Skills: {len(skills)}")
    assignment = await build_final_assignment(roadmap, skills)
    print(f"✅ Final assignment: {len(assignment)} chars")
    return {
        **state,
        "final_assignment": assignment or "",
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
workflow.add_node("final_assignment_task", final_assignment_node)

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
workflow.add_edge("roadmap_builder", "final_assignment_task")
workflow.add_edge("final_assignment_task", END)

app = workflow.compile()


@traceable
async def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the LangGraph workflow for reviewing, SMART-transforming, retrieving context, building roadmap, and final assignment.
    """
    print("\n" + "🚀" + "="*58 + "🚀")
    print("           PIPELINE EXECUTION STARTED")
    print("🚀" + "="*58 + "🚀")
    
    initial_state: AgentState = {
        "objective": payload.get("objective", ""),
        "skills": payload.get("skills", []),
        "is_valid": False,
        "status": "",
        "deadline": "1 mes",
        "smart_objective": "",
        "context": "",
        "roadmap": "",
        "final_assignment": "",
    }
    
    print(f"📊 Initial State:")
    print(f"   - Objective: {len(initial_state['objective'])} chars")
    print(f"   - Skills: {len(initial_state['skills'])} items")
    print("")
    
    result = await app.ainvoke(initial_state)
    
    print("\n" + "="*60)
    print("📦 [FINAL] BUILDING RESPONSE")
    print("="*60)
    
    # Si el objetivo no es válido, retornar mensaje de ayuda
    if result.get("status") == "invalid_objective":
        response = (
            "❌ *Objetivo no válido*\n\n"
            "Solo puedo ayudarte con objetivos de *programación y tecnología*.\n\n"
            "Puedo ayudarte a aprender:\n"
            "• 🔤 Lenguajes: Python, JavaScript, Java, TypeScript, etc.\n"
            "• ⚛️ Frameworks: React, Django, Node.js, Vue, Angular, etc.\n"
            "• 🐳 Tecnologías: Docker, Kubernetes, Git, CI/CD, etc.\n"
            "• ☁️ Cloud: AWS, Azure, GCP, serverless, etc.\n"
            "• 🗄️ Bases de datos: SQL, MongoDB, PostgreSQL, etc.\n"
            "• 🤖 Data Science, Machine Learning, IA\n"
            "• 🌐 Desarrollo web, móvil, backend, frontend\n\n"
            "Ejemplos válidos:\n"
            "• _'Quiero aprender React en 2 semanas'_\n"
            "• _'Necesito dominar Python'_\n"
            "• _'Aprender Docker y Kubernetes'_"
        )
        print(f"❌ Status: invalid_objective")
        print(f"📝 Response length: {len(response)} chars")
        print("\n" + "🏁" + "="*58 + "🏁")
        print("           PIPELINE COMPLETED (REJECTED)")
        print("🏁" + "="*58 + "🏁\n")
        return {
            "status": "invalid_objective",
            "response": response,
        }
    
    smart_text = (result.get("smart_objective") or "").strip()
    roadmap = (result.get("roadmap") or "").strip()
    final_assignment = (result.get("final_assignment") or "").strip()
    deadline = result.get("deadline", "1 mes")
    
    print(f"✅ Status: {result.get('status', 'ok')}")
    print(f"📝 SMART objective: {len(smart_text)} chars")
    print(f"🗺️  Roadmap: {len(roadmap)} chars")
    print(f"🧪  Final assignment: {len(final_assignment)} chars")
    print(f"⏰ Deadline: {deadline}")
    
    # Build a single response string with rich formatting
    response_parts: List[str] = []
    if smart_text:
        response_parts.append(f"✨ *OBJETIVO SMART*\n\n{smart_text}")
    if roadmap:
        response_parts.append(f"🗺️ *ROADMAP DE APRENDIZAJE* _(Plazo: {deadline})_\n\n{roadmap}")
    if final_assignment:
        response_parts.append(f"🧪 *TRABAJO FINAL*\n\n{final_assignment}")
    
    separator = "\n\n" + "─" * 40 + "\n\n"
    response = separator.join(response_parts) if response_parts else ""

    print(f"📦 Final response: {len(response)} chars")
    print("\n" + "🏁" + "="*58 + "🏁")
    print("           PIPELINE COMPLETED (SUCCESS)")
    print("🏁" + "="*58 + "🏁\n")
    
    return {
        "status": result.get("status", "ok"),
        "response": response,
    }


