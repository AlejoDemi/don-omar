import json
from typing import List, Dict, Any
from ..llm import build_chat_llm


async def build_roadmap(smart_objective: str, context: str, skills: List[Dict[str, Any]] = None, deadline: str = "1 mes") -> str:
    """
    Build a concise, clear learning roadmap in Spanish with timeline.
    Takes into account user's current skills to personalize the roadmap.
    Adjusts depth and number of steps based on the deadline.
    Use provided context when helpful but do not limit to it.
    Each step must include:
    - Concept
    - Description
    - Timeline (estimated time to complete)
    - Useful links
    """
    llm = build_chat_llm()
    if llm is None:
        return _fallback_roadmap(smart_objective, context, skills, deadline)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        return _fallback_roadmap(smart_objective, context, skills, deadline)

    # Formatear las skills del usuario
    skills_text = _format_skills(skills)

    system_msg = (
        "Eres un coach técnico experto. PRIORIZA Y USA EL CONTEXTO PROPORCIONADO como base principal del roadmap. "
        "El contexto contiene información curada y relevante que DEBES aprovechar al máximo. "
        "Genera un roadmap conciso, claro y altamente personalizado.\n\n"
        "PRIORIDADES (en orden de importancia):\n"
        "1. 🎯 CONTEXTO: Si hay contexto disponible, úsalo como BASE del roadmap:\n"
        "   - Extrae los conceptos clave mencionados\n"
        "   - USA PRINCIPALMENTE los links/URLs que aparecen en el contexto\n"
        "   - Adapta los recursos del contexto a las necesidades del usuario\n"
        "   - Si el contexto tiene cursos/tutoriales específicos, inclúyelos\n\n"
        "2. 👤 SKILLS DEL USUARIO: Personaliza según su nivel:\n"
        "   - Si tiene skills relacionadas: salta fundamentos básicos, ve directo a temas intermedios/avanzados\n"
        "   - Si NO tiene skills relacionadas: empieza desde cero con fundamentos\n"
        "   - Menciona explícitamente cómo sus skills actuales lo ayudan (ej: 'Dado tu conocimiento en X...')\n\n"
        "3. ⏰ PLAZO DISPONIBLE: Ajusta cantidad y profundidad:\n"
        "   - Plazo corto (1-2 semanas): 2-3 pasos focalizados en lo esencial\n"
        "   - Plazo medio (1 mes): 3-4 pasos con buena cobertura\n"
        "   - Plazo largo (2-3 meses): 4-6 pasos con profundidad progresiva\n"
        "   - Plazo muy largo (6+ meses): 6-8 pasos con desarrollo completo\n"
        "   - Asegúrate que la suma de tiempos NO exceda el plazo total\n\n"
        "FORMATO DE SALIDA (usa SOLO markdown de Slack, NO markdown estándar):\n\n"
        "Para cada paso usa este formato EXACTO:\n\n"
        "*📚 [Número]. [Título del Concepto]*\n"
        "[Descripción breve y accionable - máximo 2 líneas]\n"
        "⏱️ _Tiempo:_ [tiempo estimado]\n"
        "🔗 _Links:_ [enlaces relevantes]\n\n"
        "Ejemplo:\n"
        "*📚 1. Fundamentos de React*\n"
        "Aprende componentes, props y state para construir interfaces interactivas.\n"
        "⏱️ _Tiempo:_ 2 días\n"
        "🔗 _Links:_ https://react.dev/learn\n\n"
        "CRÍTICO - Formato de Slack:\n"
        "- Usa *texto* (UN solo asterisco) para negrita, NO uses **texto**\n"
        "- Usa _texto_ (guión bajo) para cursiva\n"
        "- Usa emojis Unicode directos (📚 ⏱️ 🔗) NO códigos :emoji:\n"
        "- Mantén descripciones CONCISAS (1-2 líneas máximo)\n"
        "- Deja UNA línea en blanco entre pasos\n"
        "- RESPETA el plazo total: ajusta cantidad de pasos y tiempos individuales\n\n"
        "IMPORTANTE - Links:\n"
        "- PRIORIDAD 1: Usa los links/URLs que aparecen en el contexto proporcionado\n"
        "- PRIORIDAD 2: Solo si no hay links en el contexto, usa recursos conocidos relevantes\n"
        "- Si el contexto menciona cursos específicos, úsalos directamente\n\n"
        "Devuelve solo el roadmap formateado, sin texto adicional."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human",
         "OBJETIVO SMART:\n{smart}\n\n"
         "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
         "📚 CONTEXTO CURADO (PRIORIDAD ALTA - USA ESTA INFORMACIÓN):\n{context}\n"
         "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
         "👤 SKILLS ACTUALES DEL USUARIO (PERSONALIZA SEGÚN ESTO):\n{skills}\n\n"
         "⏰ PLAZO DISPONIBLE: {deadline}\n\n"
         "INSTRUCCIONES:\n"
         "1. PRIORIZA el contexto: extrae conceptos y links de ahí\n"
         "2. ADAPTA al nivel del usuario según sus skills\n"
         "3. AJUSTA la profundidad al plazo disponible\n"
         "4. USA los links del contexto en tu roadmap\n\n"
         "Construye el roadmap ahora:")
    ])

    chain = prompt | llm | StrOutputParser()
    try:
        # Preparar el contexto con énfasis
        context_text = (context or "").strip()
        if not context_text:
            context_text = "(No hay contexto disponible - usa recursos conocidos de calidad)"
        
        result = await chain.ainvoke({
            "smart": (smart_objective or "").strip(),
            "context": context_text,
            "skills": skills_text,
            "deadline": deadline,
        })
        return (result or "").strip()
    except Exception:
        return _fallback_roadmap(smart_objective, context, skills, deadline)


