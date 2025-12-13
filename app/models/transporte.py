from pydantic import BaseModel
from typing import Optional

from .transportadora import Transporta
from .veiculo_transportadora import VeicTransp
from .reboque import Reboque
from .volume import Vol

class Transp(BaseModel):
    modFrete: str
    transporta: Transporta
    veicTransp: VeicTransp
    reboque: Optional[Reboque] = None
    vol: Vol