from pydantic import BaseModel
from typing import Optional


class Entrega(BaseModel):
    CNPJ: str
    xLgr: str
    nro: str
    xCpl: Optional[str] = None
    xBairro: str
    cMun: str
    xMun: str
    UF: str