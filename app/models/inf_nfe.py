from typing import List, Optional

from pydantic import BaseModel

from models.destinatario import Dest
from models.emitente import Emit
from models.entrega import Entrega
from models.ide import Ide
from models.inf_adic import InfAdic
from models.retirada import Retirada
from models.total import Total
from models.transporte import Transp
from .det import Det 

class InfNFe(BaseModel):
    Id: str
    versao: str
    ide: Ide
    emit: Emit
    dest: Dest
    retirada: Optional[Retirada] = None
    entrega: Optional[Entrega] = None
    det: List[Det] 
    total: Total
    transp: Transp
    infAdic: Optional[InfAdic] = None
