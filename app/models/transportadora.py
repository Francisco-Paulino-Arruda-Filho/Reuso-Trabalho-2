from pydantic import BaseModel


class Transporta(BaseModel):
    CNPJ: str
    xNome: str
    IE: str
    xEnder: str
    xMun: str
    UF: str