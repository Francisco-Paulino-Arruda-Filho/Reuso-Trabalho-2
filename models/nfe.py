from pydantic import BaseModel
from .inf_nfe import InfNFe
from .signature import Signature


class NFe(BaseModel):
    infNFe: InfNFe
    Signature: Signature
