from ..llm import build_chat_llm


async def review_objective(objective: str) -> bool:
    """
    LLM-driven check: Ask the model if the objective is a relevant technical learning goal.
    Model must answer strictly 'VALID' or 'INVALID'.
    Falls back to a permissive simple check if LLM is unavailable.
    """
    if not objective or len(objective.strip()) < 3:
        return False

    llm = build_chat_llm()
    if llm is None:
        text = objective.lower()
        return 'aprender' in text or len(text.split()) >= 2

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        text = objective.lower()
        return 'aprender' in text or len(text.split()) >= 2

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres un filtro. Determina si el objetivo del usuario es un objetivo técnico relevante "
         "(software, datos, infraestructura, IA, DevOps, etc.). Responde SOLO con 'VALID' o 'INVALID'."),
        ("human",
         "Objetivo del usuario:\n{objective}\n\n"
         "Responde únicamente una palabra: VALID o INVALID.")
    ])

    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({"objective": objective})
        normalized = (result or "").strip().upper()
        return normalized == "VALID"
    except Exception:
        text = objective.lower()
        return 'aprender' in text or len(text.split()) >= 2


