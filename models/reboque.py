from typing import Optional
from pydantic import BaseModel


class Reboque(BaseModel):
    placa: str
    UF: str
    RNTC: Optional[str] = None