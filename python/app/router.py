from fastapi import APIRouter, Request
from .schemas import AgentRequest, AgentResponse
from .pipeline import run_pipeline

router = APIRouter()


@router.post("/agent", response_model=AgentResponse)
async def agent_endpoint(body: AgentRequest, request: Request):
    payload = {"objective": body.objective, "skills": [s.model_dump() for s in body.skills]}
    result = await run_pipeline(payload)

    # Unify contract: always return 'response' to the Node client
    resp_text = result.get("response") or ""
    try:
        print(f"[ROUTER] Returning response:\n{resp_text}")
    except Exception:
        pass
    return AgentResponse(
        status=result.get("status", "ok"),
        response=resp_text
    )


