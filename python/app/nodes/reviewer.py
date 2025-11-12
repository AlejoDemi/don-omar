from typing import Tuple
import json
from ..llm import build_chat_llm


async def review_objective(objective: str) -> Tuple[bool, str]:
    """
    LLM-driven check: Ask the model if the objective is a relevant technical learning goal
    and extract the deadline/timeframe if specified.
    Returns: (is_valid, deadline)
    - is_valid: True if valid technical objective, False otherwise
    - deadline: Extracted deadline (e.g., "2 semanas", "1 mes", "3 meses") or "1 mes" as default
    """
    if not objective or len(objective.strip()) < 3:
        return False, "1 mes"

    llm = build_chat_llm()
    if llm is None:
        is_valid = _is_technical_fallback(objective)
        deadline = _extract_simple_deadline(objective)
        return is_valid, deadline

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception:
        is_valid = _is_technical_fallback(objective)
        deadline = _extract_simple_deadline(objective)
        return is_valid, deadline

    system_msg = (
        "Eres un filtro MUY ESTRICTO de objetivos técnicos. Solo acepta objetivos de PROGRAMACIÓN y TECNOLOGÍA.\n\n"
        "ACEPTA SOLO (VALID) si menciona EXPLÍCITAMENTE:\n"
        "✅ Lenguajes: Python, JavaScript, Java, TypeScript, C++, Go, Rust, PHP, etc.\n"
        "✅ Frameworks: React, Vue, Angular, Django, Flask, Spring, Node.js, etc.\n"
        "✅ Tecnologías: Docker, Kubernetes, Git, CI/CD, Terraform, etc.\n"
        "✅ Bases de datos: SQL, MySQL, PostgreSQL, MongoDB, Redis, etc.\n"
        "✅ Cloud: AWS, Azure, GCP, Lambda, S3, EC2, etc.\n"
        "✅ Desarrollo: web development, mobile development, backend, frontend, APIs\n"
        "✅ ML/AI: machine learning, deep learning, TensorFlow, PyTorch, data science\n"
        "✅ Testing: Jest, Pytest, Selenium, unit testing, TDD\n\n"
        "RECHAZA (INVALID) TODO LO DEMÁS:\n"
        "❌ Habilidades blandas: comunicación, liderazgo, trabajo en equipo\n"
        "❌ No técnico: marketing, ventas, diseño gráfico, fotografía, video\n"
        "❌ Negocios: emprendimiento, finanzas, administración\n"
        "❌ Personal: idiomas (inglés, francés), fitness, cocina\n"
        "❌ Saludos o mensajes vagos: 'hola', 'ayuda', 'no sé'\n"
        "❌ Sin tecnología específica mencionada\n\n"
        "REGLA DE ORO: Si NO menciona una tecnología/lenguaje/framework ESPECÍFICO → INVALID\n\n"
        "Responde SIEMPRE en formato JSON:\n"
        '{{"valid": "VALID", "deadline": "1 semana"}} o {{"valid": "INVALID", "deadline": "1 mes"}}\n\n'
        "Ejemplos:\n"
        '• "aprender react" → {{"valid": "VALID", "deadline": "1 mes"}}\n'
        '• "python en 2 semanas" → {{"valid": "VALID", "deadline": "2 semanas"}}\n'
        '• "mejorar comunicación" → {{"valid": "INVALID", "deadline": "1 mes"}}\n'
        '• "diseño gráfico" → {{"valid": "INVALID", "deadline": "1 mes"}}\n'
        '• "ser mejor líder" → {{"valid": "INVALID", "deadline": "1 mes"}}'
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human",
         "Mensaje: '{objective}'\n\n"
         "¿Es un objetivo técnico válido de programación/tecnología?\n"
         "Responde SOLO con JSON (sin explicaciones):")
    ])

    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({"objective": objective})
        print(f"[REVIEWER] LLM Response: {result}")
        
        # Try to parse JSON response
        parsed = _parse_review_response(result)
        print(f"[REVIEWER] Parsed: {parsed}")
        
        if parsed:
            is_valid = parsed.get("valid", "INVALID").upper() == "VALID"
            deadline = parsed.get("deadline", "1 mes").strip()
            print(f"[REVIEWER] is_valid={is_valid}, deadline={deadline}")
            return is_valid, deadline
        
        # Si no se pudo parsear, rechazar por seguridad
        print("[REVIEWER] Failed to parse JSON, rejecting by default")
        return False, "1 mes"
    except Exception as e:
        print(f"[REVIEWER] Exception: {e}")
        is_valid = _is_technical_fallback(objective)
        deadline = _extract_simple_deadline(objective)
        print(f"[REVIEWER] Fallback: is_valid={is_valid}, deadline={deadline}")
        return is_valid, deadline


