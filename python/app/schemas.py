from typing import List, Optional
from pydantic import BaseModel


class Skill(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None
    categories: Optional[List[str]] = None


class AgentRequest(BaseModel):
    objective: str
    skills: List[Skill] = []


class AgentResponse(BaseModel):
    status: str
    response: str


