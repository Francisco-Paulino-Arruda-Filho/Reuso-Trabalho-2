from typing import Optional
from pydantic import BaseModel


class InfAdic(BaseModel):
    infAdFisco: Optional[str] = None