def _is_technical_fallback(text: str) -> bool:
    """
    Simple keyword-based check for technical objectives as fallback.
    Returns True only if text contains technical programming/technology keywords.
    """
    if not text or len(text.strip()) < 3:
        return False
    
    text_lower = text.lower()
    
    # Lista de palabras clave técnicas
    technical_keywords = [
        # Lenguajes de programación
        'python', 'javascript', 'java', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
        'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'bash', 'shell',
        # Frameworks y librerías
        'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express',
        'node.js', 'nodejs', 'next.js', 'nuxt', 'svelte', 'laravel', 'rails',
        # Tecnologías y herramientas
        'docker', 'kubernetes', 'k8s', 'git', 'github', 'gitlab', 'jenkins', 'ci/cd',
        'terraform', 'ansible', 'webpack', 'babel', 'npm', 'yarn', 'maven', 'gradle',
        # Cloud y DevOps
        'aws', 'azure', 'gcp', 'cloud', 'devops', 'serverless', 'lambda', 's3', 'ec2',
        # Bases de datos
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'database',
        'nosql', 'oracle', 'db', 'firebase', 'dynamodb',
        # Web y desarrollo
        'html', 'css', 'sass', 'scss', 'tailwind', 'bootstrap', 'rest', 'api', 'graphql',
        'frontend', 'backend', 'fullstack', 'web', 'mobile', 'app',
        # Data Science y ML
        'machine learning', 'ml', 'ai', 'data science', 'tensorflow', 'pytorch',
        'pandas', 'numpy', 'scikit', 'deep learning', 'neural network',
        # Testing y QA
        'testing', 'jest', 'pytest', 'selenium', 'cypress', 'unit test', 'tdd',
        # Conceptos de programación
        'programming', 'programación', 'programar', 'coding', 'desarrollo',
        'desarrollo web', 'desarrollo mobile', 'software', 'algoritmo', 'data structure'
    ]
    
    # Verificar si contiene alguna palabra clave técnica
    for keyword in technical_keywords:
        if keyword in text_lower:
            return True
    
    return False


def _parse_review_response(text: str) -> dict:
    """Parse JSON response from LLM with multiple fallback strategies"""
    if not text:
        return None
    
    # Limpiar el texto
    text = text.strip()
    
    # Estrategia 1: Parse directo
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Estrategia 2: Buscar JSON con regex
    import re
    try:
        # Buscar el primer objeto JSON válido
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except Exception:
        pass
    
    # Estrategia 3: Construir manualmente buscando las claves
    try:
        text_lower = text.lower()
        
        # Buscar "valid": "VALID" o "INVALID"
        is_valid = None
        if '"valid"' in text_lower or "'valid'" in text_lower:
            if 'valid' in text_lower and 'invalid' in text_lower:
                # Buscar cuál aparece primero en el contexto de la respuesta
                valid_match = re.search(r'["\']valid["\']\s*:\s*["\'](\w+)["\']', text, re.IGNORECASE)
                if valid_match:
                    is_valid = valid_match.group(1).upper()
        
        # Buscar deadline
        deadline = None
        deadline_match = re.search(r'["\']deadline["\']\s*:\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
        if deadline_match:
            deadline = deadline_match.group(1)
        
        if is_valid:
            return {
                "valid": is_valid,
                "deadline": deadline or "1 mes"
            }
    except Exception:
        pass
    
    return None


def _extract_simple_deadline(text: str) -> str:
    """Simple regex-based deadline extraction as fallback"""
    import re
    text_lower = text.lower()
    
    # Mapeo de palabras numéricas a números
    word_to_num = {
        'una': '1', 'un': '1', 'uno': '1',
        'dos': '2', 'tres': '3', 'cuatro': '4', 'cinco': '5',
        'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9',
        'diez': '10', 'doce': '12'
    }
    
    # Reemplazar palabras por números
    for word, num in word_to_num.items():
        text_lower = text_lower.replace(f'en {word} ', f'en {num} ')
        text_lower = text_lower.replace(f'{word} ', f'{num} ')
    
    # Patterns for common deadline expressions
    patterns = [
        (r'en (\d+)\s*(semana|semanas)', lambda m: f"{m.group(1)} {'semana' if m.group(1) == '1' else 'semanas'}"),
        (r'en (\d+)\s*(mes|meses)', lambda m: f"{m.group(1)} {'mes' if m.group(1) == '1' else 'meses'}"),
        (r'en (\d+)\s*(año|años)', lambda m: f"{m.group(1)} {'año' if m.group(1) == '1' else 'años'}"),
        (r'(\d+)\s*(semana|semanas)', lambda m: f"{m.group(1)} {'semana' if m.group(1) == '1' else 'semanas'}"),
        (r'(\d+)\s*(mes|meses)', lambda m: f"{m.group(1)} {'mes' if m.group(1) == '1' else 'meses'}"),
        (r'(\d+)\s*(año|años)', lambda m: f"{m.group(1)} {'año' if m.group(1) == '1' else 'años'}"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return formatter(match)
    
    return "1 mes"


