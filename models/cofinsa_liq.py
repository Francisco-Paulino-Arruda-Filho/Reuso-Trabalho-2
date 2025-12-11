from pydantic import BaseModel


class COFINSAliq(BaseModel):
    CST: str
    vBC: float
    pCOFINS: float
    vCOFINS: float