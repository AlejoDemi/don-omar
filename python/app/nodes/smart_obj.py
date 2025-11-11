import json
from ..llm import build_chat_llm


async def to_smart_objective(objective: str, skills: list) -> str:
    """
    Transform the raw user objective into a concise SMART objective in Spanish.
    SMART = Específico, Medible, Alcanzable, Relevante, con Tiempo definido.
    If LLM is not available, return a basic templated SMART objective.
    """
    llm = build_chat_llm()
    if llm is None:
        return _fallback_smart(objective)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        return _fallback_smart(objective)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres un experto en planificación de objetivos. Convierte el objetivo del usuario "
         "en un objetivo SMART en español. Sigue estas pautas:\n"
         "- Específico: qué quiere lograr exactamente.\n"
         "- Medible: indicadores o métricas claras.\n"
         "- Alcanzable: realista con recursos y nivel actual.\n"
         "- Relevante: por qué importa para el usuario.\n"
         "- Tiempo: un plazo concreto (fechas/semanas/meses).\n"
         "Devuelve SOLO el objetivo final en una o dos oraciones, sin listas ni explicaciones adicionales."),
        ("human",
         "Objetivo original:\n{objective}\n\n"
         "Skills (contexto opcional):\n{skills}\n\n"
         "Devuelve el objetivo SMART.")
    ])

    skills_brief = []
    for s in skills or []:
        if isinstance(s, dict):
            skills_brief.append({
                "name": s.get("name"),
                "proficiency": s.get("proficiency"),
                "categories": s.get("categories"),
            })

    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({
            "objective": objective or "",
            "skills": json.dumps(skills_brief, ensure_ascii=False),
        })
        return (result or "").strip()
    except Exception:
        return _fallback_smart(objective)


def _fallback_smart(objective: str) -> str:
    text = (objective or "").strip()
    if not text:
        text = "Aprender un tema técnico relevante"
    return (
        f"{text} con un plan práctico y ejercicios, midiendo progreso con hitos semanales, "
        f"asegurando avances realistas según disponibilidad, y logrando un entregable concreto en 4 semanas."
    )


