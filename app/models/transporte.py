from pydantic import BaseModel
from models.transportadora import Transporta
from models.veiculo_transportadora import VeicTransp
from models.reboque import Reboque
from models.volume import Vol
from typing import Optional

class Transp(BaseModel):
    modFrete: str
    transporta: Transporta
    veicTransp: VeicTransp
    reboque: Optional[Reboque] = None
    vol: Vol