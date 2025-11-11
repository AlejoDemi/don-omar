import json
from ..llm import build_chat_llm


async def build_roadmap(smart_objective: str, context: str) -> str:
    """
    Build a concise, clear learning roadmap in Spanish.
    Use provided context when helpful but do not limit to it.
    Each step must include:
    - Concept
    - Description
    - Useful links
    """
    llm = build_chat_llm()
    if llm is None:
        return _fallback_roadmap(smart_objective, context)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        return _fallback_roadmap(smart_objective, context)

    system_msg = (
        "Eres un coach técnico. Usa el contexto como referencia, pero NO te limites a él. "
        "Genera un roadmap conciso y claro con los conceptos clave a aprender y, cuando corresponda, "
        "incluye cursos o recursos recomendados (por ejemplo, si aparecen en el contexto). "
        "Formato requerido para cada paso (en español):\n\n"
        "Concept: <título del concepto>\n"
        "Description: <explicación breve y accionable>\n"
        "Useful links: <uno o más enlaces relevantes>\n\n"
        "Devuelve solo el roadmap (lista de pasos), sin texto adicional ni explicaciones previas/posteriores."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human",
         "SMART objective:\n{smart}\n\n"
         "Context (referencia opcional):\n{context}\n\n"
         "Construye el roadmap siguiendo estrictamente el formato indicado.")
    ])

    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({
            "smart": (smart_objective or "").strip(),
            "context": (context or "").strip(),
        })
        return (result or "").strip()
    except Exception:
        return _fallback_roadmap(smart_objective, context)


def _fallback_roadmap(smart_objective: str, context: str) -> str:
    base = (smart_objective or "Aprender un tema técnico").strip()
    return (
        f"Concept: Fundamentos del tema\n"
        f"Description: Asegura comprensión de los principios básicos para {base}.\n"
        f"Useful links: https://developer.mozilla.org/\n\n"
        f"Concept: Práctica guiada\n"
        f"Description: Realiza un proyecto pequeño aplicando los conceptos clave.\n"
        f"Useful links: https://www.freecodecamp.org/\n\n"
        f"Concept: Despliegue\n"
        f"Description: Publica el proyecto y documenta el proceso extremo a extremo.\n"
        f"Useful links: https://docs.docker.com/"
    )


