from pydantic import BaseModel
from typing import Optional


class VeicTransp(BaseModel):
    placa: str
    UF: str
    RNTC: Optional[str] = None