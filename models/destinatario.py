from typing import Optional
from pydantic import BaseModel

from models.endereco import Ender

class Dest(BaseModel):
    CNPJ: str
    xNome: str
    enderDest: Ender
    IE: Optional[str] = None