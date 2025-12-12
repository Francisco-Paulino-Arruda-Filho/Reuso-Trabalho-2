from pydantic import BaseModel


class ICMSTot(BaseModel):
    vBC: float
    vICMS: float
    vBCST: float
    vST: float
    vProd: float
    vFrete: float
    vSeg: float
    vDesc: float
    vII: float
    vIPI: float
    vPIS: float
    vCOFINS: float
    vOutro: float
    vNF: float