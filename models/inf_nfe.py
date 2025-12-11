from pydantic import BaseModel
from typing import Optional, List
from .ide import Ide
from .entrega import Entrega
from .retirada import Retirada
from .total import Total
from .emitente import Emit
from .destinatario import Dest
from .destinatario import Det
from .transporte import Transp
from .inf_adic import InfAdic

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