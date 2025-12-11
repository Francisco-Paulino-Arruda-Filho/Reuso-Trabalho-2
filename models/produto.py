from pydantic import BaseModel
from pyparsing import Optional


class Prod(BaseModel):
    cProd: str
    cEAN: Optional[str] = None
    xProd: str
    CFOP: str
    uCom: str
    qCom: float
    vUnCom: float
    vProd: float
    cEANTrib: Optional[str] = None
    uTrib: str
    qTrib: float
    vUnTrib: float