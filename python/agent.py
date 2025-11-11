#!/usr/bin/env python3
import sys
import json
import os
import asyncio
from dotenv import load_dotenv

# Ensure local imports work when called as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

load_dotenv()

def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw or "{}")

        try:
            from app.pipeline import run_pipeline
            result = asyncio.run(run_pipeline(payload))
        except Exception as inner_err:
            # If pipeline import/exec fails, return minimal echo so caller can still parse
            response_text = f"No se pudo procesar el objetivo (error interno). Detalle: pipeline_error: {inner_err}"
            print(json.dumps({
                "received": payload,
                "response": response_text,
                "error": f"pipeline_error: {inner_err}"
            }, ensure_ascii=False))
            return

        # Ensure 'response' is present even in CLI fallback path
        output = {
            "received": payload,
            "result": result
        }
        if isinstance(result, dict) and "response" in result:
            output["response"] = result.get("response")
        print(json.dumps(output, ensure_ascii=False))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()


