import json
from ..llm import build_chat_llm


async def to_smart_objective(objective: str, skills: list, deadline: str = "1 mes") -> str:
    """
    Transform the raw user objective into a concise SMART objective in Spanish.
    SMART = Específico, Medible, Alcanzable, Relevante, con Tiempo definido.
    If LLM is not available, return a basic templated SMART objective.
    """
    llm = build_chat_llm()
    if llm is None:
        return _fallback_smart(objective, deadline)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        return _fallback_smart(objective, deadline)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres un experto en planificación de objetivos. Convierte el objetivo del usuario "
         "en un objetivo SMART en español con formato enriquecido para Slack. Sigue estas pautas:\n"
         "- Específico: qué quiere lograr exactamente.\n"
         "- Medible: indicadores o métricas claras.\n"
         "- Alcanzable: realista con recursos y nivel actual (considera el plazo disponible).\n"
         "- Relevante: por qué importa para el usuario.\n"
         "- Tiempo: usa el plazo proporcionado como marco temporal del objetivo.\n"
         "IMPORTANTE: Ajusta el alcance y profundidad del objetivo según el tiempo disponible. "
         "Si el plazo es corto (1-2 semanas), el objetivo debe ser más acotado. "
         "Si es más largo (3+ meses), puede ser más ambicioso.\n\n"
         "FORMATO DE SALIDA:\n"
         "Usa SOLO formato markdown de Slack (NO uses markdown estándar):\n"
         "- Usa *texto* (UN asterisco) para negrita\n"
         "- Usa _texto_ (guión bajo) para cursiva\n"
         "- Usa emojis Unicode directos (🎯 ✨ 💪) NO códigos como :emoji:\n"
         "- Máximo 3-4 líneas de texto, muy conciso\n"
         "- Haz el objetivo directo e inspirador, SIN explicaciones extensas\n\n"
         "Devuelve SOLO el objetivo SMART (2-3 oraciones máximo), sin listas ni detalles."),
        ("human",
         "Objetivo original:\n{objective}\n\n"
         "Skills (contexto opcional):\n{skills}\n\n"
         "Plazo disponible:\n{deadline}\n\n"
         "Devuelve el objetivo SMART con formato enriquecido.")
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
            "deadline": deadline,
        })
        return (result or "").strip()
    except Exception:
        return _fallback_smart(objective, deadline)


def _fallback_smart(objective: str, deadline: str = "1 mes") -> str:
    text = (objective or "").strip()
    if not text:
        text = "Aprender un tema técnico relevante"
    return (
        f"🎯 *Objetivo SMART:*\n\n"
        f"{text} mediante un *plan práctico con ejercicios*, "
        f"midiendo progreso con *hitos semanales*, "
        f"asegurando avances realistas según disponibilidad, "
        f"y logrando un *entregable concreto* en *{deadline}*."
    )


