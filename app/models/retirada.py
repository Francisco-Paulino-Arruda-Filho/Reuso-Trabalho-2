from typing import Optional
from pydantic import BaseModel


class Retirada(BaseModel):
    CNPJ: str
    xLgr: str
    nro: str
    xCpl: Optional[str] = None
    xBairro: str
    cMun: str
    xMun: str
    UF: str