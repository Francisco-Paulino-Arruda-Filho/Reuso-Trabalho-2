from pydantic import BaseModel
from pyparsing import Optional


class VeicTransp(BaseModel):
    placa: str
    UF: str
    RNTC: Optional[str] = None