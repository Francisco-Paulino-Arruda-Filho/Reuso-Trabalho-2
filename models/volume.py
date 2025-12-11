from pydantic import BaseModel

from models.lacre import Lacre


class Vol(BaseModel):
    qVol: float
    esp: str
    marca: str
    nVol: str
    pesoL: float
    pesoB: float
    lacres: Lacre