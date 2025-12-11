from typing import Optional
from pydantic import BaseModel

from models.endereco import Ender

class Emit(BaseModel):
    CNPJ: str
    xNome: str
    xFant: Optional[str] = None
    enderEmit: Ender
    IE: Optional[str] = None