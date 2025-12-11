from pydantic import BaseModel


class ICMS00(BaseModel):
    orig: str
    CST: str
    modBC: str
    vBC: float
    pICMS: float
    vICMS: float