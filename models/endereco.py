from typing import Optional
from pydantic import BaseModel

class Ender(BaseModel):
    xLgr: str
    nro: str
    xCpl: Optional[str] = None
    xBairro: str
    cMun: str
    xMun: str
    UF: str
    CEP: Optional[str] = None
    cPais: Optional[str] = None
    xPais: Optional[str] = None
    fone: Optional[str] = None