def _format_skills(skills: List[Dict[str, Any]] = None) -> str:
    """
    Format user skills into a readable text format with emphasis for roadmap personalization.
    """
    if not skills or len(skills) == 0:
        return "⚠️ Usuario SIN skills previas registradas → Empieza desde FUNDAMENTOS BÁSICOS"
    
    formatted = [f"✅ Usuario CON {len(skills)} skill(s) existente(s) → ADAPTA el nivel según esto:\n"]
    
    for i, skill in enumerate(skills, 1):
        skill_name = skill.get("name", "Desconocido")
        proficiency = skill.get("proficiency", "")
        categories = skill.get("categories", [])
        
        skill_text = f"{i}. {skill_name}"
        if proficiency:
            skill_text += f" - Nivel: {proficiency}"
        if categories and len(categories) > 0:
            skill_text += f" - Categorías: {', '.join(categories)}"
        formatted.append(skill_text)
    
    formatted.append("\n💡 APROVECHA estas skills como base para acelerar el aprendizaje")
    
    return "\n".join(formatted)


def _fallback_roadmap(smart_objective: str, context: str, skills: List[Dict[str, Any]] = None, deadline: str = "1 mes") -> str:
    base = (smart_objective or "Aprender un tema técnico").strip()
    has_skills = skills and len(skills) > 0
    
    # Ajustar número de pasos según el deadline
    deadline_lower = deadline.lower()
    if "semana" in deadline_lower and not "mes" in deadline_lower:
        # Plazo corto: 2 pasos
        return (
            f"*📚 1. Fundamentos Esenciales*\n"
            f"Comprende los conceptos básicos clave para {base}.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.6)}\n"
            f"🔗 _Links:_ https://developer.mozilla.org/\n\n"
            f"*📚 2. Práctica Inicial*\n"
            f"Aplica lo aprendido en un ejercicio práctico pequeño.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.4)}\n"
            f"🔗 _Links:_ https://www.freecodecamp.org/"
        )
    elif "6 mes" in deadline_lower or "año" in deadline_lower:
        # Plazo largo: 5 pasos
        return (
            f"*📚 1. Fundamentos del Tema*\n"
            f"Domina los principios básicos para {base}.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.2)}\n"
            f"🔗 _Links:_ https://developer.mozilla.org/\n\n"
            f"*📚 2. Conceptos Intermedios*\n"
            f"Profundiza en técnicas y patrones avanzados.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.25)}\n"
            f"🔗 _Links:_ https://www.freecodecamp.org/\n\n"
            f"*📚 3. Proyecto Práctico*\n"
            f"Desarrolla un proyecto completo aplicando todo lo aprendido.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.3)}\n"
            f"🔗 _Links:_ https://github.com/\n\n"
            f"*📚 4. Optimización y Mejores Prácticas*\n"
            f"Refina el proyecto con patrones profesionales.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.15)}\n"
            f"🔗 _Links:_ https://refactoring.guru/\n\n"
            f"*📚 5. Despliegue y Documentación*\n"
            f"Publica el proyecto y documenta todo el proceso.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.1)}\n"
            f"🔗 _Links:_ https://docs.docker.com/"
        )
    else:
        # Plazo medio (1-3 meses): 3 pasos
        return (
            f"*📚 1. Fundamentos del Tema*\n"
            f"Asegura comprensión de los principios básicos para {base}.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.4)}\n"
            f"🔗 _Links:_ https://developer.mozilla.org/\n\n"
            f"*📚 2. Práctica Guiada*\n"
            f"Realiza un proyecto aplicando los conceptos clave.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.4)}\n"
            f"🔗 _Links:_ https://www.freecodecamp.org/\n\n"
            f"*📚 3. Despliegue*\n"
            f"Publica el proyecto y documenta el proceso.\n"
            f"⏱️ _Tiempo:_ {_calculate_step_time(deadline, 0.2)}\n"
            f"🔗 _Links:_ https://docs.docker.com/"
        )


def _calculate_step_time(total_deadline: str, percentage: float) -> str:
    """Calculate step time based on total deadline and percentage"""
    import re
    deadline_lower = total_deadline.lower()
    
    # Extract number and unit
    match = re.search(r'(\d+)\s*(semana|mes|año)', deadline_lower)
    if not match:
        return "1 semana"
    
    number = int(match.group(1))
    unit = match.group(2)
    
    # Calculate step time
    step_value = int(number * percentage)
    if step_value < 1:
        step_value = 1
    
    # Return formatted time
    if unit == "semana" or unit == "semanas":
        return f"{step_value} {'semana' if step_value == 1 else 'semanas'}"
    elif unit == "mes" or unit == "meses":
        return f"{step_value} {'mes' if step_value == 1 else 'meses'}"
    else:  # año
        if step_value >= 12:
            months = step_value
            return f"{months} meses"
        return f"{step_value} {'mes' if step_value == 1 else 'meses'}"


