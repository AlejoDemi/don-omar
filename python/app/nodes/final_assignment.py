from typing import List, Dict, Any
import re
from ..llm import build_chat_llm


async def build_final_assignment(roadmap: str, skills: List[Dict[str, Any]]) -> str:
    """
    Create a detailed final assignment that consolidates the knowledge from the roadmap.
    Assumes the user already knows the skills in `skills`; tasks may include those skills.
    Output should be concise (~1000 chars), point by point (Spanish, Slack markdown friendly),
    and MUST NOT exceed 1000 characters to avoid overwhelming the main roadmap.
    """
    llm = build_chat_llm()
    if llm is None:
        return _fallback_assignment(roadmap, skills)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        return _fallback_assignment(roadmap, skills)

    skills_lines = []
    for s in skills or []:
        if not isinstance(s, dict):
            continue
        name = s.get("name") or ""
        prof = s.get("proficiency") or ""
        cats = s.get("categories") or []
        line = f"- {name}" + (f" ({prof})" if prof else "")
        if cats:
            line += f" - {', '.join(cats)}"
        skills_lines.append(line)
    skills_text = "\n".join(skills_lines) if skills_lines else "(sin skills registradas)"

    system_msg = (
        "Eres un instructor técnico. A partir del ROADMAP, crea un TRABAJO FINAL conciso para practicar. "
        "Asume conocidas las SKILLS (puedes usarlas en las tareas). "
        "REQUISITOS ESTRICTOS:\n"
        "- Máximo 1000 caracteres total.\n"
        "- Español, formato simple para Slack.\n"
        "- 1 línea de objetivo + 3–5 pasos numerados '1.', '2.', '3.' en líneas separadas (cada paso: qué hacer y un criterio breve en UNA línea).\n"
        "- No repitas el roadmap; solo consolida y convierte en acciones.\n"
        "- Sin títulos largos, sin bloques de código, sin listas extensas."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human",
         "ROADMAP (resumen de lo aprendido):\n{roadmap}\n\n"
         "SKILLS DADAS POR SABIDAS (pueden usarse en las tareas):\n{skills}\n\n"
         "Devuelve SOLO el trabajo final, cumpliendo estrictamente con el máximo de 1000 caracteres y los pasos en líneas separadas.")
    ])

    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({
            "roadmap": (roadmap or "").strip(),
            "skills": skills_text,
        })
        text = (result or "").strip()
        text = _normalize_slack_mrkdwn(text)
        return _shorten(text, 1000)
    except Exception:
        return _fallback_assignment(roadmap, skills)


def _fallback_assignment(roadmap: str, skills: List[Dict[str, Any]]) -> str:
    base = "Objetivo: Proyecto integrador aplicando el roadmap.\n"
    steps = (
        "1. Módulo principal listo (pasa pruebas)\n"
        "2. Feature que combine 2 conceptos del roadmap (funcional)\n"
        "3. README y ejecución/despliegue listos (pasos claros)"
    )
    text = f"{base}{steps}"
    text = _normalize_slack_mrkdwn(text)
    return _shorten(text, 1000)


def _shorten(text: str, max_len: int) -> str:
    if not text:
        return ""
    s = " ".join(text.split())  # compact whitespace/newlines
    if len(s) <= max_len:
        return s
    return s[:max_len - 1] + "…"


def _normalize_slack_mrkdwn(text: str) -> str:
    """
    Normalize output to be Slack-friendly:
    - Convert **bold** to *bold*
    - Ensure numbered steps '1.' '2.' '3.' each start on their own line
    - Convert '1)' or '1)-' to '1.'
    - Collapse excessive whitespace while preserving newlines between items
    """
    if not text:
        return ""
    out = text
    # Convert **bold** -> *bold*
    out = re.sub(r"\*\*(.+?)\*\*", r"*\1*", out)
    # Convert 1) / 1)- / 1.- -> 1.
    out = re.sub(r"(\b\d+)\s*[\)\.-]\s*", r"\1. ", out)
    # Ensure each numbered item starts on a new line
    out = re.sub(r"(?<!^)(?<!\n)(\d+\.\s)", r"\n\1", out, flags=re.MULTILINE)
    # Trim trailing spaces on lines
    out = "\n".join([ln.rstrip() for ln in out.splitlines()])
    return out.strip()

