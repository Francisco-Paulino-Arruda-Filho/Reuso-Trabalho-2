from typing import List, Optional

from pydantic import BaseModel

from .destinatario import Dest
from .emitente import Emit
from .entrega import Entrega
from .ide import Ide
from .inf_adic import InfAdic
from .retirada import Retirada
from .total import Total
from .transporte import Transp
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
