from pydantic import BaseModel

from .inf_nfe import InfNFe



class NFePayload(BaseModel):
    infNFe: InfNFe