from pydantic import BaseModel


class PISAliq(BaseModel):
    CST: str
    vBC: float
    pPIS: float
    vPIS: float